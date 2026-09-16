from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path

from .config import MEMORY_DIR


LOG_DIR = MEMORY_DIR / "logs"


class TraceLogger:
    def __init__(
        self,
        directory: Path | None = None,
        retention_days: int = 7,
        enabled: bool = True,
    ) -> None:
        self.directory = Path(directory) if directory else LOG_DIR
        self.retention_days = max(1, int(retention_days))
        self.enabled = bool(enabled)
        self._lock = threading.Lock()
        self._day: str | None = None
        self._jsonl_handle = None
        self._console_handle = None
        if self.enabled:
            self.directory.mkdir(parents=True, exist_ok=True)

    def _ensure_files(self) -> None:
        day = datetime.now().strftime("%Y-%m-%d")
        if day == self._day and self._jsonl_handle is not None:
            return
        self._close_handles()
        self.directory.mkdir(parents=True, exist_ok=True)
        self._jsonl_handle = (self.directory / f"trace_{day}.jsonl").open("a", encoding="utf-8")
        self._console_handle = (self.directory / "bolt_console.log").open("a", encoding="utf-8")
        self._day = day
        self._prune()

    def _close_handles(self) -> None:
        for handle in (self._jsonl_handle, self._console_handle):
            if handle is not None:
                try:
                    handle.flush()
                    handle.close()
                except Exception:
                    pass
        self._jsonl_handle = None
        self._console_handle = None

    def _prune(self) -> None:
        try:
            cutoff = datetime.now().timestamp() - self.retention_days * 86400
            for path in self.directory.glob("trace_*.jsonl"):
                try:
                    if path.stat().st_mtime < cutoff:
                        path.unlink()
                except OSError:
                    continue
        except Exception:
            pass

    def log(self, event_type: str, payload: dict) -> None:
        if not self.enabled:
            return
        record = {
            "ts": datetime.now().isoformat(timespec="milliseconds"),
            "thread": threading.current_thread().name,
            "type": event_type,
            "payload": payload,
        }
        line = json.dumps(record, ensure_ascii=False)
        with self._lock:
            try:
                self._ensure_files()
                if self._jsonl_handle is not None:
                    self._jsonl_handle.write(line + "\n")
                    self._jsonl_handle.flush()
                if self._console_handle is not None:
                    self._console_handle.write(self._pretty(record) + "\n")
                    self._console_handle.flush()
            except Exception:
                pass

    def close(self) -> None:
        with self._lock:
            self._close_handles()

    @staticmethod
    def _pretty(record: dict) -> str:
        etype = record.get("type", "info")
        payload = record.get("payload", {})
        ts = record.get("ts", "")
        brief = str(payload.get("brief") or payload.get("line") or "")
        if not brief:
            try:
                brief = json.dumps(payload, ensure_ascii=False)[:300]
            except Exception:
                brief = ""
        return f"[{ts}] [{etype.upper()}] {brief}"
