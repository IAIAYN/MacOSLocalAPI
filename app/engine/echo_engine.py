from __future__ import annotations

from collections.abc import Iterable
from typing import Sequence

from .base import ChatMessageLike, GenerationParams, LLMEngine


class EchoEngine(LLMEngine):
    def __init__(self, model_id: str = "local-echo") -> None:
        self.model_id = model_id

    def generate(self, prompt: str, params: GenerationParams) -> str:
        return f"[echo]\n{prompt}"

    def stream_generate(self, prompt: str, params: GenerationParams) -> Iterable[str]:
        text = self.generate(prompt, params)
        for i in range(0, len(text), 32):
            yield text[i : i + 32]

    def generate_chat(self, messages: Sequence[ChatMessageLike], params: GenerationParams) -> str:
        # Echo only the last user message for readability.
        last_user = next((m.content for m in reversed(messages) if m.role == "user"), "")
        return f"[echo-chat] {last_user}"

    def stream_generate_chat(
        self, messages: Sequence[ChatMessageLike], params: GenerationParams
    ) -> Iterable[str]:
        text = self.generate_chat(messages, params)
        for i in range(0, len(text), 32):
            yield text[i : i + 32]
