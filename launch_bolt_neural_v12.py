from __future__ import annotations

import math
import random
import re
import threading
import time
import tkinter as tk
from tkinter import scrolledtext

from bolt_v12.config import load_config
from bolt_v12.models import build_model_provider
from bolt_v12.memory import EpisodicMemory, KnowledgeMemory, VectorMemory
from bolt_v12.agent import BoltAgent
from bolt_v12.voice import VoiceEngine
from bolt_v12.proactive import SystemMonitor
from bolt_v12.trace import TraceLogger
from bolt_v12.ui import NeuralCanvas, PALETTES


TRACE_TAGS = {
    "request": "#a7ecff", "step": "#8b93a7", "model_output": "#6b7280",
    "reasoning": "#00e5ff", "tool_started": "#ffd166", "tool_result": "#4ade80",
    "guard": "#fb923c", "plan": "#c084fc", "learn": "#4ade80",
    "direct": "#4ade80", "limit": "#f87171", "final": "#ffffff", "info": "#9ca3af",
}


class BoltNeuralV12App(tk.Tk):
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
        self.trace_visible = True
        self.agent = BoltAgent(
            self.config_data, self.provider,
            episodic=self.episodic,
            knowledge=self.knowledge,
            vector=self.vector,
        )
        self.agent.subscribe(self._on_trace_event)
        self.voice = VoiceEngine()
        self.monitor = SystemMonitor(self.config_data)
        self.monitor.on_alert(self._on_alert)
        self.mode = "normal"
        self.stop_listening = None

        self.title(f"Bolt Neural V12 - {self.provider.name}")
        self.geometry("1100x780")
        self.minsize(800, 560)
        self.configure(bg=PALETTES["normal"]["bg"])

        self.canvas = NeuralCanvas(self, bg=PALETTES["normal"]["bg"])
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.overlay = tk.Frame(self.canvas, bg=PALETTES["normal"]["bg"])
        self.overlay_id = self.canvas.create_window(0, 0, anchor="nw", window=self.overlay, tags="overlay")
        self.canvas.bind("<Configure>", self._position_overlay)

        self.status = tk.Label(
            self.overlay, text="BOLT NEURAL V12",
            bg=PALETTES["normal"]["bg"], fg=PALETTES["normal"]["accent"],
            font=("Consolas", 22, "bold"),
        )
        self.status.pack(anchor="w", padx=28, pady=(24, 0))

        self.substatus = tk.Label(
            self.overlay,
            text=f"Big Pickle ({self.provider.name}) | Memoria: {self.episodic.count()} eps, {self.vector.count()} vec",
            bg=PALETTES["normal"]["bg"], fg="#9fb9c4",
            font=("Consolas", 10),
        )
        self.substatus.pack(anchor="w", padx=30, pady=(4, 0))

        self.log = scrolledtext.ScrolledText(
            self.overlay, width=52, height=10, wrap=tk.WORD,
            bg="#070b12", fg="#a7ecff", insertbackground="#a7ecff",
            relief=tk.FLAT, font=("Consolas", 10),
        )
        self.log.pack(anchor="w", padx=28, pady=(14, 0))
        self.log.insert(tk.END, "Sistema listo. Di 'Bolt' seguido de tu comando.\n")
        for tag, color in TRACE_TAGS.items():
            self.log.tag_configure(tag, foreground=color)
        self.log.configure(state=tk.DISABLED)

        self.command_frame = tk.Frame(self.overlay, bg=PALETTES["normal"]["bg"])
        self.command_frame.pack(anchor="w", padx=28, pady=(10, 0), fill=tk.X)

        self.entry = tk.Entry(
            self.command_frame, bg="#111827", fg="#ffffff",
            insertbackground="#ffffff", relief=tk.FLAT, font=("Consolas", 11),
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8)
        self.entry.bind("<Return>", lambda _e: self._send_text())

        self.send_button = tk.Button(
            self.command_frame, text="Enviar", command=self._send_text,
            bg="#1e3a8a", fg="#ffffff", relief=tk.FLAT,
            font=("Consolas", 10, "bold"),
        )
        self.send_button.pack(side=tk.LEFT, padx=(8, 0), ipadx=12, ipady=5)

        self.listen_button = tk.Button(
            self.command_frame, text="Escucha: OFF", command=self._toggle_listening,
            bg="#263244", fg="#ffffff", relief=tk.FLAT,
            font=("Consolas", 10, "bold"),
        )
        self.listen_button.pack(side=tk.LEFT, padx=(8, 0), ipadx=12, ipady=5)

        self.voice_button = tk.Button(
            self.command_frame,
            text="Voz: ON" if self.voice.voice_enabled else "Voz: OFF",
            command=self._toggle_voice,
            bg="#334155", fg="#ffffff", relief=tk.FLAT,
            font=("Consolas", 10, "bold"),
        )
        self.voice_button.pack(side=tk.LEFT, padx=(8, 0), ipadx=12, ipady=5)

        self.trace_button = tk.Button(
            self.command_frame, text="Detalle: ON", command=self._toggle_trace,
            bg="#334155", fg="#fb923c", relief=tk.FLAT,
            font=("Consolas", 9, "bold"),
        )
        self.trace_button.pack(side=tk.LEFT, padx=(8, 0), ipadx=12, ipady=5)

        self.bind("<Control-k>", lambda _e: self._toggle_keyboard())
        self.protocol("WM_DELETE_WINDOW", self._close)

        self.monitor.start()
        if self.voice.mic_available:
            self.after(500, self._toggle_listening)

    def _position_overlay(self, event) -> None:
        self.canvas.coords(self.overlay_id, 0, 0)
        self.canvas.itemconfigure(self.overlay_id, width=event.width)

    def _toggle_listening(self) -> None:
        if not self.voice.mic_available:
            self._append("SpeechRecognition no disponible. Usa el teclado.\n")
            return
        if self.stop_listening:
            self.stop_listening(wait_for_stop=False)
            self.stop_listening = None
            self.listen_button.configure(text="Escucha: OFF", bg="#263244")
            self._append("Escucha desactivada.\n")
            return
        self.voice.calibrate_mic()
        self.stop_listening = self.voice.listen_in_background(self._voice_callback)
        if self.stop_listening:
            self.listen_button.configure(text="Escucha: ON", bg="#0f766e")
            self._append("Escucha activa. Di 'Bolt' + comando.\n")
        else:
            self._append("No se pudo activar el micrófono.\n")

    def _voice_callback(self, recognizer, audio) -> None:
        try:
            text = recognizer.recognize_google(audio, language="es-MX").lower().strip()
        except Exception:
            return
        if "bolt" not in text:
            return
        command = re.sub(r"\bbolt\b", "", text, flags=re.IGNORECASE).strip(" ,.:;")
        if len(command) < 4:
            return
        self.after(0, self._handle_command, command, True)

    def _send_text(self) -> None:
        command = self.entry.get().strip()
        self.entry.delete(0, tk.END)
        if command:
            self._handle_command(command, False)

    def _handle_command(self, command: str, from_voice: bool) -> None:
        self.canvas.pulse(0.32)
        source = "Voz" if from_voice else "Texto"
        self._append(f"{source}: {command}\n")

        requested_mode = self._extract_mode(command)
        if requested_mode:
            self._set_mode(requested_mode)
            response = f"Modo {requested_mode} activado."
            self._append(f"Bolt: {response}\n")
            self.voice.speak(response)
            return

        self.send_button.configure(state=tk.DISABLED)
        threading.Thread(target=self._run_agent, args=(command,), daemon=True).start()

    def _extract_mode(self, command: str) -> str | None:
        normalized = command.lower()
        aliases = {
            "constructor": ["modo constructor", "modo construccion", "modo construir", "modo creador"],
            "investigador": ["modo investigador", "modo investigacion", "modo cientifico"],
            "sistema": ["modo sistema", "modo control", "modo pc"],
            "creativo": ["modo creativo", "modo creatividad", "modo innovador"],
            "normal": ["modo normal", "modo asistente"],
        }
        for mode, phrases in aliases.items():
            if any(phrase in normalized for phrase in phrases):
                return mode
        return None

    def _set_mode(self, mode: str) -> None:
        if not self.agent.set_mode(mode):
            return
        self.mode = mode
        palette = PALETTES[mode]
        self.configure(bg=palette["bg"])
        self.canvas.set_mode(mode)
        self.overlay.configure(bg=palette["bg"])
        self.command_frame.configure(bg=palette["bg"])
        self.status.configure(bg=palette["bg"], fg=palette["accent"], text=f"BOLT {mode.upper()}")
        self.substatus.configure(
            bg=palette["bg"],
            text=f"Modo {mode} | {self.provider.name} | Ctrl+K oculta/muestra teclado",
        )
        self.canvas.pulse(0.55)

    def _run_agent(self, command: str) -> None:
        try:
            response = self.agent.run(command)
        except Exception as exc:
            response = f"[ERROR]: {exc}"
        self.after(0, self._finish_agent, response)

    def _finish_agent(self, response: str) -> None:
        clean = re.sub(r"\[(EJECUTAR|CARPETA|BUSCAR|EDITAR|CREAR_ARCHIVO|LISTAR|ABRIR_ARCHIVO|CREAR_CARPETA|LEER_ARCHIVO):\s*(.*?)\]", "", response)
        self._append(f"Bolt: {clean}\n")
        self.voice.speak(clean)
        self.canvas.pulse(0.35)
        self.send_button.configure(state=tk.NORMAL)
        self.substatus.configure(
            text=f"Modo {self.mode} | {self.provider.name} | Memoria: {self.episodic.count()} eps",
        )

    def _on_alert(self, alert) -> None:
        self.after(0, self._append, f"\n[ALERTA]: {alert.message}\n\n")

    def _append(self, text: str) -> None:
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, text)
        self.log.configure(state=tk.DISABLED)
        self.log.see(tk.END)

    def _toggle_trace(self) -> None:
        self.trace_visible = not self.trace_visible
        self.trace_button.configure(text="Detalle: ON" if self.trace_visible else "Detalle: OFF")

    def _on_trace_event(self, event: dict) -> None:
        self.trace_logger.log(event.get("type", "info"), event.get("payload", {}))
        if self.trace_visible:
            self.after(0, self._render_trace, event)

    def _render_trace(self, event: dict) -> None:
        etype = event.get("type", "info")
        payload = event.get("payload", {}) or {}
        tag = etype if etype in TRACE_TAGS else "info"
        ts = event.get("ts", "")
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, self._trace_line(etype, payload, ts), tag)
        self.log.configure(state=tk.DISABLED)
        self.log.see(tk.END)

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

    def _toggle_keyboard(self) -> None:
        if self.command_frame.winfo_ismapped():
            self.command_frame.pack_forget()
        else:
            self.command_frame.pack(anchor="w", padx=28, pady=(10, 0), fill=tk.X)

    def _toggle_voice(self) -> None:
        self.voice.voice_enabled = not self.voice.voice_enabled
        self.voice_button.configure(text="Voz: ON" if self.voice.voice_enabled else "Voz: OFF")

    def _close(self) -> None:
        if self.stop_listening:
            self.stop_listening(wait_for_stop=False)
        self.monitor.stop()
        self.trace_logger.close()
        self.destroy()


if __name__ == "__main__":
    BoltNeuralV12App().mainloop()
