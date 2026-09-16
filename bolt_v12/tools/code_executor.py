from __future__ import annotations

import os
import sys
import subprocess
import tempfile
import traceback
from pathlib import Path

from ..config import CODE_EXEC_DIR
from .base import Tool, ToolResult


def execute_python_code(code: str, timeout: int = 30) -> ToolResult:
    CODE_EXEC_DIR.mkdir(parents=True, exist_ok=True)
    script_path = CODE_EXEC_DIR / f"exec_{id(code) & 0xFFFFFF:06x}.py"
    try:
        script_path.write_text(code, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(CODE_EXEC_DIR),
        )
        stdout = result.stdout[-8000:] if result.stdout else ""
        stderr = result.stderr[-4000:] if result.stderr else ""
        ok = result.returncode == 0
        output = stdout
        if stderr:
            output += f"\n[ERROR]:\n{stderr}" if output else f"[ERROR]:\n{stderr}"
        if not output.strip():
            output = "Código ejecutado sin salida."
        return ToolResult(ok, output, {"returncode": result.returncode, "stdout": stdout, "stderr": stderr})
    except subprocess.TimeoutExpired:
        return ToolResult(False, f"Código expiró después de {timeout}s.")
    except Exception as exc:
        return ToolResult(False, f"Error ejecutando código: {exc}")
    finally:
        try:
            script_path.unlink(missing_ok=True)
        except Exception:
            pass


def execute_in_terminal(command: str, working_dir: str | None = None, timeout: int = 60) -> ToolResult:
    cwd = working_dir or str(Path.cwd())
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
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
        return ToolResult(False, f"Error: {exc}")


def install_package(package_name: str) -> ToolResult:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package_name],
            capture_output=True,
            text=True,
            timeout=120,
        )
        ok = result.returncode == 0
        output = result.stdout[-4000:] if result.stdout else ""
        if result.stderr:
            output += f"\n{result.stderr[-2000:]}"
        return ToolResult(ok, f"Instalación de {package_name}: {'exitosa' if ok else 'falló'}", {"output": output})
    except Exception as exc:
        return ToolResult(False, f"Error instalando {package_name}: {exc}")


def build_code_executor_tools() -> list[Tool]:
    return [
        Tool(
            name="execute_python_code",
            description="Ejecuta codigo Python y devuelve la salida. Ideal para calculos, procesamiento, scraping.",
            parameters={"code": "Codigo Python a ejecutar", "timeout": "Timeout opcional en segundos"},
            handler=execute_python_code,
        ),
        Tool(
            name="execute_in_terminal",
            description="Ejecuta un comando en la terminal/PowerShell.",
            parameters={"command": "Comando", "working_dir": "Directorio de trabajo opcional", "timeout": "Timeout opcional"},
            handler=execute_in_terminal,
            dangerous=True,
        ),
        Tool(
            name="install_package",
            description="Instala un paquete de Python via pip.",
            parameters={"package_name": "Nombre del paquete"},
            handler=install_package,
            dangerous=True,
        ),
    ]
