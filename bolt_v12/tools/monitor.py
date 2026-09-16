from __future__ import annotations

import os
import platform
from datetime import datetime
from pathlib import Path

from .base import Tool, ToolResult


def get_system_info() -> ToolResult:
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        
        info = {
            "os": platform.system(),
            "os_version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python": platform.python_version(),
            "cpu_percent": cpu_percent,
            "cpu_count": psutil.cpu_count(),
            "ram_total_gb": round(memory.total / (1024**3), 2),
            "ram_used_gb": round(memory.used / (1024**3), 2),
            "ram_percent": memory.percent,
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "disk_used_gb": round(disk.used / (1024**3), 2),
            "disk_percent": disk.percent,
            "uptime_hours": round((datetime.now().timestamp() - psutil.boot_time()) / 3600, 1),
        }
        return ToolResult(True, f"Sistema: {info['os']} {info['os_version']}", info)
    except ImportError:
        info = {
            "os": platform.system(),
            "os_version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python": platform.python_version(),
        }
        return ToolResult(True, "Info básica (instala psutil para info completa)", info)
    except Exception as exc:
        return ToolResult(False, f"Error obteniendo info del sistema: {exc}")


def get_running_processes(limit: int = 15) -> ToolResult:
    try:
        import psutil
        processes = []
        for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                info = proc.info
                processes.append({
                    "pid": info["pid"],
                    "name": info["name"],
                    "cpu": info["cpu_percent"],
                    "memory": round(info["memory_percent"], 1),
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        processes.sort(key=lambda x: x["memory"], reverse=True)
        return ToolResult(True, f"Top {limit} procesos por uso de memoria", {"processes": processes[:limit]})
    except ImportError:
        return ToolResult(False, "Instala psutil: pip install psutil")
    except Exception as exc:
        return ToolResult(False, f"Error: {exc}")


def get_disk_usage(path: str = "/") -> ToolResult:
    try:
        import psutil
        usage = psutil.disk_usage(path)
        return ToolResult(True, f"Uso de disco en {path}", {
            "total_gb": round(usage.total / (1024**3), 2),
            "used_gb": round(usage.used / (1024**3), 2),
            "free_gb": round(usage.free / (1024**3), 2),
            "percent": usage.percent,
        })
    except Exception as exc:
        return ToolResult(False, f"Error: {exc}")


def get_network_info() -> ToolResult:
    try:
        import psutil
        net = psutil.net_io_counters()
        return ToolResult(True, "Info de red", {
            "bytes_sent_gb": round(net.bytes_sent / (1024**3), 2),
            "bytes_recv_gb": round(net.bytes_recv / (1024**3), 2),
            "packets_sent": net.packets_sent,
            "packets_recv": net.packets_recv,
        })
    except ImportError:
        return ToolResult(False, "Instala psutil: pip install psutil")
    except Exception as exc:
        return ToolResult(False, f"Error: {exc}")


def monitor_alerts(cpu_threshold: int = 85, disk_threshold: int = 90) -> ToolResult:
    try:
        import psutil
        alerts = []
        cpu = psutil.cpu_percent(interval=1)
        disk = psutil.disk_usage("/").percent
        memory = psutil.virtual_memory().percent
        
        if cpu > cpu_threshold:
            alerts.append(f"CPU alta: {cpu}% (umbral: {cpu_threshold}%)")
        if disk > disk_threshold:
            alerts.append(f"Disco bajo: {100-disk}% libre (umbral: {disk_threshold}% usado)")
        if memory > 90:
            alerts.append(f"RAM alta: {memory}%")
        
        return ToolResult(True, f"Alertas: {len(alerts)}", {
            "alerts": alerts,
            "cpu": cpu,
            "disk": disk,
            "memory": memory,
            "has_alerts": len(alerts) > 0,
        })
    except ImportError:
        return ToolResult(False, "Instala psutil: pip install psutil")
    except Exception as exc:
        return ToolResult(False, f"Error: {exc}")


def get_current_directory_info() -> ToolResult:
    cwd = Path.cwd()
    items = list(cwd.iterdir())
    dirs = sum(1 for i in items if i.is_dir())
    files = sum(1 for i in items if i.is_file())
    return ToolResult(True, f"Directorio actual: {cwd}", {
        "path": str(cwd),
        "total_dirs": dirs,
        "total_files": files,
        "parent": str(cwd.parent),
    })


def build_monitor_tools() -> list[Tool]:
    return [
        Tool(
            name="get_system_info",
            description="Obtiene info completa del sistema: CPU, RAM, disco, OS.",
            parameters={},
            handler=get_system_info,
        ),
        Tool(
            name="get_running_processes",
            description="Lista procesos en ejecucion ordenados por uso de memoria.",
            parameters={"limit": "Cantidad de procesos a mostrar"},
            handler=get_running_processes,
        ),
        Tool(
            name="get_disk_usage",
            description="Muestra uso de disco de una ruta.",
            parameters={"path": "Ruta a analizar"},
            handler=get_disk_usage,
        ),
        Tool(
            name="get_network_info",
            description="Obtiene estadisticas de red.",
            parameters={},
            handler=get_network_info,
        ),
        Tool(
            name="monitor_alerts",
            description="Verifica si hay alertas del sistema (CPU, disco, RAM).",
            parameters={"cpu_threshold": "Umbral CPU opcional", "disk_threshold": "Umbral disco opcional"},
            handler=monitor_alerts,
        ),
        Tool(
            name="get_current_directory_info",
            description="Info del directorio de trabajo actual.",
            parameters={},
            handler=get_current_directory_info,
        ),
    ]
