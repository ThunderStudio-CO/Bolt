from __future__ import annotations

import math
import random
import re
import threading
import time
import tkinter as tk
import asyncio
import ctypes
import os
from dataclasses import dataclass
from pathlib import Path
from tkinter import scrolledtext

from bolt_v11.agent import BoltAgent
from bolt_v11.config import load_config
from bolt_v11.models import build_model_provider

try:
    import speech_recognition as sr
except Exception:  # pragma: no cover - optional runtime dependency
    sr = None

try:
    import edge_tts
except Exception:  # pragma: no cover - optional runtime dependency
    edge_tts = None


PALETTES = {
    "normal": {"bg": "#05070d", "node": "#00d5ff", "edge": "#174863", "accent": "#00e5ff"},
    "constructor": {"bg": "#080706", "node": "#ff9b21", "edge": "#5f3518", "accent": "#ffb13d"},
    "investigador": {"bg": "#05090a", "node": "#42ffae", "edge": "#1c6146", "accent": "#59ffc0"},
    "sistema": {"bg": "#080711", "node": "#b064ff", "edge": "#442b68", "accent": "#c58cff"},
    "listening": {"bg": "#05070d", "node": "#ffffff", "edge": "#2f5b72", "accent": "#ffffff"},
}


@dataclass
class NeuralNode:
    base_x: float
    base_y: float
    x: float
    y: float
    radius: float
    phase: float


class NeuralCanvas(tk.Canvas):
    def __init__(self, master: tk.Misc, **kwargs) -> None:
        super().__init__(master, highlightthickness=0, **kwargs)
        self.nodes: list[NeuralNode] = []
        self.mode = "normal"
        self.energy = 0.22
        self.last_size = (0, 0)
        self.after(120, self._seed)
        self.after(33, self._tick)

    def set_mode(self, mode: str) -> None:
        self.mode = mode if mode in PALETTES else "normal"
        self.configure(bg=PALETTES[self.mode]["bg"])

    def pulse(self, amount: float = 1.0) -> None:
        self.energy = min(0.85, self.energy + amount)

    def _seed(self) -> None:
        width = max(self.winfo_width(), 640)
        height = max(self.winfo_height(), 420)
        self.last_size = (width, height)
        count = 78
        self.nodes = []
        attempts = 0
        while len(self.nodes) < count and attempts < count * 30:
            attempts += 1
            x = random.uniform(width * 0.16, width * 0.84)
            y = random.uniform(height * 0.16, height * 0.78)
            nx = (x - width * 0.5) / (width * 0.31)
            ny = (y - height * 0.43) / (height * 0.29)
            left_lobe = ((x - width * 0.39) / (width * 0.22)) ** 2 + ((y - height * 0.4) / (height * 0.28)) ** 2 < 1
            right_lobe = ((x - width * 0.58) / (width * 0.25)) ** 2 + ((y - height * 0.41) / (height * 0.31)) ** 2 < 1
            lower_tail = abs(nx) < 0.38 and 0.15 < ny < 1.1 and random.random() < 0.45
            if not (left_lobe or right_lobe or lower_tail):
                continue
            self.nodes.append(
                NeuralNode(
                    base_x=x,
                    base_y=y,
                    x=x,
                    y=y,
                    radius=random.uniform(2.8, 5.2),
                    phase=random.uniform(0, math.tau),
                )
            )

    def _tick(self) -> None:
        if not self.nodes:
            self._seed()
        self._draw()
        self.energy = max(0.25, self.energy * 0.965)
        self.after(33, self._tick)

    def _draw(self) -> None:
        width = max(self.winfo_width(), 1)
        height = max(self.winfo_height(), 1)
        if abs(width - self.last_size[0]) > 140 or abs(height - self.last_size[1]) > 100:
            self._seed()
        palette = PALETTES.get(self.mode, PALETTES["normal"])
        self.delete("neural")
        self.configure(bg=palette["bg"])

        now = time.time()

        for node in self.nodes:
            drift = 2.2 + self.energy * 3.2
            node.x = node.base_x + math.sin(now * 0.32 + node.phase) * drift
            node.y = node.base_y + math.cos(now * 0.27 + node.phase) * drift

        max_distance = 104 + self.energy * 18
        for index, first in enumerate(self.nodes):
            for second in self.nodes[index + 1 :]:
                distance = math.hypot(first.x - second.x, first.y - second.y)
                if distance <= max_distance:
                    alpha = 1 - distance / max_distance
                    color = self._mix(palette["edge"], palette["accent"], alpha * 0.45)
                    self.create_line(first.x, first.y, second.x, second.y, fill=color, width=1, tags="neural")

        for node in self.nodes:
            glow = node.radius * (1.8 + self.energy * 0.65)
            glow_color = self._mix(palette["bg"], palette["node"], 0.18)
            self.create_oval(
                node.x - glow,
                node.y - glow,
                node.x + glow,
                node.y + glow,
                fill=glow_color,
                outline="",
                tags="neural",
            )
            r = node.radius * (1 + self.energy * 0.12)
            self.create_oval(
                node.x - r,
                node.y - r,
                node.x + r,
                node.y + r,
                fill=palette["node"],
                outline="",
                tags="neural",
            )
        self.tag_raise("overlay")

    def _mix(self, color_a: str, color_b: str, factor: float) -> str:
        factor = max(0.0, min(1.0, factor))
        a = tuple(int(color_a[i : i + 2], 16) for i in (1, 3, 5))
        b = tuple(int(color_b[i : i + 2], 16) for i in (1, 3, 5))
        values = tuple(int(a[index] + (b[index] - a[index]) * factor) for index in range(3))
        return f"#{values[0]:02x}{values[1]:02x}{values[2]:02x}"


class BoltNeuralApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.config_data = load_config()
        self.provider = build_model_provider(self.config_data)
        self.agent = BoltAgent(self.config_data, self.provider)
        self.mode = "normal"
        self.stop_listening = None
        self.voice_enabled = edge_tts is not None
        self.recognizer = sr.Recognizer() if sr else None
        self.microphone = None

        self.title(f"Bolt Neural - {self.provider.name}")
        self.geometry("1000x720")
        self.minsize(760, 520)
        self.configure(bg=PALETTES["normal"]["bg"])

        self.canvas = NeuralCanvas(self, bg=PALETTES["normal"]["bg"])
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.overlay = tk.Frame(self.canvas, bg=PALETTES["normal"]["bg"])
        self.overlay_id = self.canvas.create_window(0, 0, anchor="nw", window=self.overlay, tags="overlay")
        self.canvas.bind("<Configure>", self._position_overlay)

        self.status = tk.Label(
            self.overlay,
            text="BOLT NEURAL",
            bg=PALETTES["normal"]["bg"],
            fg=PALETTES["normal"]["accent"],
            font=("Consolas", 22, "bold"),
        )
        self.status.pack(anchor="w", padx=28, pady=(24, 0))

        self.substatus = tk.Label(
            self.overlay,
            text=f"Modo normal | proveedor {self.provider.name} | di: Bolt, modo constructor",
            bg=PALETTES["normal"]["bg"],
            fg="#9fb9c4",
            font=("Consolas", 10),
        )
        self.substatus.pack(anchor="w", padx=30, pady=(4, 0))

        self.log = scrolledtext.ScrolledText(
            self.overlay,
            width=46,
            height=9,
            wrap=tk.WORD,
            bg="#070b12",
            fg="#a7ecff",
            insertbackground="#a7ecff",
            relief=tk.FLAT,
            font=("Consolas", 10),
        )
        self.log.pack(anchor="w", padx=28, pady=(18, 0))
        self.log.insert(tk.END, "Sistema listo. El teclado queda como respaldo.\n")
        self.log.configure(state=tk.DISABLED)

        self.command_frame = tk.Frame(self.overlay, bg=PALETTES["normal"]["bg"])
        self.command_frame.pack(anchor="w", padx=28, pady=(12, 0), fill=tk.X)

        self.entry = tk.Entry(
            self.command_frame,
            bg="#111827",
            fg="#ffffff",
            insertbackground="#ffffff",
            relief=tk.FLAT,
            font=("Consolas", 11),
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8)
        self.entry.bind("<Return>", lambda _event: self._send_text())

        self.send_button = tk.Button(
            self.command_frame,
            text="Enviar",
            command=self._send_text,
            bg="#1e3a8a",
            fg="#ffffff",
            relief=tk.FLAT,
            font=("Consolas", 10, "bold"),
        )
        self.send_button.pack(side=tk.LEFT, padx=(8, 0), ipadx=12, ipady=5)

        self.listen_button = tk.Button(
            self.command_frame,
            text="Escucha: OFF",
            command=self.toggle_listening,
            bg="#263244",
            fg="#ffffff",
            relief=tk.FLAT,
            font=("Consolas", 10, "bold"),
        )
        self.listen_button.pack(side=tk.LEFT, padx=(8, 0), ipadx=12, ipady=5)

        self.voice_button = tk.Button(
            self.command_frame,
            text="Voz: ON" if self.voice_enabled else "Voz: OFF",
            command=self._toggle_voice,
            bg="#334155",
            fg="#ffffff",
            relief=tk.FLAT,
            font=("Consolas", 10, "bold"),
        )
        self.voice_button.pack(side=tk.LEFT, padx=(8, 0), ipadx=12, ipady=5)

        self.bind("<Control-k>", lambda _event: self._toggle_keyboard())
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.after(500, self.toggle_listening)

    def _position_overlay(self, event: tk.Event) -> None:
        self.canvas.coords(self.overlay_id, 0, 0)
        self.canvas.itemconfigure(self.overlay_id, width=event.width)

    def toggle_listening(self) -> None:
        if not sr:
            self._append("SpeechRecognition no esta instalado. Usa el teclado o instala la dependencia.\n")
            return

        if self.stop_listening:
            self.stop_listening(wait_for_stop=False)
            self.stop_listening = None
            self.listen_button.configure(text="Escucha: OFF", bg="#263244")
            self._append("Escucha continua desactivada.\n")
            return

        try:
            self.microphone = sr.Microphone()
            self.recognizer.pause_threshold = 1.05
            self.recognizer.phrase_threshold = 0.35
            self.recognizer.non_speaking_duration = 0.45
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            self.stop_listening = self.recognizer.listen_in_background(self.microphone, self._voice_callback)
            self.listen_button.configure(text="Escucha: ON", bg="#0f766e")
            self._append("Escucha continua activa. Wake word: Bolt.\n")
            self.command_frame.pack_forget()
        except Exception as exc:
            self._append(f"No pude activar microfono: {exc}\n")

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
        if command:
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
            self._speak(response)
            return

        self.send_button.configure(state=tk.DISABLED)
        threading.Thread(target=self._run_agent, args=(command,), daemon=True).start()

    def _extract_mode(self, command: str) -> str | None:
        normalized = command.lower()
        aliases = {
            "constructor": ["modo constructor", "modo construccion", "modo construir", "modo creador"],
            "investigador": ["modo investigador", "modo investigacion", "modo científico", "modo cientifico"],
            "sistema": ["modo sistema", "modo control", "modo pc"],
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
            text=f"Modo {mode} | proveedor {self.provider.name} | Ctrl+K oculta/muestra teclado",
        )
        self.canvas.pulse(0.55)

    def _run_agent(self, command: str) -> None:
        try:
            response = self.agent.run(command)
        except Exception as exc:
            response = f"[ERROR]: {exc}"
        self.after(0, self._finish_agent, response)

    def _finish_agent(self, response: str) -> None:
        self._append(f"Bolt: {response}\n")
        self._speak(response)
        self.canvas.pulse(0.35)
        self.send_button.configure(state=tk.NORMAL)

    def _append(self, text: str) -> None:
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, text)
        self.log.configure(state=tk.DISABLED)
        self.log.see(tk.END)

    def _toggle_keyboard(self) -> None:
        if self.command_frame.winfo_ismapped():
            self.command_frame.pack_forget()
        else:
            self.command_frame.pack(anchor="w", padx=28, pady=(12, 0), fill=tk.X)

    def _toggle_voice(self) -> None:
        self.voice_enabled = not self.voice_enabled
        self.voice_button.configure(text="Voz: ON" if self.voice_enabled else "Voz: OFF")

    def _speak(self, text: str) -> None:
        if not self.voice_enabled or edge_tts is None:
            return
        clean = self._clean_for_voice(text)
        if not clean:
            return
        threading.Thread(target=self._speak_worker, args=(clean,), daemon=True).start()

    def _clean_for_voice(self, text: str) -> str:
        text = re.sub(r"`([^`]*)`", r"\1", text)
        text = re.sub(r"https?://\S+", "un enlace", text)
        text = re.sub(r"[A-Z]:\\[^\n]+", "una ruta local", text)
        return text.strip()[:900]

    def _speak_worker(self, text: str) -> None:
        audio_path = Path.cwd() / f"respuesta_bolt_{int(time.time() * 1000)}.mp3"
        alias = f"bolt_voice_{int(time.time() * 1000)}"
        try:
            asyncio.run(edge_tts.Communicate(text, "es-MX-JorgeNeural").save(str(audio_path)))
            ctypes.windll.winmm.mciSendStringW(f'open "{audio_path}" type mpegvideo alias {alias}', None, 0, None)
            ctypes.windll.winmm.mciSendStringW(f"play {alias} wait", None, 0, None)
            ctypes.windll.winmm.mciSendStringW(f"close {alias}", None, 0, None)
        except Exception as exc:
            self.after(0, self._append, f"[Voz]: No pude hablar: {exc}\n")
        finally:
            try:
                if audio_path.exists():
                    os.remove(audio_path)
            except OSError:
                pass

    def _close(self) -> None:
        if self.stop_listening:
            self.stop_listening(wait_for_stop=False)
        self.destroy()


if __name__ == "__main__":
    BoltNeuralApp().mainloop()
