from __future__ import annotations

import json
import urllib.error
import urllib.request
import uuid
from abc import ABC, abstractmethod
from typing import Generator

from .config import BoltConfig

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


class ModelProvider(ABC):
    name: str

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def generate_stream(self, system_prompt: str, user_prompt: str) -> Generator[str, None, None]:
        raise NotImplementedError


class BigPickleProvider(ModelProvider):
    name = "bigpickle"

    def __init__(self, api_key: str, model: str, base_url: str) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self._session_id = uuid.uuid4().hex
        self._project_id = uuid.uuid4().hex
        self._client = None
        if HAS_OPENAI:
            try:
                self._client = OpenAI(
                    api_key=api_key,
                    base_url=self.base_url,
                    default_headers={
                        "x-opencode-client": "cli",
                        "x-opencode-session": self._session_id,
                        "x-opencode-project": self._project_id,
                        "x-opencode-request": uuid.uuid4().hex,
                        "User-Agent": "opencode/latest/cli",
                    },
                )
            except Exception as exc:
                print(f"[BOLT]: Error inicializando Big Pickle: {exc}")

    def _request_headers(self) -> dict:
        return {
            "x-opencode-client": "cli",
            "x-opencode-session": self._session_id,
            "x-opencode-project": self._project_id,
            "x-opencode-request": uuid.uuid4().hex,
        }

    def _error_message(self, exc: Exception) -> str:
        status = getattr(exc, "status_code", None)
        if status == 403:
            return (
                f"[BigPickle Error]: Acceso denegado (HTTP 403). "
                f"Verifica tu OPENCODE_API_KEY en .env. "
                f"Obtén una en: https://opencode.ai/auth "
                f"Detalles: {exc}"
            )
        if status == 401:
            return (
                f"[BigPickle Error]: API key inválida (HTTP 401). "
                f"Regenera tu key en: https://opencode.ai/auth"
            )
        return f"[BigPickle Error]: {exc}"

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not self._client:
            return "[BigPickle]: openai no instalado. pip install openai"
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=16384,
                extra_headers=self._request_headers(),
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            return self._error_message(exc)

    def generate_stream(self, system_prompt: str, user_prompt: str) -> Generator[str, None, None]:
        if not self._client:
            yield "[BigPickle]: openai no instalado."
            return
        try:
            stream = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=16384,
                stream=True,
                extra_headers=self._request_headers(),
            )
            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                content = getattr(delta, "content", None)
                if content:
                    yield content
        except Exception as exc:
            yield self._error_message(exc)


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
        if not self.is_available():
            return "[Ollama]: No está corriendo. Ejecuta: ollama serve"
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
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                data = json.loads(response.read().decode("utf-8"))
            return data.get("message", {}).get("content", "")
        except Exception as exc:
            return f"[Ollama Error]: {exc}"

    def generate_stream(self, system_prompt: str, user_prompt: str) -> Generator[str, None, None]:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": True,
        }
        request = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=90) as response:
            for line in response:
                line = line.decode("utf-8").strip()
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                    content = chunk.get("message", {}).get("content", "")
                    if content:
                        yield content
                    if chunk.get("done"):
                        break
                except json.JSONDecodeError:
                    continue


class EchoProvider(ModelProvider):
    name = "echo"

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        return (
            "No tengo un modelo conectado. "
            "Configura GEMINI_API_KEY en .env para usar Gemini, "
            "o BOLT_MODEL_PROVIDER=ollama para usar un modelo local."
        )

    def generate_stream(self, system_prompt: str, user_prompt: str) -> Generator[str, None, None]:
        yield self.generate(system_prompt, user_prompt)


class GeminiProvider(ModelProvider):
    name = "gemini"

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model
        self._client = None
        if HAS_GENAI:
            try:
                self._client = genai.Client(api_key=api_key)
            except Exception as exc:
                print(f"[BOLT]: Error inicializando Gemini: {exc}")

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not self._client:
            return "[Gemini]: google-genai no instalado. pip install google-genai"
        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config=types.GenerateContentConfig(system_instruction=system_prompt),
            )
            return response.text or ""
        except Exception as exc:
            return f"[Gemini Error]: {exc}"

    def generate_stream(self, system_prompt: str, user_prompt: str) -> Generator[str, None, None]:
        if not self._client:
            yield "[Gemini]: google-genai no instalado."
            return
        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config=types.GenerateContentConfig(system_instruction=system_prompt),
            )
            if response.text:
                yield response.text
        except Exception as exc:
            yield f"[Gemini Error]: {exc}"


