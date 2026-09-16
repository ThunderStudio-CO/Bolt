from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bolt_v12.config import BoltConfig
from bolt_v12.models import ModelProvider
from bolt_v12.agent import BoltAgent
from bolt_v12.tools import ToolResult
from bolt_v12.trace import TraceLogger

TEST_CONFIG = BoltConfig(
    model_provider="test",
    gemini_api_key=None,
    gemini_model="test",
    bigpickle_model="test",
    bigpickle_api_key=None,
    bigpickle_base_url="http://localhost",
    ollama_model="test",
    ollama_base_url="http://localhost",
    max_agent_steps=20,
    planning_enabled=True,
    memory_limit=50,
    vector_enabled=False,
    duplicate_window=4,
    max_repeat_tool=3,
    max_tools_per_turn=6,
    trace_enabled=False,
    log_retention_days=7,
    monitor_interval=30,
    alert_threshold_cpu=85,
    alert_threshold_disk=90,
)


class LoopStubProvider(ModelProvider):
    """Simula un modelo que repite open_app con variantes y nunca emite final."""

    name = "stub"

    def __init__(self, variant: str = "calc") -> None:
        self.variant = variant
        self.calls = 0

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        self.calls += 1
        v = self.variant
        payload = {
            "action": "tool",
            "thought": f"intento {self.calls} de abrir",
            "tool": "open_app",
            "args": {"app_name": f"{v} {self.calls}"},
        }
        return json.dumps(payload, ensure_ascii=False)

    def generate_stream(self, system_prompt: str, user_prompt: str):
        yield self.generate(system_prompt, user_prompt)


class DirectThenFinalProvider(ModelProvider):
    """Alterna herramientas distintas y termina en un final."""

    name = "stub2"

    def __init__(self) -> None:
        self.calls = 0
        self.tools = [
            ("open_app", {"app_name": "calculadora"}),
            ("get_system_info", {}),
        ]

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        self.calls += 1
        if self.calls <= len(self.tools):
            tool, args = self.tools[self.calls - 1]
            return json.dumps({"action": "tool", "thought": "paso", "tool": tool, "args": args})
        return json.dumps({"action": "final", "response": "Listo."})

    def generate_stream(self, system_prompt: str, user_prompt: str):
        yield self.generate(system_prompt, user_prompt)


class PlanLoopStubProvider(ModelProvider):
    """Simula el comportamiento real: planifica una y otra vez sin ejecutar."""

    name = "stub3"

    def __init__(self) -> None:
        self.calls = 0

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        self.calls += 1
        if self.calls == 1:
            plan = ["Verifico si existe la carpeta en C:\\xampp\\htdocs", "Genero el dashboard"]
        elif self.calls == 2:
            plan = ["Verifico la carpeta ThunderDeck en C:\\xampp\\htdocs", "Genero el dashboard premium"]
        elif self.calls == 3:
            plan = ["Verifico si existe la carpeta ThunderDeck en C:\\xampp\\htdocs"]
        else:
            return json.dumps({"action": "final", "response": "Autonomía completada."})
        return json.dumps({"action": "plan", "thought": f"plan {self.calls}", "plan": plan})

    def generate_stream(self, system_prompt: str, user_prompt: str):
        yield self.generate(system_prompt, user_prompt)


class PlanThenFinalProvider(ModelProvider):
    """Planea una sola vez y luego responde."""

    name = "stub4"

    def __init__(self) -> None:
        self.calls = 0

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        self.calls += 1
        if self.calls == 1:
            return json.dumps({"action": "plan", "thought": "un plan", "plan": ["Creo la carpeta en C:\\xampp\\htdocs", "Abro el dashboard"]})
        return json.dumps({"action": "final", "response": "Plan aceptado, listo."})

    def generate_stream(self, system_prompt: str, user_prompt: str):
        yield self.generate(system_prompt, user_prompt)


def build_agent(provider: ModelProvider) -> BoltAgent:
    return BoltAgent(TEST_CONFIG, provider, vector=None)


def test_loop_stops_on_repeat_tool() -> None:
    provider = LoopStubProvider()
    agent = build_agent(provider)
    result = agent.run("ayudame con esta tarea")
    assert "Detuve la repetición" in result, f"Guardia no disparada: {result}"
    assert provider.calls <= TEST_CONFIG.max_repeat_tool + 2, f"Demasiadas llamadas: {provider.calls}"
    print(f"[OK] test_loop_stops_on_repeat_tool -> {provider.calls} llamadas, respuesta: {result[:80]}")


def test_duplicate_window_stops() -> None:
    provider = LoopStubProvider()
    agent = build_agent(provider)
    result = agent.run("hazlo de nuevo")
    assert "Detuve la repetición" in result or "Ya ejecuté" in result
    print(f"[OK] test_duplicate_window_stops -> {provider.calls} llamadas")


