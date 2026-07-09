from __future__ import annotations

import json
import re
from dataclasses import asdict
from typing import Any

from .config import BoltConfig
from .memory import JsonlMemory
from .models import ModelProvider
from .tools import Tool, ToolResult, build_blender_tools, build_file_tools, build_system_tools, build_web_tools, build_webdev_tools


BASE_SYSTEM_PROMPT = """Tu nombre es Bolt V11.
Eres el asistente agentico de ThunderStudio, creado por Miguel Arias.
Tu personalidad es directa, analitica, pragmatica y con humor seco.

Puedes usar herramientas. Para usar una herramienta responde SOLO JSON valido con esta forma:
{"thought":"breve razonamiento","tool":"nombre_herramienta","args":{"parametro":"valor"}}

Cuando ya tengas suficiente informacion, responde SOLO JSON valido con esta forma:
{"final":"respuesta para Miguel"}

Reglas:
- No inventes resultados de herramientas.
- Para busquedas, descarga de PDFs o creacion 3D, usa herramientas antes de responder.
- Para crear sitios web, prototipos o paginas de producto, usa create_static_website o write_text_file. No busques en internet salvo que Miguel pida datos actuales, precios, fuentes o investigacion.
- En modo constructor, si Miguel pide crear algo y faltan detalles menores, haz una primera version profesional con supuestos razonables en lugar de bloquearte.
- Para abrir programas, carpetas, archivos o URLs, usa las herramientas open_app, open_path, reveal_path u open_url.
- Si una accion puede modificar archivos, hazla solo cuando Miguel lo pida claramente.
- Mantén respuestas breves y utiles.
"""


MODE_PROMPTS = {
    "normal": "Modo actual: NORMAL. Ayuda general, eficiente y pragmatica.",
    "constructor": (
        "Modo actual: CONSTRUCTOR. Prioriza crear cosas digitales: modelos 3D, sitios web, "
        "scripts, prototipos, escenas, interfaces, assets, automatizaciones y estructuras de proyecto. "
        "Cuando Miguel pida una idea creativa, conviertela en un plan ejecutable y usa herramientas si procede."
    ),
    "investigador": (
        "Modo actual: INVESTIGADOR. Prioriza busqueda, lectura, comparacion de fuentes, PDFs, "
        "resumen metodico, hipotesis, evidencia y bibliografia."
    ),
    "sistema": (
        "Modo actual: SISTEMA. Prioriza control local, archivos, carpetas, diagnostico, configuracion "
        "y automatizacion del entorno de Miguel."
    ),
}


