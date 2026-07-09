from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MEMORY_DIR = ROOT_DIR / "MEMORY"
DOWNLOADS_DIR = ROOT_DIR / "ThunderStudio" / "Descargas_Bolt"
GENERATED_3D_DIR = ROOT_DIR / "ThunderStudio" / "Modelos_3D_Bolt"


def _load_dotenv() -> None:
    env_path = ROOT_DIR / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


@dataclass(frozen=True)
class BoltConfig:
    model_provider: str
    local_model: str
    gemini_model: str
    ollama_base_url: str
    gemini_api_key: str | None
    max_agent_steps: int


def load_config() -> BoltConfig:
    _load_dotenv()
    return BoltConfig(
        model_provider=os.getenv("BOLT_MODEL_PROVIDER", "auto").lower(),
        local_model=os.getenv("BOLT_LOCAL_MODEL", "llama3.1"),
        gemini_model=os.getenv("BOLT_GEMINI_MODEL", "gemini-3.1-flash-lite"),
        ollama_base_url=os.getenv("BOLT_OLLAMA_BASE_URL", "http://localhost:11434"),
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        max_agent_steps=int(os.getenv("BOLT_MAX_AGENT_STEPS", "6")),
    )
