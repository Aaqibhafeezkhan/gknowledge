"""Offline provider.

Marks the pipeline to use local, deterministic heuristics instead of a remote
model. It keeps gknowledge fully usable with no API key and no network — a core
requirement from the README ("useful offline-first where possible" and "remain
useful even when a provider is misconfigured or unavailable").

The heavy lifting lives in :mod:`gknowledge.core.heuristics`; this adapter only
satisfies the interface and provides a plain-text completion for the chat path.
"""

from __future__ import annotations

from .base import LLMMessage, LLMProvider, LLMResponse


class OfflineProvider(LLMProvider):
    kind = "offline"
    name = "Offline (local heuristics)"

    def available(self) -> bool:
        return True

    def complete(
        self,
        messages: list[LLMMessage],
        *,
        json_object: bool = False,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        # The offline pipeline never routes structured extraction here; this is
        # only reached for the chat/answer path, and the query module composes
        # an extractive answer itself. Echo the user's question for safety.
        last_user = next(
            (m.content for m in reversed(messages) if m.role == "user"), ""
        )
        return LLMResponse(content=last_user, model="offline")
