from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MEMORY_DIR = ROOT_DIR / "MEMORY" / "v12"
KNOWLEDGE_DIR = MEMORY_DIR / "conocimiento"
EPISODIC_DIR = MEMORY_DIR / "episodios"
PROJECTS_DIR = MEMORY_DIR / "proyectos"
DOWNLOADS_DIR = ROOT_DIR / "ThunderStudio" / "Descargas_Bolt"
GENERATED_3D_DIR = ROOT_DIR / "ThunderStudio" / "Modelos_3D_Bolt"
CHROMA_DIR = MEMORY_DIR / "chroma"
CODE_EXEC_DIR = ROOT_DIR / "ThunderStudio" / "CodeExecutions"


def _load_dotenv() -> None:
    env_path = ROOT_DIR / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass(frozen=True)
class BoltConfig:
    # Model
    model_provider: str
    gemini_api_key: str | None
    gemini_model: str
    bigpickle_model: str
    bigpickle_api_key: str | None
    bigpickle_base_url: str
    ollama_model: str
    ollama_base_url: str

    # Agent
    max_agent_steps: int
    planning_enabled: bool

    # Memory
    memory_limit: int
    vector_enabled: bool

    # Loop guards
    duplicate_window: int
    max_repeat_tool: int
    max_tools_per_turn: int
    loop_free_tools: tuple[str, ...]

    # Trace
    trace_enabled: bool
    log_retention_days: int

    # Proactive
    monitor_interval: int
    alert_threshold_cpu: int
    alert_threshold_disk: int

    # Paths
    root_dir: Path = ROOT_DIR
    memory_dir: Path = MEMORY_DIR
    knowledge_dir: Path = KNOWLEDGE_DIR
    episodic_dir: Path = EPISODIC_DIR
    projects_dir: Path = PROJECTS_DIR
    downloads_dir: Path = DOWNLOADS_DIR
    generated_3d_dir: Path = GENERATED_3D_DIR
    chroma_dir: Path = CHROMA_DIR
    code_exec_dir: Path = CODE_EXEC_DIR


def load_config() -> BoltConfig:
    _load_dotenv()
    for d in [MEMORY_DIR, KNOWLEDGE_DIR, EPISODIC_DIR, PROJECTS_DIR, CHROMA_DIR, CODE_EXEC_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    return BoltConfig(
        model_provider=os.getenv("BOLT_MODEL_PROVIDER", "bigpickle").lower(),
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        gemini_model=os.getenv("BOLT_GEMINI_MODEL", "gemini-2.5-flash"),
        bigpickle_model=os.getenv("BOLT_BIGPICKLE_MODEL", "big-pickle"),
        bigpickle_api_key=os.getenv("OPENCODE_API_KEY"),
        bigpickle_base_url=os.getenv("BOLT_BIGPICKLE_BASE_URL", "https://opencode.ai/zen/v1"),
        ollama_model=os.getenv("BOLT_LOCAL_MODEL", "llama3.1"),
        ollama_base_url=os.getenv("BOLT_OLLAMA_BASE_URL", "http://localhost:11434"),
        max_agent_steps=int(os.getenv("BOLT_MAX_AGENT_STEPS", "20")),
        planning_enabled=os.getenv("BOLT_PLANNING_ENABLED", "true").lower() == "true",
        memory_limit=int(os.getenv("BOLT_MEMORY_LIMIT", "50")),
        vector_enabled=os.getenv("BOLT_VECTOR_ENABLED", "true").lower() == "true",
        duplicate_window=int(os.getenv("BOLT_DUPLICATE_WINDOW", "4")),
        max_repeat_tool=int(os.getenv("BOLT_MAX_REPEAT_TOOL", "3")),
        max_tools_per_turn=int(os.getenv("BOLT_MAX_TOOLS_PER_TURN", "0")),
        loop_free_tools=tuple(
            t.strip().lower()
            for t in os.getenv(
                "BOLT_LOOP_FREE_TOOLS",
                "list_directory,read_text_file,search_files,get_file_info,"
                "git_status,git_log,git_diff,web_search,fetch_webpage,"
                "get_system_info,get_disk_usage,get_network_info,get_running_processes",
            ).split(",")
            if t.strip()
        ),
        trace_enabled=os.getenv("BOLT_TRACE_ENABLED", "true").lower() == "true",
        log_retention_days=int(os.getenv("BOLT_LOG_RETENTION_DAYS", "7")),
        monitor_interval=int(os.getenv("BOLT_MONITOR_INTERVAL", "30")),
        alert_threshold_cpu=int(os.getenv("BOLT_ALERT_CPU", "85")),
        alert_threshold_disk=int(os.getenv("BOLT_ALERT_DISK", "90")),
    )
