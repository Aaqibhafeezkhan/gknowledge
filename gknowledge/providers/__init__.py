"""LLM provider adapters.

The application is provider-agnostic at its boundary: the ingestion and query
pipelines depend only on the :class:`LLMProvider` interface. Concrete adapters
(offline heuristics, OpenAI-compatible HTTP endpoints, ...) are selected from
project settings at runtime.
"""

from __future__ import annotations

from .base import LLMMessage, LLMProvider, LLMResponse, ProviderError
from .offline import OfflineProvider
from .openai_compatible import OpenAICompatibleProvider


def build_provider(settings: dict) -> LLMProvider:
    """Construct a provider from a settings dict (see core.project.Settings)."""
    kind = (settings or {}).get("provider", "offline")
    if kind in ("offline", "", None):
        return OfflineProvider()
    if kind in ("openai", "openai_compatible", "custom", "ollama"):
        return OpenAICompatibleProvider(
            base_url=settings.get("base_url", "https://api.openai.com/v1"),
            api_key=settings.get("api_key", ""),
            model=settings.get("model", "gpt-4o-mini"),
            embed_model=settings.get("embed_model", ""),
        )
    return OfflineProvider()


__all__ = [
    "LLMMessage",
    "LLMProvider",
    "LLMResponse",
    "ProviderError",
    "OfflineProvider",
    "OpenAICompatibleProvider",
    "build_provider",
]
