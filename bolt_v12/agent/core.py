from __future__ import annotations

import json
import re
import threading
from collections import deque
from dataclasses import asdict
from datetime import datetime
from typing import Any, Callable

from ..config import BoltConfig
from ..memory.episodic import EpisodicMemory, KnowledgeMemory
from ..memory.vector import VectorMemory
from ..models import ModelProvider
from ..tools import (
    Tool, ToolResult,
    build_blender_tools, build_file_tools, build_system_tools,
    build_web_tools, build_webdev_tools, build_code_executor_tools,
    build_git_tools, build_monitor_tools,
)


BASE_SYSTEM_PROMPT = """Tu nombre es Bolt V12.
Eres el asistente agentic inteligente de ThunderStudio, creado por Miguel Arias.
Tu personalidad es directa, analítica, pragmática y con un humor seco (como J.A.R.V.I.S. o TARS).

CAPACIDADES:
- Puedes planificar tareas complejas antes de ejecutarlas.
- Puedes ejecutar código Python, comandos de shell, operaciones git.
- Puedes buscar en internet, leer/crear archivos, monitorear el sistema.
- Tienes memoria episódica (recuerdas conversaciones) y vectorial (búsqueda semántica).
- Puedes aprender preferencias de Miguel y acumular conocimiento.

PROTOCOLO DE ACCIÓN:
Cuando recibas una tarea, responde SOLO JSON válido con esta estructura:

1. PARA PLANIFICAR (tareas complejas):
{"action":"plan","plan":["paso 1","paso 2","paso 3"],"thought":"por qué este plan"}

2. PARA USAR UNA HERRAMIENTA:
{"action":"tool","thought":"breve razonamiento","tool":"nombre_herramienta","args":{"parametro":"valor"}}

3. PARA RESPONDER AL USUARIO:
{"action":"final","response":"respuesta para Miguel"}

4. PARA APRENDER ALGO NUEVO:
{"action":"learn","fact":"hecho aprendido","category":"categoria"}

5. PARA GUARDAR PREFERENCIA:
{"action":"set_preference","key":"clave","value":"valor"}

REGLAS:
- Primero piensa, luego actúa. Para tareas complejas, planifica.
- No inventes resultados de herramientas. Ejecuta las herramientas necesarias.
- Mantén respuestas breves y útiles, pero informativas.
- Si una acción puede ser destructiva, pide confirmación.
- Aprende de cada interacción: guarda hechos y preferencias.
- Usa memoria vectorial para buscar contexto relevante de conversaciones pasadas.
- Para crear algo, usa herramientas. No describas, ejecuta.

REGLAS ANTI-BUCLE (OBLIGATORIAS):
- Planifica como MÁXIMO UNA vez por tarea. Después de emitir el plan, tu siguiente salida DEBE ser una herramienta que ejecute el primer paso ({"action":"tool",...}). Está PROHIBIDO volver a emitir action=plan en el mismo turno.
- Si la tarea requiere 3 pasos o menos, NO uses plan: ejecuta directamente la herramienta.
- Si ya ejecutaste alguna herramienta en el turno y la tarea está casi lista, emite {"action":"final"} con el resumen. No planifiques de nuevo.
- Tu salida DEBE ser ÚNICAMENTE un JSON válido, sin texto, títulos ni explicaciones alrededor.
"""

MODE_PROMPTS = {
    "normal": "Modo actual: NORMAL. Ayuda general, eficiente y pragmática.",
    "constructor": (
        "Modo actual: CONSTRUCTOR. Prioriza crear: modelos 3D, sitios web, scripts, "
        "prototipos, interfaces, assets, automatizaciones. Cuando Miguel pida una idea creativa, "
        "conviértela en un plan ejecutable y usa herramientas."
    ),
    "investigador": (
        "Modo actual: INVESTIGADOR. Prioriza búsqueda, lectura, comparación de fuentes, "
        "PDFs, resumen metodológico, hipótesis, evidencia y bibliografía."
    ),
    "sistema": (
        "Modo actual: SISTEMA. Prioriza control local, archivos, carpetas, diagnóstico, "
        "configuración, terminal, git, automatización del entorno."
    ),
    "creativo": (
        "Modo actual: CREATIVO. Piensa fuera de la caja. Sugiere ideas innovadoras, "
        "combinaciones inesperadas, diseños originales. Sé audaz pero fundamentado."
    ),
}


