from __future__ import annotations

import re
import threading
import tkinter as tk
from tkinter import scrolledtext

from bolt_v12.config import load_config
from bolt_v12.models import build_model_provider
from bolt_v12.memory import EpisodicMemory, KnowledgeMemory, VectorMemory
from bolt_v12.agent import BoltAgent
from bolt_v12.proactive import SystemMonitor
from bolt_v12.trace import TraceLogger


TRACE_TAGS = {
    "request": ("#a7ecff", False),
    "step": ("#8b93a7", False),
    "model_output": ("#6b7280", False),
    "reasoning": ("#00e5ff", False),
    "tool_started": ("#ffd166", False),
    "tool_result": ("#4ade80", False),
    "guard": ("#fb923c", False),
    "plan": ("#c084fc", False),
    "learn": ("#4ade80", False),
    "direct": ("#4ade80", False),
    "limit": ("#f87171", True),
    "final": ("#ffffff", True),
    "info": ("#9ca3af", False),
}


class BoltV12App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.config_data = load_config()
        self.provider = build_model_provider(self.config_data)
        self.episodic = EpisodicMemory()
        self.knowledge = KnowledgeMemory()
        self.vector = VectorMemory()
        self.trace_logger = TraceLogger(
            enabled=self.config_data.trace_enabled,
            retention_days=self.config_data.log_retention_days,
        )
        self.agent = BoltAgent(
            self.config_data, self.provider,
            episodic=self.episodic,
            knowledge=self.knowledge,
            vector=self.vector,
        )
        self.agent.subscribe(self._on_trace_event)
        self.monitor = SystemMonitor(self.config_data)
        self.monitor.on_alert(self._on_alert)

        self.title(f"Bolt V12 - Asistente Agentic ({self.provider.name})")
        self.geometry("1000x720")
        self.minsize(800, 520)
        self.configure(bg="#05070d")

        self.chat = scrolledtext.ScrolledText(
            self, wrap=tk.WORD, bg="#070b12", fg="#00e5ff",
            insertbackground="#00e5ff", font=("Consolas", 11),
        )
        self.chat.pack(fill=tk.BOTH, expand=True, padx=16, pady=(16, 8))
        self.chat.insert(tk.END, f"BOLT V12 en linea | Proveedor: {self.provider.name}\n")
        self.chat.insert(tk.END, f"Memoria episodica: {self.episodic.count()} eventos\n")
        self.chat.insert(tk.END, f"Memoria vectorial: {self.vector.count()} documentos\n")
        self.chat.insert(tk.END, "Modos: normal, constructor, investigador, sistema, creativo\n")
        self.chat.insert(tk.END, f"Log de traza: {self.trace_logger.directory}\n\n")
        self.chat.configure(state=tk.DISABLED)

        self.trace_visible = False
        self.trace_panel = tk.Frame(self, bg="#0a0f16")
        self.trace_header = tk.Frame(self.trace_panel, bg="#0a0f16")
        self.trace_header.pack(fill=tk.X)
        self.trace_label = tk.Label(
            self.trace_header, text="TRACE EN VIVO", bg="#0a0f16", fg="#fb923c",
            font=("Consolas", 10, "bold"),
        )
        self.trace_label.pack(side=tk.LEFT, padx=6, pady=2)
        self.trace_close = tk.Button(
            self.trace_header, text="OCULTAR", command=self._toggle_trace,
            bg="#263244", fg="#ffffff", relief=tk.FLAT, font=("Consolas", 8, "bold"),
        )
        self.trace_close.pack(side=tk.RIGHT, padx=6, pady=2)
        self.trace = scrolledtext.ScrolledText(
            self.trace_panel, wrap=tk.WORD, bg="#070b12", fg="#9ca3af",
            insertbackground="#9ca3af", relief=tk.FLAT, height=12, font=("Consolas", 9),
        )
        self.trace.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 4))
        for tag, (color, bold) in TRACE_TAGS.items():
            self.trace.tag_configure(tag, foreground=color, font=("Consolas", 9, "bold" if bold else "normal"))

        bottom = tk.Frame(self, bg="#05070d")
        bottom.pack(fill=tk.X, padx=16, pady=(0, 16))

        self.entry = tk.Entry(
            bottom, bg="#111827", fg="#ffffff", insertbackground="#ffffff",
            font=("Consolas", 11),
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), ipady=8)
        self.entry.bind("<Return>", lambda _e: self._send())

        self.trace_button = tk.Button(
            bottom, text="TRACE: MOSTRAR", command=self._toggle_trace,
            bg="#263244", fg="#fb923c", activebackground="#334155",
            activeforeground="#fb923c", relief=tk.FLAT, font=("Consolas", 9, "bold"),
        )
        self.trace_button.pack(side=tk.RIGHT, padx=(8, 0), ipady=5)

        self.button = tk.Button(
            bottom, text="EJECUTAR", command=self._send,
            bg="#1e3a8a", fg="#ffffff", activebackground="#00a8c6",
            activeforeground="#ffffff", font=("Consolas", 11, "bold"),
        )
        self.button.pack(side=tk.RIGHT, ipadx=18, ipady=5)

        self.monitor.start()
        self.protocol("WM_DELETE_WINDOW", self._close)

    def _toggle_trace(self) -> None:
        self.trace_visible = not self.trace_visible
        if self.trace_visible:
            self.trace_panel.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 8))
            self.trace_button.configure(text="TRACE: OCULTAR")
            self.trace_label.configure(text="TRACE EN VIVO")
        else:
            self.trace_panel.pack_forget()
            self.trace_button.configure(text="TRACE: MOSTRAR")

    def _on_trace_event(self, event: dict) -> None:
        self.trace_logger.log(event.get("type", "info"), event.get("payload", {}))
        if self.trace_visible:
            self.after(0, self._render_trace, event)

    def _render_trace(self, event: dict) -> None:
        etype = event.get("type", "info")
        payload = event.get("payload", {}) or {}
        tag = etype if etype in TRACE_TAGS else "info"
        ts = event.get("ts", "")
        line = self._trace_line(etype, payload, ts)
        self.trace.configure(state=tk.NORMAL)
        self.trace.insert(tk.END, line, tag)
        self.trace.configure(state=tk.DISABLED)
        self.trace.see(tk.END)

    def _trace_line(self, etype: str, payload: dict, ts: str) -> str:
        prefix = f"{ts[11:23]} "
        if etype == "request":
            return f"{prefix}[SOLICITUD] {payload.get('text', '')}\n"
        if etype == "step":
            return f"{prefix}[PASO {payload.get('step')}/{payload.get('max')}]\n"
        if etype == "reasoning":
            return f"{prefix}  razon: {payload.get('thought', '')}\n"
        if etype == "model_output":
            return f"{prefix}  modelo: {str(payload.get('output', ''))[:220]}\n"
        if etype == "tool_started":
            return f"{prefix}  -> {payload.get('tool')}({payload.get('args')})\n"
        if etype == "tool_result":
            status = "OK" if payload.get("ok") else "FALLO"
            return f"{prefix}  [{status}] {payload.get('message', '')}\n"
        if etype == "guard":
            return f"{prefix}  [GUARDIA-{str(payload.get('kind', '')).upper()}] {payload.get('tool')}({payload.get('args')})\n"
        if etype == "plan":
            return f"{prefix}  [PLAN] {payload.get('index')}. {payload.get('item')}\n"
        if etype == "learn":
            return f"{prefix}  [APRENDIZAJE] {payload.get('fact', payload.get('preference', ''))}\n"
        if etype == "direct":
            return f"{prefix}[DIRECTO] {payload.get('response', '')}\n"
        if etype == "limit":
            return f"{prefix}[LÍMITE] {payload.get('summary', '')}\n"
        if etype == "final":
            return f"{prefix}[BOLT] {payload.get('response', '')}\n"
        return f"{prefix}[{etype.upper()}] {payload.get('detail', payload)}\n"

    def _send(self, event=None) -> None:
        message = self.entry.get().strip()
        if not message:
            return
        self.entry.delete(0, tk.END)
        self._append(f"Miguel: {message}\nBolt: ")
        self.button.configure(state=tk.DISABLED, text="PROCESANDO...")
        threading.Thread(target=self._run_agent, args=(message,), daemon=True).start()

    def _run_agent(self, message: str) -> None:
        try:
            response = self.agent.run(message)
        except Exception as exc:
            response = f"[ERROR]: {exc}"
        self.after(0, self._finish_response, response)

    def _finish_response(self, response: str) -> None:
        clean = re.sub(r"\[(EJECUTAR|CARPETA|BUSCAR|EDITAR|CREAR_ARCHIVO|LISTAR|ABRIR_ARCHIVO|CREAR_CARPETA|LEER_ARCHIVO):\s*(.*?)\]", "", response)
        self._append(clean + "\n\n")
        self.button.configure(state=tk.NORMAL, text="EJECUTAR")
        self.entry.focus()

    def _on_alert(self, alert) -> None:
        self.after(0, self._append, f"\n[ALERTA]: {alert.message}\n\n")

    def _append(self, text: str) -> None:
        self.chat.configure(state=tk.NORMAL)
        self.chat.insert(tk.END, text)
        self.chat.configure(state=tk.DISABLED)
        self.chat.see(tk.END)

    def _close(self) -> None:
        self.monitor.stop()
        self.trace_logger.close()
        self.destroy()


if __name__ == "__main__":
    BoltV12App().mainloop()
