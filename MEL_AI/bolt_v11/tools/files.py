from __future__ import annotations

import os
from pathlib import Path

from .base import Tool, ToolResult


def _safe_path(path: str) -> Path:
    expanded = Path(os.path.expandvars(os.path.expanduser(path)))
    return expanded if expanded.is_absolute() else Path.cwd() / expanded


def read_text_file(path: str, max_chars: int = 20000) -> ToolResult:
    target = _safe_path(path)
    if not target.exists() or not target.is_file():
        return ToolResult(False, f"No encontré el archivo: {target}")
    try:
        text = target.read_text(encoding="utf-8", errors="replace")[:max_chars]
        return ToolResult(True, f"Leí {target}", {"path": str(target), "text": text})
    except Exception as exc:
        return ToolResult(False, f"No pude leer {target}: {exc}")


def write_text_file(path: str, content: str) -> ToolResult:
    target = _safe_path(path)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return ToolResult(True, f"Archivo escrito: {target}", {"path": str(target)})
    except Exception as exc:
        return ToolResult(False, f"No pude escribir {target}: {exc}")


def list_directory(path: str = ".") -> ToolResult:
    target = _safe_path(path)
    if not target.exists() or not target.is_dir():
        return ToolResult(False, f"No encontré la carpeta: {target}")
    try:
        items = [
            {"name": item.name, "type": "dir" if item.is_dir() else "file"}
            for item in sorted(target.iterdir(), key=lambda value: value.name.lower())
        ]
        return ToolResult(True, f"Listado de {target}", {"path": str(target), "items": items})
    except Exception as exc:
        return ToolResult(False, f"No pude listar {target}: {exc}")


def make_directory(path: str) -> ToolResult:
    target = _safe_path(path)
    try:
        target.mkdir(parents=True, exist_ok=True)
        return ToolResult(True, f"Carpeta lista: {target}", {"path": str(target)})
    except Exception as exc:
        return ToolResult(False, f"No pude crear {target}: {exc}")


def build_file_tools() -> list[Tool]:
    return [
        Tool(
            name="read_text_file",
            description="Lee un archivo de texto local.",
            parameters={"path": "Ruta del archivo", "max_chars": "Máximo de caracteres opcional"},
            handler=read_text_file,
        ),
        Tool(
            name="write_text_file",
            description="Crea o sobrescribe un archivo de texto local.",
            parameters={"path": "Ruta destino", "content": "Contenido completo"},
            handler=write_text_file,
        ),
        Tool(
            name="list_directory",
            description="Lista archivos y carpetas de una ruta local.",
            parameters={"path": "Ruta de carpeta opcional"},
            handler=list_directory,
        ),
        Tool(
            name="make_directory",
            description="Crea una carpeta local.",
            parameters={"path": "Ruta de carpeta"},
            handler=make_directory,
        ),
    ]