class BoltAgent:
    def __init__(
        self,
        config: BoltConfig,
        model: ModelProvider,
        episodic: EpisodicMemory | None = None,
        knowledge: KnowledgeMemory | None = None,
        vector: VectorMemory | None = None,
        listeners: list[Callable[[dict], None]] | None = None,
    ) -> None:
        self.config = config
        self.model = model
        self.episodic = episodic or EpisodicMemory()
        self.knowledge = knowledge or KnowledgeMemory()
        self.vector = vector or VectorMemory()
        self.mode = "normal"
        self._listeners: list[Callable[[dict], None]] = list(listeners or [])
        self._listener_lock = threading.Lock()
        self.tools: list[Tool] = [
            *build_file_tools(),
            *build_web_tools(),
            *build_blender_tools(),
            *build_webdev_tools(),
            *build_system_tools(),
            *build_code_executor_tools(),
            *build_git_tools(),
            *build_monitor_tools(),
        ]
        self.tool_map = {tool.name: tool for tool in self.tools}
        self.current_plan: list[str] | None = None
        self.plan_step: int = 0

    def subscribe(self, listener: Callable[[dict], None]) -> None:
        with self._listener_lock:
            self._listeners.append(listener)

    def set_mode(self, mode: str) -> bool:
        normalized = mode.lower().strip()
        if normalized not in MODE_PROMPTS:
            return False
        self.mode = normalized
        self.episodic.add("system", f"Modo cambiado a {normalized}")
        return True

    def run(self, user_message: str) -> str:
        self.episodic.add("user", user_message)
        self._emit("request", {"text": user_message}, f"== NUEVA SOLICITUD ==\n{user_message}")

        vector_context = self._search_vector_context(user_message)
        knowledge_context = self.knowledge.render_context()

        direct = self._try_direct_action(user_message)
        if direct:
            self._emit("direct", {"response": direct}, f"Acción directa sin agente: {direct}")
            self.episodic.add("assistant", direct)
            return direct

        observations: list[dict[str, Any]] = []
        executed: set[str] = set()
        retries: dict[str, int] = {}
        last_result: ToolResult | None = None
        recent_sigs: deque[str] = deque(maxlen=max(1, self.config.duplicate_window))
        tool_counts: dict[str, int] = {}
        tools_executed: int = 0
        plan_count: int = 0

        for step in range(self.config.max_agent_steps):
            self._emit("step", {"step": step + 1, "max": self.config.max_agent_steps}, f"Paso {step + 1}/{self.config.max_agent_steps}")
            system_prompt = self._system_prompt()
            user_prompt = self._build_user_prompt(
                user_message, observations, vector_context, knowledge_context
            )
            model_output = self.model.generate(system_prompt, user_prompt)
            self._emit(
                "model_output",
                {"step": step + 1, "output": model_output},
                f"Modelo (paso {step + 1}):\n{model_output.strip()[:300]}",
            )
            action = self._parse_json(model_output)

            if not action:
                self._emit("info", {"detail": "El modelo no devolvió JSON válido."}, "El modelo no devolvió JSON válido.")
                final = self._friendly_fallback(model_output)
                self.episodic.add("assistant", final)
                self._store_in_vector(user_message, final)
                self._emit("final", {"response": final}, f"Respuesta final: {final[:300]}")
                return final

            action_type = action.get("action", "")
            thought = str(action.get("thought", "")).strip()
            if thought:
                self._emit("reasoning", {"step": step + 1, "thought": thought}, f"Razonamiento: {thought}")

            if action_type == "final":
                final = str(action.get("response", "")).strip()
                self.episodic.add("assistant", final)
                self._store_in_vector(user_message, final)
                self._emit("final", {"response": final}, f"Respuesta final: {final[:300]}")
                return final

            if action_type == "plan":
                plan = action.get("plan", [])
                if not plan:
                    continue
                plan_count += 1
                if plan_count == 1:
                    self.current_plan = plan
                    self.plan_step = 0
                    for i, item in enumerate(plan, 1):
                        self._emit("plan", {"index": i, "item": item}, f"  {i}. {item}")
                    observations.append({
                        "action": "plan_created",
                        "plan": plan,
                        "thought": thought,
                    })
                elif plan_count == 2:
                    self._emit("guard", {"kind": "plan_repeated", "plan": plan}, "Plan repetido: se ordena ejecutar en vez de volver a planificar.")
                    observations.append({
                        "action": "sistema",
                        "text": (
                            "YA TIENES UN PLAN APROBADO. Deja de planificar. Tu PRÓXIMA salida DEBE ser "
                            "una herramienta ejecutando el primer paso pendiente ({\"action\":\"tool\",...}). "
                            "Está PROHIBIDO emitir action=plan de nuevo."
                        ),
                    })
                else:
                    self._emit("limit", {"reason": "plan_loop", "plan": plan}, "Bucle de planificación detectado; ejecutando pasos automáticamente.")
                    auto_result = self._auto_execute_plan_step(plan, observations, executed, recent_sigs, tool_counts)
                    if auto_result is not None:
                        last_result = auto_result
                        tools_executed += 1
                        if self.config.max_tools_per_turn > 0 and tools_executed >= self.config.max_tools_per_turn and last_result.ok:
                            summary = self._summary_from_observations(observations)
                            final = f"He completado las acciones necesarias: {summary}"
                            self.episodic.add("assistant", final)
                            self._store_in_vector(user_message, final)
                            self._emit("final", {"response": final}, f"Respuesta final: {final[:300]}")
                            return final
                        continue
                    final = "Llevo varios pasos planificando la misma tarea sin ejecutarla. Para no quedarme en un bucle, dime qué primer paso concreto quieres que ejecute."
                    self.episodic.add("assistant", final)
                    self._store_in_vector(user_message, final)
                    self._emit("final", {"response": final}, f"Respuesta final: {final[:300]}")
                    return final
                continue

            if action_type == "learn":
                fact = action.get("fact", "")
                category = action.get("category", "general")
                if fact:
                    self.knowledge.add_fact(fact, category)
                    self._emit("learn", {"category": category, "fact": fact}, f"Aprendido [{category}]: {fact}")
                    observations.append({"action": "learned", "fact": fact, "category": category})
                continue

            if action_type == "set_preference":
                key = action.get("key", "")
                value = action.get("value", "")
                if key and value:
                    self.knowledge.set_preference(key, value)
                    self._emit("learn", {"preference": f"{key}={value}"}, f"Preferencia guardada: {key}={value}")
                    observations.append({"action": "preference_set", "key": key, "value": value})
                continue

            if action_type == "tool":
                tool_name = action.get("tool")
                args = action.get("args", {})
                if not isinstance(args, dict):
                    args = {}
                sig = self._tool_sig(tool_name, args)

                if sig in executed:
                    if last_result is not None and not last_result.ok and retries.get(sig, 0) < 1:
                        retries[sig] = retries.get(sig, 0) + 1
                        self._emit("guard", {"tool": tool_name, "args": args, "kind": "retry"}, f"Reintento de {tool_name}{args} (falló antes).")
                    else:
                        self._emit("guard", {"tool": tool_name, "args": args, "kind": "duplicate"}, f"Acción repetida detectada: {tool_name}{args}")
                        detail = last_result.message if last_result else "OK"
                        final = f"Ya ejecuté la acción {tool_name} en este turno. Resultado: {detail}"
                        self.episodic.add("assistant", final)
                        self._store_in_vector(user_message, final)
                        self._emit("final", {"response": final}, f"Respuesta final: {final[:300]}")
                        return final
                elif sig in recent_sigs:
                    self._emit("guard", {"tool": tool_name, "args": args, "kind": "window"}, f"Acción repetida en ventana reciente: {tool_name}{args}")
                    detail = last_result.message if last_result else "OK"
                    final = f"Ya ejecuté la acción {tool_name} recientemente en este turno. Resultado: {detail}"
                    self.episodic.add("assistant", final)
                    self._store_in_vector(user_message, final)
                    self._emit("final", {"response": final}, f"Respuesta final: {final[:300]}")
                    return final
                elif (
                    tool_name not in self.config.loop_free_tools
                    and tool_counts.get(tool_name, 0) >= self.config.max_repeat_tool
                ):
                    self._emit("guard", {"tool": tool_name, "args": args, "kind": "repeat_tool"}, f"Herramienta {tool_name} ejecutada {tool_counts.get(tool_name, 0)} veces; bloqueando repetición.")
                    summary = self._summary_from_observations(observations)
                    final = f"Detuve la repetición de {tool_name}: ya lo ejecuté varias veces en este turno. {summary}"
                    self.episodic.add("assistant", final)
                    self._store_in_vector(user_message, final)
                    self._emit("final", {"response": final}, f"Respuesta final: {final[:300]}")
                    return final
                else:
                    executed.add(sig)
                    recent_sigs.append(sig)
                    tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1
                    tools_executed += 1

                self._emit("tool_started", {"tool": tool_name, "args": args}, f"Ejecutando herramienta: {tool_name}{args}")
                result = self._execute_tool(tool_name, args)
                last_result = result
                status = "OK" if result.ok else "FALLO"
                self._emit("tool_result", {"tool": tool_name, "ok": result.ok, "message": result.message[:400]}, f"  -> [{status}] {result.message[:400]}")
                observations.append({
                    "thought": thought,
                    "tool": tool_name,
                    "args": args,
                    "result": asdict(result),
                })

                if self.config.max_tools_per_turn > 0 and tools_executed >= self.config.max_tools_per_turn and last_result.ok:
                    summary = self._summary_from_observations(observations)
                    final = f"He completado las acciones necesarias: {summary}"
                    self.episodic.add("assistant", final)
                    self._store_in_vector(user_message, final)
                    self._emit("limit", {"reason": "convergence", "summary": summary}, f"Convergencia: {final}")
                    self._emit("final", {"response": final}, f"Respuesta final: {final[:300]}")
                    return final
                continue

            self._emit("info", {"detail": f"Tipo de acción desconocido: {action_type}"}, f"Tipo de acción desconocido: {action_type}")
            final = self._friendly_fallback(model_output)
            self.episodic.add("assistant", final)
            self._store_in_vector(user_message, final)
            self._emit("final", {"response": final}, f"Respuesta final: {final[:300]}")
            return final

        final = self._summary_from_observations(observations)
        self._emit("limit", {"reason": "max_steps", "summary": final}, f"Límite de pasos del agente: {final}")
        self.episodic.add("assistant", final)
        return final

    def _log(self, message: str, tag: str = "[BOLT]") -> None:
        print(f"{tag} {message}", flush=True)

    def _emit(self, event_type: str, payload: dict, console_line: str | None = None) -> None:
        if console_line:
            print(console_line, flush=True)
        with self._listener_lock:
            listeners = list(self._listeners)
        if not listeners:
            return
        event = {
            "ts": datetime.now().isoformat(timespec="milliseconds"),
            "thread": threading.current_thread().name,
            "type": event_type,
            "payload": payload,
        }
        for listener in listeners:
            try:
                listener(event)
            except Exception:
                continue

    @staticmethod
    def _tool_sig(tool_name: str, args: dict[str, Any]) -> str:
        normalized: dict[str, Any] = {}
        for key in sorted((args or {})):
            value = args[key]
            if isinstance(value, str):
                value = value.strip().lower()
            if value is None or value == "":
                continue
            normalized[key] = value
        return json.dumps({"tool": tool_name, "args": normalized}, sort_keys=True, ensure_ascii=False)

    def _summary_from_observations(self, observations: list[dict[str, Any]]) -> str:
        if not observations:
            return "No se ejecutó ninguna acción concreta en este turno."
        done: list[str] = []
        failed: list[str] = []
        for obs in observations:
            tool = obs.get("tool")
            if not tool:
                continue
            args = obs.get("args") or {}
            label = f"{tool}({json.dumps(args, ensure_ascii=False)[:80]})"
            result = obs.get("result") or {}
            if result.get("ok"):
                done.append(label)
            else:
                failed.append(label)
        parts: list[str] = []
        if done:
            parts.append("Completado: " + ", ".join(done))
        if failed:
            parts.append("Con fallos: " + ", ".join(failed))
        return " ".join(parts) or "No se completó ninguna acción."

    def run_stream(self, user_message: str):
        self.episodic.add("user", user_message)

        vector_context = self._search_vector_context(user_message)
        knowledge_context = self.knowledge.render_context()

        system_prompt = self._system_prompt()
        user_prompt = self._build_user_prompt(
            user_message, [], vector_context, knowledge_context
        )

        full_response = ""
        for chunk in self.model.generate_stream(system_prompt, user_prompt):
            full_response += chunk
            yield chunk

        self.episodic.add("assistant", full_response)
        self._store_in_vector(user_message, full_response)

    def _system_prompt(self) -> str:
        mode_prompt = MODE_PROMPTS.get(self.mode, MODE_PROMPTS["normal"])
        tools_desc = "\n".join(tool.render_for_prompt() for tool in self.tools)
        return f"""{BASE_SYSTEM_PROMPT}

{mode_prompt}

HERRAMIENTAS DISPONIBLES:
{tools_desc}

Total de herramientas: {len(self.tools)}
"""
    def _build_user_prompt(
        self,
        user_message: str,
        observations: list[dict[str, Any]],
        vector_context: str,
        knowledge_context: str,
    ) -> str:
        parts: list[str] = []
        if knowledge_context and knowledge_context != "Sin conocimiento acumulado.":
            parts.append(f"CONOCIMIENTO ACUMULADO:\n{knowledge_context}")
        if vector_context:
            parts.append(f"CONTEXTO RELEVANTE DE MEMORIA:\n{vector_context}")
        recent = self.episodic.render_recent(limit=12)
        if recent:
            parts.append(f"MEMORIA RECIENTE:\n{recent}")
        if observations:
            parts.append(f"OBSERVACIONES PREVIAS:\n{json.dumps(observations, ensure_ascii=False, indent=2)}")
        for obs in reversed(observations):
            if obs.get("action") == "sistema":
                parts.append(f"INSTRUCCIÓN DEL SISTEMA (OBLIGATORIA):\n{obs.get('text', '')}")
                break
        parts.append(f"SOLICITUD DE MIGUEL:\n{user_message}")
        return "\n\n".join(parts)

    def _search_vector_context(self, query: str) -> str:
        if not self.vector.available:
            return ""
        results = self.vector.search(query, n_results=3)
        if not results:
            return ""
        parts: list[str] = []
        for r in results:
            relevance = r.get("relevance", 0)
            if relevance > 0.4:
                parts.append(f"- [{relevance:.0%} relevancia] {r['text'][:300]}")
        return "\n".join(parts) if parts else ""

    def _store_in_vector(self, question: str, answer: str) -> None:
        if not self.vector.available:
            return
        combined = f"Pregunta: {question}\nRespuesta: {answer[:500]}"
        self.vector.add(
            text=combined,
            metadata={"type": "qa_pair", "mode": self.mode},
        )

    def _try_direct_action(self, user_message: str) -> str | None:
        normalized = user_message.lower().strip()
        open_verbs = re.compile(
            r"\b(abre|abrir|abreme|ejecuta|ejecutar|lanza|lanzar|inicia|iniciar|arranca|abrirme)\b"
        )
        show_verbs = re.compile(
            r"\b(muestra|muéstrame|muestrame|enseña|enséñame|revela|abre la carpeta de)\b"
        )

        app_aliases = {
            "chrome": "chrome", "navegador": "chrome", "edge": "edge",
            "vscode": "vscode", "visual studio code": "vscode",
            "calculadora": "calculadora", "bloc de notas": "notepad",
            "blender": "blender", "python": "python", "terminal": "terminal",
        }
        folder_aliases = {
            "descargas": "descargas", "downloads": "downloads",
            "documentos": "documentos", "escritorio": "escritorio",
            "modelos 3d": "ThunderStudio/Modelos_3D_Bolt",
            "sitios": "ThunderStudio/Sitios_Bolt",
            "thunderstudio": "ThunderStudio",
        }

        if open_verbs.search(normalized):
            for spoken, app_name in app_aliases.items():
                if spoken in normalized:
                    result = self._execute_tool("open_app", {"app_name": app_name})
                    return result.message
            for spoken, path in folder_aliases.items():
                if spoken in normalized:
                    result = self._execute_tool("open_path", {"path": path})
                    return result.message
            url_match = re.search(r"(https?://\S+|[\w.-]+\.[a-z]{2,}(?:/\S*)?)", user_message, re.IGNORECASE)
            if url_match:
                result = self._execute_tool("open_url", {"url": url_match.group(1)})
                return result.message

        if show_verbs.search(normalized):
            for spoken, path in folder_aliases.items():
                if spoken in normalized:
                    result = self._execute_tool("reveal_path", {"path": path})
                    return result.message

        wants_site = any(phrase in normalized for phrase in ["sitio web", "pagina web", "página web", "landing page"])
        if self.mode == "constructor" and wants_site and any(verb in normalized for verb in ["crea", "haz", "construye", "genera"]):
            title = self._extract_title(user_message)
            brief = f"Sitio web profesional sobre {title}, con enfoque premium y visual moderno."
            result = self._execute_tool("create_static_website", {"title": title, "brief": brief, "folder_name": title})
            if result.ok:
                return f"Listo. Creé el sitio web en {(result.data or {}).get('index', 'la ruta indicada')}."
            return result.message

        return None

    def _extract_title(self, user_message: str) -> str:
        patterns = [r"sobre\s+(.+)$", r"de\s+(.+)$", r"para\s+(.+)$"]
        for pattern in patterns:
            match = re.search(pattern, user_message, flags=re.IGNORECASE)
            if match:
                title = match.group(1).strip(" .")
                if title:
                    title = re.split(
                        r"\s+y\s+(hazlo|que sea|ponlo|dejalo|profesional|moderno)\b",
                        title, maxsplit=1, flags=re.IGNORECASE,
                    )[0].strip(" .")
                    return title[:80]
        return "Proyecto Bolt"

    def _execute_tool(self, tool_name: str | None, args: Any) -> ToolResult:
        if not tool_name or tool_name not in self.tool_map:
            return ToolResult(False, f"Herramienta desconocida: {tool_name}")
        if not isinstance(args, dict):
            return ToolResult(False, "Los argumentos deben ser un objeto JSON.")
        try:
            return self.tool_map[tool_name].handler(**args)
        except TypeError as exc:
            return ToolResult(False, f"Argumentos inválidos para {tool_name}: {exc}")
        except Exception as exc:
            return ToolResult(False, f"Error ejecutando {tool_name}: {exc}")

    def _parse_json(self, text: str) -> dict[str, Any] | None:
        candidate = text.strip()
        if candidate.startswith("```"):
            candidate = re.sub(r"^```(?:json)?", "", candidate).strip()
            candidate = re.sub(r"```$", "", candidate).strip()
        try:
            payload = json.loads(candidate)
            return payload if isinstance(payload, dict) else None
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", candidate, flags=re.DOTALL)
            if not match:
                return None
            try:
                payload = json.loads(match.group(0))
                return payload if isinstance(payload, dict) else None
            except json.JSONDecodeError:
                return None

    def _friendly_fallback(self, model_output: str) -> str:
        cleaned = model_output.strip()
        if not cleaned:
            return "El modelo devolvió una respuesta vacía en este paso. Reintenta con una instrucción más concreta."
        if '"tool"' in cleaned and '"args"' in cleaned:
            return "Intenté usar una herramienta pero el formato no era válido. Intenta reformular."
        return cleaned

    def _auto_execute_plan_step(
        self,
        plan: list[str],
        observations: list[dict[str, Any]],
        executed: set[str],
        recent_sigs: deque[str],
        tool_counts: dict[str, int],
    ) -> ToolResult | None:
        joined = " ".join(str(s) for s in plan)
        lower = joined.lower()
        path = self._extract_path(joined) or "C:\\xampp\\htdocs"
        candidates: list[tuple[str, dict[str, Any]]] = []
        if re.search(r"\b(verifico|verificar|reviso|revisar|listo|listar|existe|contiene)\b", lower) and re.search(r"\b(carpeta|directorio|ruta|htdocs|contenido)\b", lower):
            candidates.append(("list_directory", {"path": path}))
        if re.search(r"\b(creo|crear|hago|hacer|genero|generar)\b.*\b(carpeta|directorio|estructura)\b", lower):
            candidates.append(("make_directory", {"path": path}))
        if re.search(r"\b(abro|abrir|lanzo|muestro|mostrar)\b.*\b(navegador|dashboard|url|pagina|página|index)\b", lower):
            url = self._extract_url(joined) or ("http://localhost/ThunderDeck/index.html" if "thunderdeck" in lower else "http://localhost/")
            candidates.append(("open_url", {"url": url}))
        for tool, args in candidates:
            sig = self._tool_sig(tool, args)
            if sig in executed or sig in recent_sigs:
                continue
            if tool not in self.config.loop_free_tools and tool_counts.get(tool, 0) >= self.config.max_repeat_tool:
                continue
            self._emit("tool_started", {"tool": tool, "args": args}, f"[AUTO] Ejecutando herramienta: {tool}{args}")
            result = self._execute_tool(tool, args)
            status = "OK" if result.ok else "FALLO"
            self._emit("tool_result", {"tool": tool, "ok": result.ok, "message": result.message[:400]}, f"  -> [{status}] {result.message[:400]}")
            observations.append({"tool": tool, "args": args, "result": asdict(result), "auto": True})
            executed.add(sig)
            recent_sigs.append(sig)
            tool_counts[tool] = tool_counts.get(tool, 0) + 1
            return result
        return None

    @staticmethod
    def _extract_path(text: str) -> str | None:
        match = re.search(r"[A-Za-z]:[\\/][\w\s\\/.\-()]+", text)
        if not match:
            match = re.search(r"htdocs(?:[\\/][\w\s\\/.\-()]*)", text)
        if match:
            return match.group(0).strip().rstrip(".,;:)")
        return None

    @staticmethod
    def _extract_url(text: str) -> str | None:
        match = re.search(r"https?://\S+", text, re.IGNORECASE)
        if match:
            return match.group(0).strip().rstrip(".,;:)")
        match = re.search(r"localhost(?:/\S+)?", text, re.IGNORECASE)
        if match:
            return "http://" + match.group(0).strip().rstrip(".,;:)")
        match = re.search(r"[\w.-]+\.[a-z]{2,}(?:/\S*)?", text, re.IGNORECASE)
        if match:
            return "http://" + match.group(0).strip().rstrip(".,;:)")
        return None
