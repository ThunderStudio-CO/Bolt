from __future__ import annotations

import threading
import tkinter as tk
from tkinter import scrolledtext

from bolt_v11.agent import BoltAgent
from bolt_v11.config import load_config
from bolt_v11.models import build_model_provider


class BoltV11App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.config_data = load_config()
        self.provider = build_model_provider(self.config_data)
        self.agent = BoltAgent(self.config_data, self.provider)

        self.title(f"Bolt V11 - Agente ({self.provider.name})")
        self.geometry("920x680")
        self.configure(bg="#0d0d12")

        self.chat = scrolledtext.ScrolledText(
            self,
            wrap=tk.WORD,
            bg="#15151e",
            fg="#00e5ff",
            insertbackground="#00e5ff",
            font=("Consolas", 12),
        )
        self.chat.pack(fill=tk.BOTH, expand=True, padx=16, pady=(16, 8))
        self.chat.insert(tk.END, f"SISTEMA: Bolt V11 en linea. Proveedor activo: {self.provider.name}\n\n")
        self.chat.configure(state=tk.DISABLED)

        bottom = tk.Frame(self, bg="#0d0d12")
        bottom.pack(fill=tk.X, padx=16, pady=(0, 16))

        self.entry = tk.Entry(
            bottom,
            bg="#20202b",
            fg="#ffffff",
            insertbackground="#ffffff",
            font=("Consolas", 12),
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), ipady=8)
        self.entry.bind("<Return>", lambda _event: self._send())

        self.button = tk.Button(
            bottom,
            text="EJECUTAR",
            command=self._send,
            bg="#1e3a8a",
            fg="#ffffff",
            activebackground="#00a8c6",
            activeforeground="#ffffff",
            font=("Consolas", 11, "bold"),
        )
        self.button.pack(side=tk.RIGHT, ipadx=18, ipady=5)

    def _send(self, event: tk.Event | None = None) -> None:
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
        self._append(response + "\n\n")
        self.button.configure(state=tk.NORMAL, text="EJECUTAR")
        self.entry.focus()

    def _append(self, text: str) -> None:
        self.chat.configure(state=tk.NORMAL)
        self.chat.insert(tk.END, text)
        self.chat.configure(state=tk.DISABLED)
        self.chat.see(tk.END)


if __name__ == "__main__":
    BoltV11App().mainloop()
