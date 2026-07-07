"""OpenAI-compatible HTTP provider.

Works with the OpenAI API and any endpoint that speaks the same
``/chat/completions`` contract (Ollama, LM Studio, vLLM, OpenRouter, Together,
Groq, ...). Uses only the standard library so the app has no hard runtime
dependency on a vendor SDK.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from .base import LLMMessage, LLMProvider, LLMResponse, ProviderError

_TIMEOUT = 900  # long ingests should not fail prematurely (README requirement)


class OpenAICompatibleProvider(LLMProvider):
    kind = "llm"

    def __init__(
        self,
        base_url: str = "https://api.openai.com/v1",
        api_key: str = "",
        model: str = "gpt-4o-mini",
        embed_model: str = "",
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.embed_model = embed_model
        self.name = f"OpenAI-compatible ({model})"

    def available(self) -> bool:
        # Local endpoints (Ollama etc.) legitimately need no key.
        return bool(self.base_url)

    def _post(self, path: str, payload: dict) -> dict:
        url = f"{self.base_url}{path}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        if self.api_key:
            req.add_header("Authorization", f"Bearer {self.api_key}")
        try:
            with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:  # pragma: no cover - network
            body = exc.read().decode("utf-8", "replace")
            raise ProviderError(f"HTTP {exc.code}: {body[:400]}") from exc
        except urllib.error.URLError as exc:  # pragma: no cover - network
            raise ProviderError(f"Connection failed: {exc.reason}") from exc

    def complete(
        self,
        messages: list[LLMMessage],
        *,
        json_object: bool = False,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        payload: dict = {
            "model": self.model,
            "temperature": temperature,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        if json_object:
            payload["response_format"] = {"type": "json_object"}
        if max_tokens:
            payload["max_tokens"] = max_tokens
        data = self._post("/chat/completions", payload)
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise ProviderError(f"Unexpected response shape: {data}") from exc
        usage = data.get("usage", {})
        return LLMResponse(
            content=content or "",
            model=data.get("model", self.model),
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            raw=data,
        )
