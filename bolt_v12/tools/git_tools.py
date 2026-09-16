from __future__ import annotations

import subprocess
from pathlib import Path

from .base import Tool, ToolResult


def _run_git(args: list[str], cwd: str | None = None) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=cwd,
        )
        output = result.stdout.strip()
        if result.stderr.strip():
            output += f"\n{result.stderr.strip()}" if output else result.stderr.strip()
        return result.returncode == 0, output
    except FileNotFoundError:
        return False, "Git no está instalado o no está en PATH."
    except Exception as exc:
        return False, f"Error ejecutando git: {exc}"


def git_status(repo_path: str = ".") -> ToolResult:
    ok, output = _run_git(["status", "--short"], cwd=repo_path)
    return ToolResult(ok, output or "Sin cambios o no es un repositorio git.", {"output": output})


def git_log(repo_path: str = ".", limit: int = 10) -> ToolResult:
    ok, output = _run_git(["log", f"--oneline", f"-{limit}"], cwd=repo_path)
    return ToolResult(ok, output or "Sin commits.", {"output": output})


def git_diff(repo_path: str = ".", file_path: str | None = None) -> ToolResult:
    args = ["diff"]
    if file_path:
        args.append(file_path)
    ok, output = _run_git(args, cwd=repo_path)
    return ToolResult(ok, output or "Sin diferencias.", {"output": output})


def git_commit(repo_path: str = ".", message: str = "Update from Bolt", files: str | None = None) -> ToolResult:
    if files:
        for f in files.split(","):
            _run_git(["add", f.strip()], cwd=repo_path)
    else:
        _run_git(["add", "."], cwd=repo_path)
    ok, output = _run_git(["commit", "-m", message], cwd=repo_path)
    return ToolResult(ok, output or "Commit creado.", {"output": output})


def git_push(repo_path: str = ".", remote: str = "origin", branch: str = "main") -> ToolResult:
    ok, output = _run_git(["push", remote, branch], cwd=repo_path)
    return ToolResult(ok, output or "Push completado.", {"output": output})


def git_pull(repo_path: str = ".", remote: str = "origin") -> ToolResult:
    ok, output = _run_git(["pull", remote], cwd=repo_path)
    return ToolResult(ok, output or "Pull completado.", {"output": output})


def git_clone(url: str, destination: str = ".") -> ToolResult:
    ok, output = _run_git(["clone", url, destination])
    return ToolResult(ok, output or "Clonado completado.", {"output": output})


def git_branch_list(repo_path: str = ".") -> ToolResult:
    ok, output = _run_git(["branch", "-a"], cwd=repo_path)
    return ToolResult(ok, output or "Sin branches.", {"output": output})


def git_checkout(repo_path: str = ".", branch: str = "main") -> ToolResult:
    ok, output = _run_git(["checkout", branch], cwd=repo_path)
    return ToolResult(ok, output or f"Cambiado a {branch}.", {"output": output})


def build_git_tools() -> list[Tool]:
    return [
        Tool(
            name="git_status",
            description="Muestra el estado del repositorio git.",
            parameters={"repo_path": "Ruta del repositorio opcional"},
            handler=git_status,
        ),
        Tool(
            name="git_log",
            description="Muestra los ultimos commits.",
            parameters={"repo_path": "Ruta del repositorio opcional", "limit": "Cantidad de commits"},
            handler=git_log,
        ),
        Tool(
            name="git_diff",
            description="Muestra las diferencias actuales.",
            parameters={"repo_path": "Ruta del repositorio opcional", "file_path": "Archivo especifico opcional"},
            handler=git_diff,
        ),
        Tool(
            name="git_commit",
            description="Crea un commit con los cambios.",
            parameters={"repo_path": "Ruta del repositorio", "message": "Mensaje del commit", "files": "Archivos especificos (separados por coma)"},
            handler=git_commit,
        ),
        Tool(
            name="git_push",
            description="Sube commits al remoto.",
            parameters={"repo_path": "Ruta del repositorio", "remote": "Remote name", "branch": "Branch"},
            handler=git_push,
            dangerous=True,
        ),
        Tool(
            name="git_pull",
            description="Descarga cambios del remoto.",
            parameters={"repo_path": "Ruta del repositorio", "remote": "Remote name"},
            handler=git_pull,
        ),
        Tool(
            name="git_clone",
            description="Clona un repositorio git.",
            parameters={"url": "URL del repositorio", "destination": "Carpeta destino"},
            handler=git_clone,
        ),
        Tool(
            name="git_branch_list",
            description="Lista todas las branches.",
            parameters={"repo_path": "Ruta del repositorio"},
            handler=git_branch_list,
        ),
        Tool(
            name="git_checkout",
            description="Cambia a otra branch.",
            parameters={"repo_path": "Ruta del repositorio", "branch": "Nombre de la branch"},
            handler=git_checkout,
        ),
    ]
