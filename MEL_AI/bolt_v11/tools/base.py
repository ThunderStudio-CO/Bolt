from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class ToolResult:
    ok: bool
    message: str
    data: dict[str, Any] | None = None


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    parameters: dict[str, str]
    handler: Callable[..., ToolResult]

    def render_for_prompt(self) -> str:
        params = ", ".join(f"{key}: {value}" for key, value in self.parameters.items())
        return f"- {self.name}({params}) -> {self.description}"