def test_direct_action_with_embedded_verb() -> None:
    """El regex debe detectar 'abre' aunque el mensaje no empiece con el verbo."""
    provider = DirectThenFinalProvider()
    agent = build_agent(provider)
    agent._execute_tool = lambda name, args: ToolResult(True, f"Abrí {args}.") if name == "open_app" else ToolResult(False, "no-op")
    result = agent.run("bien hecho, abre ahora la calculadora")
    assert "Abrí" in result
    assert provider.calls == 0, "No debería invocarse al modelo (acción directa)"
    print(f"[OK] test_direct_action_with_embedded_verb -> {result}")


def test_normal_response_works() -> None:
    provider = DirectThenFinalProvider()
    agent = build_agent(provider)
    result = agent.run("dame el estado del sistema")
    assert "Listo." in result
    assert provider.calls == 3
    print(f"[OK] test_normal_response_works -> {provider.calls} llamadas, respuesta: {result}")


def test_plan_loop_breaks() -> None:
    """El bucle de planificación debe romperse: tras 3 planes, se ejecuta una herramienta automáticamente."""
    provider = PlanLoopStubProvider()
    agent = build_agent(provider)
    events: list[dict] = []
    agent.subscribe(events.append)
    result = agent.run("hazme una prueba de autonomia")
    assert "Autonomía completada." in result
    assert provider.calls == 4, f"Debería parar tras 4 llamadas, no {provider.calls}"
    limits = [e for e in events if e["type"] == "limit"]
    assert limits and limits[0]["payload"]["reason"] == "plan_loop", "Faltó la detección de plan_loop"
    auto_tools = [e for e in events if e["type"] == "tool_result" and e["payload"].get("tool") == "list_directory"]
    assert auto_tools and auto_tools[0]["payload"]["ok"], "No se ejecutó la herramienta automática"
    print(f"[OK] test_plan_loop_breaks -> {provider.calls} llamadas, list_directory auto-ejecutado")


def test_plan_once_then_final() -> None:
    """Un único plan debe aceptarse y luego continuar sin repetirse."""
    provider = PlanThenFinalProvider()
    agent = build_agent(provider)
    result = agent.run("organiza algo")
    assert "Plan aceptado" in result
    assert provider.calls == 2, f"Esperaba 2 llamadas, hubo {provider.calls}"
    print(f"[OK] test_plan_once_then_final -> {provider.calls} llamadas")


def test_empty_model_output_handled() -> None:
    """Salida vacía del modelo debe dar un mensaje útil, no texto vacío."""
    provider = DirectThenFinalProvider()
    agent = build_agent(provider)
    fallback = agent._friendly_fallback("   \n  ")
    assert fallback and "vacía" in fallback
    print(f"[OK] test_empty_model_output_handled -> {fallback}")


def test_events_are_emitted() -> None:
    provider = DirectThenFinalProvider()
    agent = build_agent(provider)
    events: list[dict] = []
    agent.subscribe(events.append)
    agent.run("prueba de eventos")
    types = [e["type"] for e in events]
    assert "request" in types
    assert "tool_started" in types
    assert "tool_result" in types
    assert "final" in types
    print(f"[OK] test_events_are_emitted -> {len(events)} eventos: {types}")


def test_trace_logger_writes_files(tmp_dir: Path) -> None:
    logger = TraceLogger(directory=tmp_dir, enabled=True)
    logger.log("request", {"text": "hola"})
    logger.log("tool_result", {"tool": "open_app", "ok": True, "message": "Abrí calculadora"})
    logger.close()
    jsonl = list(tmp_dir.glob("trace_*.jsonl"))
    assert jsonl, "No se generó el archivo JSONL"
    lines = jsonl[0].read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2, f"Esperaba 2 líneas, hay {len(lines)}"
    console = tmp_dir / "bolt_console.log"
    assert console.exists() and console.read_text(encoding="utf-8").strip()
    print(f"[OK] test_trace_logger_writes_files -> {jsonl[0].name}, {len(lines)} eventos")


if __name__ == "__main__":
    from tempfile import TemporaryDirectory

    test_loop_stops_on_repeat_tool()
    test_duplicate_window_stops()
    test_direct_action_with_embedded_verb()
    test_normal_response_works()
    test_plan_loop_breaks()
    test_plan_once_then_final()
    test_empty_model_output_handled()
    test_events_are_emitted()
    with TemporaryDirectory() as tmp:
        test_trace_logger_writes_files(Path(tmp))
    print("\n=== TODOS LOS TESTS PASARON ===")