class BoltAgent:
    def __init__(
        self,
        config: BoltConfig,
        model: ModelProvider,
        memory: JsonlMemory | None = None,
        tools: list[Tool] | None = None,
    ) -> None:
        self.config = config
        self.model = model
        self.memory = memory or JsonlMemory()
        self.tools = tools or [
            *build_file_tools(),
            *build_web_tools(),
            *build_blender_tools(),
            *build_webdev_tools(),
            *build_system_tools(),
        ]
        self.tool_map = {tool.name: tool for tool in self.tools}
        self.mode = "normal"

    def set_mode(self, mode: str) -> bool:
        normalized = mode.lower().strip()
        if normalized not in MODE_PROMPTS:
            return False
        self.mode = normalized
        self.memory.add("system", f"Modo cambiado a {normalized}")
        return True

    def run(self, user_message: str) -> str:
        self.memory.add("user", user_message)
        system_action = self._try_direct_system_action(user_message)
        if system_action:
            self.memory.add("assistant", system_action)
            return system_action

        direct = self._try_direct_creation(user_message)
        if direct:
            self.memory.add("assistant", direct)
            return direct

        observations: list[dict[str, Any]] = []

        for _ in range(self.config.max_agent_steps):
            model_output = self.model.generate(
                self._system_prompt(),
                self._build_user_prompt(user_message, observations),
            )
            action = self._parse_json(model_output)

            if not action:
                final = self._friendly_fallback(model_output)
                self.memory.add("assistant", final)
                return final

            if "final" in action:
                final = str(action["final"]).strip()
                self.memory.add("assistant", final)
                return final

            tool_name = action.get("tool")
            args = action.get("args", {})
            result = self._execute_tool(tool_name, args)
            observations.append(
                {
                    "tool": tool_name,
                    "args": args,
                    "result": asdict(result),
                }
            )

        final = "Llegué al límite de pasos del agente. Tengo observaciones parciales, pero no conviene fingir cierre."
        self.memory.add("assistant", final)
        return final

    def _system_prompt(self) -> str:
        return BASE_SYSTEM_PROMPT + "\n" + MODE_PROMPTS.get(self.mode, MODE_PROMPTS["normal"])

    def _build_user_prompt(self, user_message: str, observations: list[dict[str, Any]]) -> str:
        tools = "\n".join(tool.render_for_prompt() for tool in self.tools)
        return f"""Memoria reciente:
{self.memory.render_recent()}

Herramientas disponibles:
{tools}

Solicitud de Miguel:
{user_message}

Observaciones previas:
{json.dumps(observations, ensure_ascii=False, indent=2)}
"""

    def _execute_tool(self, tool_name: str | None, args: Any) -> ToolResult:
        if not tool_name or tool_name not in self.tool_map:
            return ToolResult(False, f"Herramienta desconocida: {tool_name}")
        if not isinstance(args, dict):
            return ToolResult(False, "Los argumentos de herramienta deben ser un objeto JSON.")
        try:
            return self.tool_map[tool_name].handler(**args)
        except TypeError as exc:
            return ToolResult(False, f"Argumentos invalidos para {tool_name}: {exc}")
        except Exception as exc:
            return ToolResult(False, f"Error ejecutando {tool_name}: {exc}")

    def _try_direct_creation(self, user_message: str) -> str | None:
        normalized = user_message.lower()
        wants_site = any(phrase in normalized for phrase in ["sitio web", "pagina web", "página web", "landing page"])
        if self.mode == "constructor" and wants_site and any(verb in normalized for verb in ["crea", "haz", "construye", "genera"]):
            title = self._extract_site_title(user_message)
            brief = f"Sitio web profesional sobre {title}, con enfoque premium, visual moderno y estructura lista para mejorar."
            result = self._execute_tool(
                "create_static_website",
                {"title": title, "brief": brief, "folder_name": title},
            )
            if result.ok:
                index = (result.data or {}).get("index")
                return f"Listo. Creé el sitio web profesional en {index}."
            return result.message
        return None

    def _try_direct_system_action(self, user_message: str) -> str | None:
        normalized = user_message.lower().strip()
        open_verbs = ("abre", "abrir", "ejecuta", "lanza", "inicia")
        show_verbs = ("muestra", "muéstrame", "muestrame", "enseña", "enséñame", "revela")

        app_aliases = {
            "chrome": "chrome",
            "navegador": "navegador",
            "edge": "edge",
            "vscode": "vscode",
            "visual studio code": "visual studio code",
            "calculadora": "calculadora",
            "bloc de notas": "bloc de notas",
            "notepad": "notepad",
        }
        folder_aliases = {
            "descargas": "descargas",
            "downloads": "downloads",
            "documentos": "documentos",
            "escritorio": "escritorio",
            "modelos 3d": "ThunderStudio/Modelos_3D_Bolt",
            "modelo 3d": "ThunderStudio/Modelos_3D_Bolt",
            "sitios": "ThunderStudio/Sitios_Bolt",
            "sitio web": "ThunderStudio/Sitios_Bolt",
            "thunderstudio": "ThunderStudio",
        }

        if normalized.startswith(open_verbs):
            for spoken, app_name in app_aliases.items():
                if spoken in normalized:
                    result = self._execute_tool("open_app", {"app_name": app_name})
                    return result.message
            for spoken, path in folder_aliases.items():
                if spoken in normalized:
                    result = self._execute_tool("open_path", {"path": path})
                    return result.message
            url_match = re.search(r"(https?://\S+|[\w.-]+\.[a-z]{2,}(?:/\S*)?)", user_message, flags=re.IGNORECASE)
            if url_match:
                result = self._execute_tool("open_url", {"url": url_match.group(1)})
                return result.message

        if normalized.startswith(show_verbs):
            for spoken, path in folder_aliases.items():
                if spoken in normalized:
                    result = self._execute_tool("reveal_path", {"path": path})
                    return result.message

        return None

    def _extract_site_title(self, user_message: str) -> str:
        patterns = [
            r"sobre\s+(.+)$",
            r"de\s+(.+)$",
            r"para\s+(.+)$",
        ]
        for pattern in patterns:
            match = re.search(pattern, user_message, flags=re.IGNORECASE)
            if match:
                title = match.group(1).strip(" .")
                if title:
                    title = re.split(
                        r"\s+y\s+(hazlo|que sea|ponlo|dejalo|déjalo|crealo|créalo|profesional|moderno)\b",
                        title,
                        maxsplit=1,
                        flags=re.IGNORECASE,
                    )[0].strip(" .")
                    return title[:80]
        return "Proyecto Bolt"

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
        if '"tool"' in model_output and '"args"' in model_output:
            return "El modelo intentó usar una herramienta, pero devolvió una instrucción mal formada. Ya lo registré; intenta repetirlo con una frase directa."
        return model_output.strip()
