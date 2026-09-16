from __future__ import annotations

import math
import random
import time
import tkinter as tk
from dataclasses import dataclass


PALETTES = {
    "normal": {"bg": "#05070d", "node": "#00d5ff", "edge": "#174863", "accent": "#00e5ff"},
    "constructor": {"bg": "#080706", "node": "#ff9b21", "edge": "#5f3518", "accent": "#ffb13d"},
    "investigador": {"bg": "#05090a", "node": "#42ffae", "edge": "#1c6146", "accent": "#59ffc0"},
    "sistema": {"bg": "#080711", "node": "#b064ff", "edge": "#442b68", "accent": "#c58cff"},
    "creativo": {"bg": "#0a0508", "node": "#ff6b9d", "edge": "#5c1835", "accent": "#ff8ab5"},
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
        count = 90
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
                    base_x=x, base_y=y, x=x, y=y,
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
            for second in self.nodes[index + 1:]:
                distance = math.hypot(first.x - second.x, first.y - second.y)
                if distance <= max_distance:
                    alpha = 1 - distance / max_distance
                    color = self._mix(palette["edge"], palette["accent"], alpha * 0.45)
                    self.create_line(first.x, first.y, second.x, second.y, fill=color, width=1, tags="neural")

        for node in self.nodes:
            glow = node.radius * (1.8 + self.energy * 0.65)
            glow_color = self._mix(palette["bg"], palette["node"], 0.18)
            self.create_oval(
                node.x - glow, node.y - glow, node.x + glow, node.y + glow,
                fill=glow_color, outline="", tags="neural",
            )
            r = node.radius * (1 + self.energy * 0.12)
            self.create_oval(
                node.x - r, node.y - r, node.x + r, node.y + r,
                fill=palette["node"], outline="", tags="neural",
            )
        self.tag_raise("overlay")

    def _mix(self, color_a: str, color_b: str, factor: float) -> str:
        factor = max(0.0, min(1.0, factor))
        a = tuple(int(color_a[i:i + 2], 16) for i in (1, 3, 5))
        b = tuple(int(color_b[i:i + 2], 16) for i in (1, 3, 5))
        values = tuple(int(a[i] + (b[i] - a[i]) * factor) for i in range(3))
        return f"#{values[0]:02x}{values[1]:02x}{values[2]:02x}"
