from __future__ import annotations

import os
from pathlib import Path

from .base import Tool, ToolResult


def _safe_path(path: str) -> Path:
    expanded = Path(os.path.expandvars(os.path.expanduser(path)))
    return expanded if expanded.is_absolute() else Path.cwd() / expanded


def read_text_file(path: str, max_chars: int = 30000) -> ToolResult:
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


def append_text_file(path: str, content: str) -> ToolResult:
    target = _safe_path(path)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "a", encoding="utf-8") as f:
            f.write(content)
        return ToolResult(True, f"Contenido agregado a: {target}", {"path": str(target)})
    except Exception as exc:
        return ToolResult(False, f"No pude agregar a {target}: {exc}")


def list_directory(path: str = ".") -> ToolResult:
    target = _safe_path(path)
    if not target.exists() or not target.is_dir():
        return ToolResult(False, f"No encontré la carpeta: {target}")
    try:
        items = []
        for item in sorted(target.iterdir(), key=lambda v: v.name.lower()):
            items.append({
                "name": item.name,
                "type": "dir" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else 0,
            })
        return ToolResult(True, f"Listado de {target}", {"path": str(target), "items": items})
    except Exception as exc:
        return ToolResult(False, f"No pude listar {target}: {exc}")


def make_directory(path: str) -> ToolResult:
    target = _safe_path(path)
    try:
        target.mkdir(parents=True, exist_ok=True)
        return ToolResult(True, f"Carpeta creada: {target}", {"path": str(target)})
    except Exception as exc:
        return ToolResult(False, f"No pude crear {target}: {exc}")


def delete_file(path: str) -> ToolResult:
    target = _safe_path(path)
    if not target.exists():
        return ToolResult(False, f"No encontré: {target}")
    try:
        if target.is_dir():
            import shutil
            shutil.rmtree(target)
        else:
            target.unlink()
        return ToolResult(True, f"Eliminado: {target}", {"path": str(target)})
    except Exception as exc:
        return ToolResult(False, f"No pude eliminar {target}: {exc}")


def search_files(path: str, pattern: str, max_results: int = 20) -> ToolResult:
    target = _safe_path(path)
    if not target.exists():
        return ToolResult(False, f"No encontré: {target}")
    try:
        matches = []
        for match in target.rglob(pattern):
            if len(matches) >= max_results:
                break
            matches.append({"path": str(match), "name": match.name, "type": "dir" if match.is_dir() else "file"})
        return ToolResult(True, f"Encontré {len(matches)} resultado(s)", {"matches": matches})
    except Exception as exc:
        return ToolResult(False, f"Error buscando: {exc}")


def get_file_info(path: str) -> ToolResult:
    target = _safe_path(path)
    if not target.exists():
        return ToolResult(False, f"No encontré: {target}")
    try:
        stat = target.stat()
        return ToolResult(True, f"Info de {target}", {
            "path": str(target),
            "name": target.name,
            "type": "dir" if target.is_dir() else "file",
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "created": stat.st_ctime,
        })
    except Exception as exc:
        return ToolResult(False, f"No pude obtener info: {exc}")


def build_file_tools() -> list[Tool]:
    return [
        Tool(
            name="read_text_file",
            description="Lee un archivo de texto local.",
            parameters={"path": "Ruta del archivo", "max_chars": "Maximo de caracteres opcional"},
            handler=read_text_file,
        ),
        Tool(
            name="write_text_file",
            description="Crea o sobrescribe un archivo de texto local.",
            parameters={"path": "Ruta destino", "content": "Contenido completo"},
            handler=write_text_file,
        ),
        Tool(
            name="append_text_file",
            description="Agrega contenido al final de un archivo existente.",
            parameters={"path": "Ruta del archivo", "content": "Contenido a agregar"},
            handler=append_text_file,
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
        Tool(
            name="delete_file",
            description="Elimina un archivo o carpeta. ACCION DESTRUCTIVA.",
            parameters={"path": "Ruta a eliminar"},
            handler=delete_file,
            dangerous=True,
        ),
        Tool(
            name="search_files",
            description="Busca archivos por patron glob en una carpeta.",
            parameters={"path": "Carpeta base", "pattern": " Patron (ej: *.py, *.txt)", "max_results": "Maximo opcional"},
            handler=search_files,
        ),
        Tool(
            name="get_file_info",
            description="Obtiene info detallada de un archivo: tamano, fechas, tipo.",
            parameters={"path": "Ruta del archivo"},
            handler=get_file_info,
        ),
    ]
