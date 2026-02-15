from __future__ import annotations

from pathlib import Path

from .tts_base import TTSParams, TTSEngine


class CosyVoiceTTSEngine(TTSEngine):
    """Placeholder adapter for CosyVoice2/3 local models.

    This project supports selecting the CosyVoice backend via:
      AUDIO_BACKEND=cosyvoice
      AUDIO_MODEL_PATH=/path/to/cosyvoice/model

    CosyVoice2/3 Python APIs and model layouts vary by upstream repo/releases.
    To avoid pinning a potentially heavy dependency set into this template repo,
    this adapter is implemented as a thin integration point:

    - It validates the model path exists.
    - It raises a clear error explaining how to install the required backend.

    If you can share the exact CosyVoice2/3 package/repo you use (pip name) and
    expected directory structure, we can wire it up to real inference.
    """

    def __init__(self, model_id: str, model_path: str) -> None:
        self.model_id = model_id
        p = Path(model_path).expanduser()
        if not p.exists():
            raise FileNotFoundError(f"AUDIO_MODEL_PATH not found: {p}")
        self._model_path = p

    def synthesize(self, text: str, params: TTSParams, *, format: str = "wav") -> bytes:
        raise RuntimeError(
            "CosyVoice backend is not wired to inference yet. "
            "Please provide the CosyVoice2/3 python package name (or repo) and model layout. "
            "Then we can implement real loading/generation under app/engine/cosyvoice_tts.py."
        )

