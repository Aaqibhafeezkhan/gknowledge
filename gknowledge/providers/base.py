"""Provider interface shared by every LLM adapter."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


class ProviderError(RuntimeError):
    """Raised when a provider cannot fulfil a request (network, auth, quota)."""


@dataclass
class LLMMessage:
    role: str          # "system" | "user" | "assistant"
    content: str


@dataclass
class LLMResponse:
    content: str
    model: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    raw: dict = field(default_factory=dict)


class LLMProvider(ABC):
    #: "offline" adapters are driven by local heuristics; "llm" adapters make
    #: real completion calls. Pipelines use this to decide whether to attempt a
    #: network call at all, and whether a heuristic fallback is appropriate.
    kind: str = "llm"
    name: str = "provider"

    @abstractmethod
    def available(self) -> bool:
        """Whether the provider is configured well enough to be used."""

    @abstractmethod
    def complete(
        self,
        messages: list[LLMMessage],
        *,
        json_object: bool = False,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Return a single completion for the given chat messages."""
