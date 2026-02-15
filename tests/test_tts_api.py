from __future__ import annotations

from fastapi.testclient import TestClient

from app.app_factory import create_app
from app.config import Settings


def test_audio_speech_route_exists():
    app = create_app(Settings(echo_mode=True, chat_model_id="local-chat", audio_model_id="local-audio"))
    client = TestClient(app)

    r = client.get("/v1/models")
    assert r.status_code == 200

    resp = client.post(
        "/v1/audio/speech",
        json={"model": "local-audio", "input": "hello", "format": "wav"},
    )

    assert resp.status_code in (200, 404)
    if resp.status_code == 200:
        assert resp.headers["content-type"].startswith("audio/")
        assert len(resp.content) > 100


def test_audio_speech_ref_audio_required_returns_400(monkeypatch):
    from app.app_factory import create_app

    app = create_app()

    class DummyEngine:
        model_id = "local-audio"

        def synthesize(self, text, params, *, format="wav", **kwargs):  # noqa: ANN001
            raise ValueError("ref_audio is required for this model")

    # Replace registry tts engine
    app.state.registry.tts_models["local-audio"] = DummyEngine()  # type: ignore[attr-defined]

    client = TestClient(app)
    r = client.post(
        "/v1/audio/speech",
        json={"model": "local-audio", "input": "hi", "format": "wav"},
    )

    assert r.status_code == 400
    assert "ref_audio" in r.text


def test_audio_speech_ref_audio_required_wrapped_still_returns_400():
    app = create_app()

    class DummyEngine:
        model_id = "local-audio"

        def synthesize(self, text, params, *, format="wav", **kwargs):  # noqa: ANN001
            raise RuntimeError("ref_audio is required for model")

    app.state.registry.tts_models["local-audio"] = DummyEngine()  # type: ignore[attr-defined]

    client = TestClient(app)
    r = client.post(
        "/v1/audio/speech",
        json={"model": "local-audio", "input": "hi", "format": "wav"},
    )

    assert r.status_code == 400
    assert "ref_audio" in r.text


def test_audio_speech_uses_default_ref_audio_from_settings(tmp_path):
    ref = tmp_path / "ref.wav"
    ref.write_bytes(b"RIFF....WAVE")

    app = create_app(
        Settings(
            **{
                "echo_mode": True,
                "chat_model_id": "local-chat",
                "audio_model_id": "local-audio",
                "audio_ref_audio": str(ref),
            }
        )
    )

    called = {}

    class DummyEngine:
        model_id = "local-audio"

        def synthesize(self, text, params, *, format="wav", **kwargs):  # noqa: ANN001
            called["ref_audio"] = kwargs.get("ref_audio")
            return b"RIFF....WAVE"

    app.state.registry.tts_models["local-audio"] = DummyEngine()  # type: ignore[attr-defined]

    client = TestClient(app)
    r = client.post(
        "/v1/audio/speech",
        json={"model": "local-audio", "input": "hi", "format": "wav"},
    )

    assert r.status_code == 200
    assert called.get("ref_audio") == str(ref)
