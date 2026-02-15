from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol, Sequence


@dataclass(frozen=True)
class GenerationParams:
    max_tokens: int = 256
    temperature: float = 0.7
    top_p: float = 0.95


class ChatMessageLike(Protocol):
    role: str
    content: str | None


class LLMEngine:
    """Minimal interface the API layer relies on."""

    model_id: str

    def generate(self, prompt: str, params: GenerationParams) -> str:
        raise NotImplementedError

    def stream_generate(self, prompt: str, params: GenerationParams) -> Iterable[str]:
        """Yield incremental text chunks (already decoded)."""
        raise NotImplementedError

    # Optional chat-friendly helpers.
    def generate_chat(self, messages: Sequence[ChatMessageLike], params: GenerationParams) -> str:
        prompt = "\n".join(
            f"{m.role}: {m.content}" for m in messages if getattr(m, "content", None) is not None
        ) + "\nassistant:"
        return self.generate(prompt, params)

    def stream_generate_chat(
        self, messages: Sequence[ChatMessageLike], params: GenerationParams
    ) -> Iterable[str]:
        prompt = "\n".join(
            f"{m.role}: {m.content}" for m in messages if getattr(m, "content", None) is not None
        ) + "\nassistant:"
        return self.stream_generate(prompt, params)
