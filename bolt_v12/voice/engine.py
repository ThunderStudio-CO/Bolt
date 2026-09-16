from __future__ import annotations

import os
import re
import time
import asyncio
import threading
from pathlib import Path

try:
    import edge_tts
except ImportError:
    edge_tts = None

try:
    import speech_recognition as sr
except ImportError:
    sr = None


class VoiceEngine:
    def __init__(self) -> None:
        self.voice_enabled = edge_tts is not None
        self.recognizer = sr.Recognizer() if sr else None
        self.microphone = None
        self._speaking = False

    @property
    def mic_available(self) -> bool:
        return sr is not None

    def calibrate_mic(self) -> bool:
        if not self.mic_available:
            return False
        try:
            self.microphone = sr.Microphone()
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            return True
        except Exception:
            return False

    def listen_once(self, timeout: int = 5, phrase_limit: int = 15) -> str | None:
        if not self.mic_available or not self.microphone:
            return None
        try:
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
            return self.recognizer.recognize_google(audio, language="es-MX")
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except Exception:
            return None

    def listen_in_background(self, callback) -> callable | None:
        if not self.mic_available:
            return None
        try:
            self.microphone = sr.Microphone()
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            return self.recognizer.listen_in_background(self.microphone, callback)
        except Exception:
            return None

    def speak(self, text: str, voice: str = "es-MX-JorgeNeural") -> None:
        if not self.voice_enabled or not text.strip():
            return
        clean = self._clean_for_voice(text)
        if not clean:
            return
        threading.Thread(target=self._speak_worker, args=(clean, voice), daemon=True).start()

    def _clean_for_voice(self, text: str) -> str:
        text = re.sub(r"`([^`]*)`", r"\1", text)
        text = re.sub(r"https?://\S+", "un enlace", text)
        text = re.sub(r"[A-Z]:\\[^\n]+", "una ruta local", text)
        text = re.sub(r"\[.*?\]", "", text)
        return text.strip()[:900]

    def _speak_worker(self, text: str, voice: str) -> None:
        self._speaking = True
        audio_path = Path.cwd() / f"bolt_audio_{int(time.time() * 1000)}.mp3"
        alias = f"bolt_voice_{int(time.time() * 1000)}"
        try:
            asyncio.run(edge_tts.Communicate(text, voice).save(str(audio_path)))
            import ctypes
            ctypes.windll.winmm.mciSendStringW(
                f'open "{audio_path}" type mpegvideo alias {alias}', None, 0, None
            )
            ctypes.windll.winmm.mciSendStringW(f"play {alias} wait", None, 0, None)
            ctypes.windll.winmm.mciSendStringW(f"close {alias}", None, 0, None)
        except Exception:
            pass
        finally:
            self._speaking = False
            try:
                if audio_path.exists():
                    os.remove(audio_path)
            except OSError:
                pass
