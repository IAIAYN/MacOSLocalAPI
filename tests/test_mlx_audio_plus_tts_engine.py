from __future__ import annotations

from pathlib import Path

import pytest


def test_mlx_audio_plus_engine_calls_generate_audio(monkeypatch, tmp_path: Path):
    # Import lazily to allow running tests even if mlx_audio isn't installed.
    from app.engine.mlx_audio_plus_tts import MLXAudioPlusTTSEngine

    calls = {}

    def fake_generate_audio(*, text, model, ref_audio=None, source_audio=None, ref_text=None, instruct_text=None, file_prefix, audio_format="wav", join_audio=False, verbose=True, **kw):
        calls["text"] = text
        calls["model"] = model
        calls["ref_audio"] = ref_audio
        calls["source_audio"] = source_audio
        calls["ref_text"] = ref_text
        calls["instruct_text"] = instruct_text
        calls["file_prefix"] = file_prefix
        calls["audio_format"] = audio_format
        calls["join_audio"] = join_audio
        calls["verbose"] = verbose

        # join_audio=True -> write single output file
        out = Path(f"{file_prefix}.{audio_format}")
        out.write_bytes(b"RIFF....WAVE")

    # Patch the underlying import target function
    import importlib

    try:
        gen_mod = importlib.import_module("mlx_audio.tts.generate")
    except Exception:
        pytest.skip("mlx_audio not importable in this environment")

    monkeypatch.setattr(gen_mod, "generate_audio", fake_generate_audio, raising=True)

    engine = MLXAudioPlusTTSEngine(model_id="local-audio", model_path="mlx-community/fake")
    audio = engine.synthesize("hello", params=None, format="wav", ref_text="x")  # type: ignore[arg-type]

    assert audio.startswith(b"RIFF")
    assert calls["text"] == "hello"
    assert calls["model"] == "mlx-community/fake"
    assert calls["audio_format"] == "wav"
    assert calls["join_audio"] is True
    assert calls["verbose"] is False


def test_mlx_audio_plus_engine_picks_numbered_output(monkeypatch, tmp_path: Path):
    # With join_audio=True, numbered outputs shouldn't matter, but keep fallback behavior.
    from app.engine.mlx_audio_plus_tts import MLXAudioPlusTTSEngine

    def fake_generate_audio(*, file_prefix, audio_format="wav", join_audio=False, **kwargs):
        parent = Path(file_prefix).parent
        if join_audio:
            (parent / f"speech.{audio_format}").write_bytes(b"JOINED")
        else:
            (parent / f"speech_000.{audio_format}").write_bytes(b"FIRST")
            (parent / f"speech_001.{audio_format}").write_bytes(b"SECOND")

    import importlib

    try:
        gen_mod = importlib.import_module("mlx_audio.tts.generate")
    except Exception:
        pytest.skip("mlx_audio not importable in this environment")

    monkeypatch.setattr(gen_mod, "generate_audio", fake_generate_audio, raising=True)

    engine = MLXAudioPlusTTSEngine(model_id="local-audio", model_path="mlx-community/fake")
    audio = engine.synthesize("hello", params=None, format="wav")  # type: ignore[arg-type]
    assert audio == b"JOINED"
