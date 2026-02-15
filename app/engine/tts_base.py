from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TTSParams:
    # OpenAI supports: input, voice, format, speed. We'll keep minimal.
    voice: str = "default"
    speed: float = 1.0
    speaker_id: int | None = None


class TTSEngine:
    model_id: str

    def synthesize(self, text: str, params: TTSParams, *, format: str = "wav", **kwargs) -> bytes:
        """Return audio bytes in the requested format (e.g. wav).

        Implementations may accept additional backend-specific kwargs.
        """
        raise NotImplementedError
