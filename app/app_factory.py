from __future__ import annotations

from fastapi import FastAPI

from .config import Settings, get_settings
from .engine.echo_engine import EchoEngine
from .engine.mlx_engine import MLXEngine
from .engine.macos_say_tts import MacOSSayTTSEngine
from .engine.piper_tts import PiperTTSEngine
from .engine.mlx_audio_plus_tts import MLXAudioPlusTTSEngine
from .api.v1 import openai
from .api.v1 import audio
from .registry import ModelRegistry


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    app = FastAPI(title="MacOS Local OpenAI API", version="0.1.0")

    # --- Chat engine(s) ---
    if settings.echo_mode or not settings.chat_model_path:
        chat_engine = EchoEngine(model_id=settings.chat_model_id)
    else:
        chat_engine = MLXEngine(model_id=settings.chat_model_id, model_path=settings.chat_model_path)

    # --- Audio/TTS engine(s) ---
    tts_models = {}

    backend = (settings.audio_backend or "auto").strip().lower()
    if backend == "cosyvoice":
        backend = "mlx-audio-plus"

    if backend not in {"auto", "macos-say", "piper", "mlx-audio-plus"}:
        raise RuntimeError(f"Unknown AUDIO_BACKEND: {settings.audio_backend}")

    if backend == "auto":
        backend = "piper" if settings.audio_model_path else "macos-say"

    if backend in {"piper", "mlx-audio-plus"} and not settings.audio_model_path:
        raise RuntimeError(f"AUDIO_BACKEND={backend} requires AUDIO_MODEL_PATH")

    if backend == "piper":
        try:
            piper_engine = PiperTTSEngine(
                model_id=settings.audio_model_id, model_path=settings.audio_model_path  # type: ignore[arg-type]
            )
            tts_models[piper_engine.model_id] = piper_engine
        except Exception as e:
            raise RuntimeError(f"Failed to load Piper AUDIO_MODEL_PATH: {e}") from e

    elif backend == "mlx-audio-plus":
        try:
            mlx_audio_engine = MLXAudioPlusTTSEngine(
                model_id=settings.audio_model_id,
                model_path=settings.audio_model_path,  # type: ignore[arg-type]
            )
            tts_models[mlx_audio_engine.model_id] = mlx_audio_engine
        except Exception as e:
            raise RuntimeError(f"Failed to load MLX Audio Plus AUDIO_MODEL_PATH: {e}") from e

    else:  # macos-say
        try:
            say_engine = MacOSSayTTSEngine(model_id=settings.audio_model_id)
            tts_models[say_engine.model_id] = say_engine
        except Exception as e:
            print(f"[startup] TTS disabled: {e}")

    registry = ModelRegistry(chat_models={chat_engine.model_id: chat_engine}, tts_models=tts_models)

    app.state.settings = settings
    app.state.engine = chat_engine  # backward compat
    app.state.registry = registry

    temp_kw = getattr(chat_engine, "_temp_kw", None)
    print(
        f"[startup] chat_engine={chat_engine.__class__.__name__} chat_model_id={settings.chat_model_id} "
        f"echo_mode={settings.echo_mode} chat_model_path={settings.chat_model_path} temp_kw={temp_kw}"
    )
    print(
        f"[startup] audio_backend={settings.audio_backend} audio_model_id={settings.audio_model_id} "
        f"audio_model_path={settings.audio_model_path} tts_models={list(tts_models.keys())}"
    )

    app.include_router(openai.router, prefix="/v1")
    app.include_router(audio.router, prefix="/v1")

    @app.get("/")
    async def root():
        return {
            "status": "ok",
            "chat_model_id": settings.chat_model_id,
            "chat_model_path": settings.chat_model_path,
            "audio_backend": settings.audio_backend,
            "audio_model_id": settings.audio_model_id,
            "audio_model_path": settings.audio_model_path,
            "echo_mode": settings.echo_mode,
            "models": registry.list_model_ids(),
        }

    return app
