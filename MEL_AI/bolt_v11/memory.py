from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from .config import MEMORY_DIR


@dataclass
class MemoryEvent:
    role: str
    text: str
    created_at: str


class JsonlMemory:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (MEMORY_DIR / "bolt_v11_memory.jsonl")
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def add(self, role: str, text: str) -> None:
        event = MemoryEvent(
            role=role,
            text=text,
            created_at=datetime.now().isoformat(timespec="seconds"),
        )
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")

    def recent(self, limit: int = 16) -> list[MemoryEvent]:
        if not self.path.exists():
            return []

        lines = self.path.read_text(encoding="utf-8").splitlines()[-limit:]
        events: list[MemoryEvent] = []
        for line in lines:
            try:
                payload = json.loads(line)
                events.append(MemoryEvent(**payload))
            except Exception:
                continue
        return events

    def render_recent(self, limit: int = 16) -> str:
        events = self.recent(limit=limit)
        if not events:
            return "Sin memoria previa relevante."
        return "\n".join(f"{event.role}: {event.text}" for event in events)