class FallbackProvider(ModelProvider):
    name = "fallback"

    def __init__(self, providers: list[ModelProvider]) -> None:
        self.providers = providers
        self._active: ModelProvider | None = None

    def _get_active(self) -> ModelProvider:
        if self._active:
            return self._active
        return self.providers[0] if self.providers else EchoProvider()

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        errors: list[str] = []
        for provider in self.providers:
            try:
                result = provider.generate(system_prompt, user_prompt)
                if result and not result.startswith("[") and "Error" not in result[:30]:
                    self._active = provider
                    self.name = provider.name
                    return result
                errors.append(f"{provider.name}: respuesta con error")
            except Exception as exc:
                errors.append(f"{provider.name}: {exc}")
                continue
        error_detail = " | ".join(errors)
        return (
            f"[BOLT]: Ningún modelo disponible.\n"
            f"Detalles: {error_detail}\n"
            f"Opciones:\n"
            f"  1. Obtén una API key válida en: https://opencode.ai/auth\n"
            f"  2. Instala y ejecuta Ollama: ollama serve\n"
            f"  3. Cambia BOLT_MODEL_PROVIDER en .env"
        )

    def generate_stream(self, system_prompt: str, user_prompt: str) -> Generator[str, None, None]:
        errors: list[str] = []
        for provider in self.providers:
            try:
                chunks = list(provider.generate_stream(system_prompt, user_prompt))
                full = "".join(chunks)
                if full and not full.startswith("[") and "Error" not in full[:30]:
                    self._active = provider
                    self.name = provider.name
                    yield from chunks
                    return
                errors.append(f"{provider.name}: respuesta con error")
            except Exception as exc:
                errors.append(f"{provider.name}: {exc}")
                continue
        yield (
            f"[BOLT]: Ningún modelo disponible.\n"
            f"Detalles: {' | '.join(errors)}"
        )


def build_model_provider(config: BoltConfig) -> ModelProvider:
    if config.model_provider == "gemini":
        if not config.gemini_api_key:
            print("[BOLT]: GEMINI_API_KEY no configurada.")
            print("[BOLT]: Configura tu key en .env")
            ollama = OllamaProvider(config.ollama_base_url, config.ollama_model)
            if ollama.is_available():
                print("[BOLT]: Usando Ollama como respaldo.")
                return ollama
            return EchoProvider()
        return GeminiProvider(api_key=config.gemini_api_key, model=config.gemini_model)

    if config.model_provider == "bigpickle":
        if not config.bigpickle_api_key:
            print("[BOLT]: OPENCODE_API_KEY no configurada.")
            print("[BOLT]: Obtén tu key en: https://opencode.ai/auth")
            ollama = OllamaProvider(config.ollama_base_url, config.ollama_model)
            if ollama.is_available():
                print("[BOLT]: Usando Ollama como respaldo.")
                return ollama
            return EchoProvider()
        return BigPickleProvider(
            api_key=config.bigpickle_api_key,
            model=config.bigpickle_model,
            base_url=config.bigpickle_base_url,
        )

    if config.model_provider == "ollama":
        provider = OllamaProvider(config.ollama_base_url, config.ollama_model)
        if provider.is_available():
            return provider
        print("[BOLT]: Ollama no disponible.")
        if config.gemini_api_key:
            print("[BOLT]: Intentando Gemini...")
            return GeminiProvider(api_key=config.gemini_api_key, model=config.gemini_model)
        if config.bigpickle_api_key:
            print("[BOLT]: Intentando Big Pickle...")
            return BigPickleProvider(
                api_key=config.bigpickle_api_key,
                model=config.bigpickle_model,
                base_url=config.bigpickle_base_url,
            )
        return EchoProvider()

    if config.model_provider == "auto":
        providers: list[ModelProvider] = []
        if config.bigpickle_api_key:
            providers.append(BigPickleProvider(
                api_key=config.bigpickle_api_key,
                model=config.bigpickle_model,
                base_url=config.bigpickle_base_url,
            ))
        if config.gemini_api_key:
            providers.append(GeminiProvider(api_key=config.gemini_api_key, model=config.gemini_model))
        ollama = OllamaProvider(config.ollama_base_url, config.ollama_model)
        providers.append(ollama)
        if len(providers) > 1:
            print("[BOLT]: Modo auto - intentando Big Pickle, Gemini, luego Ollama.")
            return FallbackProvider(providers)
        if providers:
            return providers[0]
        return EchoProvider()

    return EchoProvider()
