from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class Settings(BaseModel):
    """Runtime configuration.

    Chat and Audio (TTS) models are configured independently so the same service
    can serve multiple models concurrently.
    """

    model_config = ConfigDict(extra="allow")

    host: str = "127.0.0.1"
    port: int = 8000

    # --- Chat model ---
    chat_model_id: str = "local-chat"
    chat_model_path: str | None = None

    # --- Audio model (TTS) ---
    audio_model_id: str = "local-audio"
    audio_model_path: str | None = None

    # Choose which TTS backend to use.
    # - "auto": if AUDIO_MODEL_PATH set -> piper, else -> macos-say
    # - "macos-say": always use macOS `say`
    # - "piper": use Piper ONNX model (requires AUDIO_MODEL_PATH)
    # - "mlx-audio-plus": use `mlx-audio-plus` (CosyVoice2/3, Chatterbox, etc.) (requires AUDIO_MODEL_PATH)
    # - "cosyvoice": alias of "mlx-audio-plus"
    audio_backend: str = "auto"

    # If true, we don't try to use real MLX generation and just echo (chat only).
    echo_mode: bool = False

    # --- Defaults for MLX TTS backends (e.g. CosyVoice) ---
    audio_ref_audio: str | None = None
    audio_ref_text: str | None = None
    audio_instruct_text: str | None = None
    audio_source_audio: str | None = None


def get_settings() -> Settings:
    import os

    def _get_bool(name: str, default: bool) -> bool:
        v = os.getenv(name)
        if v is None:
            return default
        return v.strip().lower() in {"1", "true", "yes", "y", "on"}

    # Backward-compat: MODEL_ID/MODEL_PATH map to chat model.
    legacy_model_id = os.getenv("MODEL_ID")
    legacy_model_path = os.getenv("MODEL_PATH")

    return Settings(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8000")),
        chat_model_id=os.getenv("CHAT_MODEL_ID", legacy_model_id or "local-chat"),
        chat_model_path=os.getenv("CHAT_MODEL_PATH", legacy_model_path),
        audio_model_id=os.getenv("AUDIO_MODEL_ID", "local-audio"),
        audio_model_path=os.getenv("AUDIO_MODEL_PATH"),
        audio_backend=os.getenv("AUDIO_BACKEND", "auto"),
        audio_ref_audio=os.getenv("AUDIO_REF_AUDIO"),
        audio_ref_text=os.getenv("AUDIO_REF_TEXT"),
        audio_instruct_text=os.getenv("AUDIO_INSTRUCT_TEXT"),
        audio_source_audio=os.getenv("AUDIO_SOURCE_AUDIO"),
        echo_mode=_get_bool("ECHO_MODE", False),
    )
