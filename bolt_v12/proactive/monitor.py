from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable

from ..config import BoltConfig
from ..tools.monitor import get_system_info, monitor_alerts, get_running_processes


@dataclass
class Alert:
    level: str
    message: str
    timestamp: str
    data: dict = field(default_factory=dict)


class SystemMonitor:
    def __init__(self, config: BoltConfig) -> None:
        self.config = config
        self.alerts: list[Alert] = []
        self._running = False
        self._thread: threading.Thread | None = None
        self._callbacks: list[Callable[[Alert], None]] = []
        self._last_cpu = 0.0
        self._last_disk = 0.0
        self._last_memory = 0.0

    def on_alert(self, callback: Callable[[Alert], None]) -> None:
        self._callbacks.append(callback)

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

    def _monitor_loop(self) -> None:
        while self._running:
            try:
                result = monitor_alerts(
                    cpu_threshold=self.config.alert_threshold_cpu,
                    disk_threshold=self.config.alert_threshold_disk,
                )
                if result.ok and result.data:
                    self._last_cpu = result.data.get("cpu", 0)
                    self._last_disk = result.data.get("disk", 0)
                    self._last_memory = result.data.get("memory", 0)

                    if result.data.get("has_alerts"):
                        for alert_msg in result.data.get("alerts", []):
                            alert = Alert(
                                level="warning",
                                message=alert_msg,
                                timestamp=datetime.now().isoformat(timespec="seconds"),
                                data={"cpu": self._last_cpu, "disk": self._last_disk, "memory": self._last_memory},
                            )
                            self.alerts.append(alert)
                            for cb in self._callbacks:
                                try:
                                    cb(alert)
                                except Exception:
                                    pass
            except Exception:
                pass
            time.sleep(self.config.monitor_interval)

    def get_status(self) -> dict:
        return {
            "monitoring": self._running,
            "cpu": self._last_cpu,
            "disk": self._last_disk,
            "memory": self._last_memory,
            "alert_count": len(self.alerts),
            "recent_alerts": [a.message for a in self.alerts[-5:]],
        }


class BackgroundTask:
    def __init__(self, name: str, interval: int, func: Callable[[], None]) -> None:
        self.name = name
        self.interval = interval
        self.func = func
        self._running = False
        self._thread: threading.Thread | None = None
        self.last_run: str | None = None

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

    def _run_loop(self) -> None:
        while self._running:
            try:
                self.func()
                self.last_run = datetime.now().isoformat(timespec="seconds")
            except Exception:
                pass
            time.sleep(self.interval)


class TaskScheduler:
    def __init__(self) -> None:
        self.tasks: list[BackgroundTask] = []

    def add_task(self, name: str, interval: int, func: Callable[[], None]) -> BackgroundTask:
        task = BackgroundTask(name, interval, func)
        self.tasks.append(task)
        return task

    def start_all(self) -> None:
        for task in self.tasks:
            task.start()

    def stop_all(self) -> None:
        for task in self.tasks:
            task.stop()

    def get_status(self) -> list[dict]:
        return [
            {"name": t.name, "running": t._running, "last_run": t.last_run}
            for t in self.tasks
        ]
