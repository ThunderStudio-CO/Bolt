from __future__ import annotations

import os
import subprocess
import webbrowser
from pathlib import Path

from .base import Tool, ToolResult


KNOWN_FOLDERS = {
    "escritorio": "Desktop",
    "desktop": "Desktop",
    "documentos": "Documents",
    "documents": "Documents",
    "descargas": "Downloads",
    "downloads": "Downloads",
}

KNOWN_APPS = {
    "chrome": ["cmd", "/c", "start", "", "chrome"],
    "navegador": ["cmd", "/c", "start", "", "chrome"],
    "edge": ["cmd", "/c", "start", "", "msedge"],
    "vscode": ["cmd", "/c", "start", "", "code"],
    "visual studio code": ["cmd", "/c", "start", "", "code"],
    "code": ["cmd", "/c", "start", "", "code"],
    "calculadora": ["calc"],
    "calculator": ["calc"],
    "bloc de notas": ["notepad"],
    "notepad": ["notepad"],
    "explorador": ["explorer"],
    "archivos": ["explorer"],
    "blender": ["cmd", "/c", "start", "", "blender"],
    "python": ["cmd", "/c", "start", "", "python"],
    "terminal": ["cmd", "/c", "start", "", "cmd"],
    "powershell": ["cmd", "/c", "start", "", "powershell"],
}


def _resolve_path(path: str) -> Path:
    lowered = path.lower().strip()
    home = Path.home()
    if lowered in KNOWN_FOLDERS:
        candidate = home / KNOWN_FOLDERS[lowered]
        if candidate.exists():
            return candidate
    expanded = Path(os.path.expandvars(os.path.expanduser(path)))
    return expanded if expanded.is_absolute() else Path.cwd() / expanded


def open_path(path: str) -> ToolResult:
    target = _resolve_path(path)
    if not target.exists():
        return ToolResult(False, f"No encontré la ruta: {target}")
    try:
        os.startfile(str(target))
        return ToolResult(True, f"Abrí {target}", {"path": str(target)})
    except Exception as exc:
        return ToolResult(False, f"No pude abrir {target}: {exc}")


def reveal_path(path: str) -> ToolResult:
    target = _resolve_path(path)
    if not target.exists():
        return ToolResult(False, f"No encontré la ruta: {target}")
    try:
        if target.is_file():
            subprocess.Popen(["explorer", "/select,", str(target)])
        else:
            subprocess.Popen(["explorer", str(target)])
        return ToolResult(True, f"Mostré {target} en el explorador.", {"path": str(target)})
    except Exception as exc:
        return ToolResult(False, f"No pude mostrar {target}: {exc}")


def open_app(app_name: str) -> ToolResult:
    normalized = app_name.lower().strip()
    command = KNOWN_APPS.get(normalized)
    if command is None:
        command = ["cmd", "/c", "start", "", app_name]
    try:
        subprocess.Popen(command)
        return ToolResult(True, f"Abrí {app_name}.", {"app": app_name})
    except Exception as exc:
        return ToolResult(False, f"No pude abrir {app_name}: {exc}")


def open_url(url: str) -> ToolResult:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        webbrowser.open(url)
        return ToolResult(True, f"Abrí {url}.", {"url": url})
    except Exception as exc:
        return ToolResult(False, f"No pude abrir {url}: {exc}")


def run_shell_command(command: str, timeout: int = 60) -> ToolResult:
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(Path.home()),
        )
        stdout = result.stdout[-8000:] if result.stdout else ""
        stderr = result.stderr[-4000:] if result.stderr else ""
        ok = result.returncode == 0
        output = stdout
        if stderr:
            output += f"\n[STDERR]:\n{stderr}" if output else f"[STDERR]:\n{stderr}"
        if not output.strip():
            output = "Comando ejecutado sin salida."
        return ToolResult(ok, output, {"returncode": result.returncode, "stdout": stdout, "stderr": stderr})
    except subprocess.TimeoutExpired:
        return ToolResult(False, f"Comando expiró después de {timeout}s.")
    except Exception as exc:
        return ToolResult(False, f"Error ejecutando comando: {exc}")


def build_system_tools() -> list[Tool]:
    return [
        Tool(
            name="open_path",
            description="Abre un archivo o carpeta local.",
            parameters={"path": "Ruta o nombre conocido"},
            handler=open_path,
        ),
        Tool(
            name="reveal_path",
            description="Muestra un archivo o carpeta en el Explorador.",
            parameters={"path": "Ruta o nombre conocido"},
            handler=reveal_path,
        ),
        Tool(
            name="open_app",
            description="Abre una aplicacion como chrome, vscode, blender.",
            parameters={"app_name": "Nombre de la aplicacion"},
            handler=open_app,
        ),
        Tool(
            name="open_url",
            description="Abre una URL en el navegador.",
            parameters={"url": "URL o dominio"},
            handler=open_url,
        ),
        Tool(
            name="run_shell_command",
            description="Ejecuta un comando de shell/PowerShell. Puede instalar paquetes, compilar, ejecutar git, etc.",
            parameters={"command": "Comando a ejecutar", "timeout": "Timeout en segundos opcional"},
            handler=run_shell_command,
            dangerous=True,
        ),
    ]
