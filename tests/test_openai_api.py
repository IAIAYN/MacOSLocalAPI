from fastapi.testclient import TestClient

from app.app_factory import create_app
from app.config import Settings


def test_list_models():
    app = create_app(Settings(echo_mode=True, chat_model_id="local-chat"))
    client = TestClient(app)
    r = client.get("/v1/models")
    assert r.status_code == 200
    data = r.json()
    assert data["object"] == "list"
    # At least the chat model should be visible.
    ids = [m["id"] for m in data["data"]]
    assert "local-chat" in ids


def test_chat_completions_non_stream():
    app = create_app(Settings(echo_mode=True, chat_model_id="local-chat"))
    client = TestClient(app)
    r = client.post(
        "/v1/chat/completions",
        json={
            "model": "local-chat",
            "messages": [{"role": "user", "content": "hi"}],
            "stream": False,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["object"] == "chat.completion"
    assert data["choices"][0]["message"]["role"] == "assistant"
    content = data["choices"][0]["message"]["content"] or ""
    assert "hi" in content


def test_chat_completions_stream():
    app = create_app(Settings(echo_mode=True, chat_model_id="local-chat"))
    client = TestClient(app)
    with client.stream(
        "POST",
        "/v1/chat/completions",
        json={
            "model": "local-chat",
            "messages": [{"role": "user", "content": "hi"}],
            "stream": True,
        },
    ) as r:
        assert r.status_code == 200
        body = b"".join(list(r.iter_bytes()))
    assert b"data: [DONE]" in body
