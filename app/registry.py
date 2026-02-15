from __future__ import annotations

from dataclasses import dataclass

from .engine.base import LLMEngine
from .engine.tts_base import TTSEngine


@dataclass
class ModelRegistry:
    chat_models: dict[str, LLMEngine]
    tts_models: dict[str, TTSEngine]

    def list_model_ids(self) -> list[str]:
        # OpenAI /v1/models is a flat list.
        ids = set(self.chat_models.keys()) | set(self.tts_models.keys())
        return sorted(ids)

    def get_chat(self, model_id: str) -> LLMEngine:
        try:
            return self.chat_models[model_id]
        except KeyError:
            raise KeyError(f"Unknown chat model: {model_id}")

    def get_tts(self, model_id: str) -> TTSEngine:
        try:
            return self.tts_models[model_id]
        except KeyError:
            raise KeyError(f"Unknown tts model: {model_id}")

