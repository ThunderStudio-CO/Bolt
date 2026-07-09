from __future__ import annotations

import json
import urllib.error
import urllib.request
from abc import ABC, abstractmethod

from google import genai
from google.genai import types

from .config import BoltConfig


class ModelProvider(ABC):
    name: str

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        raise NotImplementedError


class OllamaProvider(ModelProvider):
    name = "ollama"

    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    def is_available(self) -> bool:
        try:
            with urllib.request.urlopen(f"{self.base_url}/api/tags", timeout=3) as response:
                return response.status == 200
        except Exception:
            return False

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
        }
        request = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=45) as response:
            data = json.loads(response.read().decode("utf-8"))
        return data.get("message", {}).get("content", "")


class GeminiProvider(ModelProvider):
    name = "gemini"

    def __init__(self, api_key: str, model: str) -> None:
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config=types.GenerateContentConfig(system_instruction=system_prompt),
        )
        return response.text or ""


class EchoProvider(ModelProvider):
    name = "echo"

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        return (
            "No tengo un modelo conectado todavía. "
            "Configura Ollama local o GEMINI_API_KEY en .env para activar el cerebro completo."
        )


def build_model_provider(config: BoltConfig) -> ModelProvider:
    if config.model_provider == "ollama":
        return OllamaProvider(config.ollama_base_url, config.local_model)

    if config.model_provider == "gemini":
        if not config.gemini_api_key:
            return EchoProvider()
        return GeminiProvider(config.gemini_api_key, config.gemini_model)

    local = OllamaProvider(config.ollama_base_url, config.local_model)
    if local.is_available():
        return local

    if config.gemini_api_key:
        return GeminiProvider(config.gemini_api_key, config.gemini_model)

    return EchoProvider()
