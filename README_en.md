<!--
  Tip: This README is optimized for GitHub rendering.
  The banner below is an inline SVG (no external assets required).
-->

<div align="center">

[中文](./README.md) | [English](./README_en.md)

<!-- Inline SVG Banner (works on GitHub) -->
<svg width="860" height="140" viewBox="0 0 860 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="MacOSLocalAPI banner">
  <defs>
    <linearGradient id="g" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0%" stop-color="#111827"/>
      <stop offset="55%" stop-color="#0b1220"/>
      <stop offset="100%" stop-color="#0f172a"/>
    </linearGradient>
    <linearGradient id="a" x1="0" x2="1" y1="0" y2="0">
      <stop offset="0%" stop-color="#22c55e"/>
      <stop offset="50%" stop-color="#60a5fa"/>
      <stop offset="100%" stop-color="#a78bfa"/>
    </linearGradient>
    <filter id="blur" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="14"/>
    </filter>
  </defs>

  <rect x="0" y="0" width="860" height="140" rx="18" fill="url(#g)"/>

  <!-- decorative blobs -->
  <circle cx="120" cy="42" r="42" fill="#22c55e" opacity="0.22" filter="url(#blur)"/>
  <circle cx="210" cy="112" r="46" fill="#60a5fa" opacity="0.20" filter="url(#blur)"/>
  <circle cx="770" cy="70" r="58" fill="#a78bfa" opacity="0.18" filter="url(#blur)"/>

  <!-- title -->
  <text x="46" y="66" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI" font-size="34" font-weight="700" fill="#e5e7eb">MacOSLocalAPI</text>
  <text x="46" y="98" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI" font-size="16" fill="#cbd5e1">FastAPI + MLX (optional mlx-lm) · OpenAI-compatible Chat & TTS · Runs locally on macOS</text>

  <!-- right tag -->
  <rect x="640" y="30" width="188" height="34" rx="10" fill="none" stroke="url(#a)" stroke-width="2"/>
  <text x="734" y="53" text-anchor="middle" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI" font-size="14" font-weight="600" fill="#e5e7eb">OpenAI-compatible</text>
</svg>

<br/>

<p>
  <img alt="Platform" src="https://img.shields.io/badge/platform-macOS-black?style=flat" />
  <img alt="API" src="https://img.shields.io/badge/API-OpenAI%20compatible-0ea5e9?style=flat" />
  <img alt="Framework" src="https://img.shields.io/badge/FastAPI-059669?style=flat" />
  <img alt="Runtime" src="https://img.shields.io/badge/uv-managed-111827?style=flat" />
  <img alt="MLX" src="https://img.shields.io/badge/MLX-local%20inference-7c3aed?style=flat" />
  <img alt="TTS" src="https://img.shields.io/badge/TTS-macOS%20say-f97316?style=flat" />
</p>

Wrap local models into an **OpenAI-style API** (Chat + TTS) on macOS, so any OpenAI-compatible client can connect.

</div>

---

## Features

- **Chat**: `POST /v1/chat/completions`
  - SSE streaming with `stream=true`
  - Uses tokenizer `apply_chat_template()` when available, with basic output cleanup
- **TTS**: `POST /v1/audio/speech`
  - Default backend: macOS `say` + `afconvert` (no extra models required)
- **Coexist multiple models**: Chat and TTS models are configured independently
  - `CHAT_MODEL_ID` / `CHAT_MODEL_PATH`
  - `AUDIO_MODEL_ID` / `AUDIO_MODEL_PATH`
- **Model listing**: `GET /v1/models`

---

## Requirements

| Item | Notes |
|---|---|
| OS | macOS (Apple Silicon recommended) |
| Python | `>= 3.11` (declared by project; uv may run newer versions) |
| Dependency manager | `uv` |

---

## Install & Run

### 1) Install deps

```bash
uv sync
```

### 2) Echo mode (recommended first)

Echo mode does not load a model. It helps validate routing and OpenAI compatibility.

```bash
ECHO_MODE=1 uv run uvicorn main:app --reload
```

Default model IDs:
- Chat: `local-chat`
- Audio: `local-audio`

### 3) Enable local MLX chat model

```bash
CHAT_MODEL_PATH=/path/to/mlx-chat-model \
uv run uvicorn main:app --reload
```

Custom external model ID:

```bash
CHAT_MODEL_ID=qwen-chat CHAT_MODEL_PATH=/path/to/mlx-chat-model \
uv run uvicorn main:app --reload
```

> `mlx-lm` is required for MLX chat generation:
>
> ```bash
> uv add mlx-lm
> ```

### 4) Enable TTS

#### 4.1 Default (macOS say)

If `AUDIO_MODEL_PATH` is not set, the service uses macOS built-in `say`.

#### 4.2 Local Piper model (ONNX)

Set `AUDIO_BACKEND=piper` and `AUDIO_MODEL_PATH` to a `.onnx` file or a folder containing exactly one `.onnx`.

#### 4.3 Unified MLX TTS via `mlx-audio-plus` (CosyVoice2/3, Chatterbox, ...)

If your TTS model is in **MLX format**, use `mlx-audio-plus` as a unified backend.

Why `ref_audio` may be required?

Many MLX TTS models are **speaker-conditioned / voice-cloning** models. They require a reference audio clip to determine the target speaker/style. This is model-dependent, not a server requirement.

If you want pure text-to-speech without reference audio:
1) Use `macos-say`
2) Use `piper`
3) Choose an MLX TTS model/mode that supports no-reference generation

Startup example (HF repo id):

```bash
AUDIO_BACKEND=mlx-audio-plus \
AUDIO_MODEL_ID=local-audio \
AUDIO_MODEL_PATH=mlx-community/Fun-CosyVoice3-0.5B-2512-4bit \
uv run uvicorn main:app --reload
```

Request example:

```bash
curl http://127.0.0.1:8000/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -d '{
    "model":"local-audio",
    "input":"Hello, this is a test.",
    "format":"wav",
    "ref_audio":"reference.wav",
    "ref_text":"This is what I said in the reference audio."
  }' \
  --output out.wav
```

Common extra fields (passed through to the backend):
- `ref_audio`: reference audio path (or base64/data URL)
- `ref_text`: transcript of the reference audio
- `instruct_text`: style/emotion instruction
- `source_audio`: voice conversion input

#### Duplicate / repeated phrases (basic mitigation)

Some MLX TTS models may occasionally generate **a repeated leading phrase** (e.g. `A + A + B`).

This service applies two low-risk mitigations:
1) Forces `join_audio=true` when calling `mlx-audio-plus`, so the library joins multi-segment outputs internally.
2) For `wav` output only, applies a conservative "repeated prefix trimming" post-process: it trims only when the very beginning contains an *immediately repeated PCM16 prefix*.

Note: this is an engineering workaround for local usability (not OpenAI official behavior). Non-`wav` formats currently skip this post-process.

---

## Configuration (Environment Variables)

| Category | Variable | Default | Notes |
|---|---|---:|---|
| Common | `HOST` | `127.0.0.1` | Bind host |
| Common | `PORT` | `8000` | Bind port |
| Chat | `CHAT_MODEL_ID` | `local-chat` | External chat model name |
| Chat | `CHAT_MODEL_PATH` | *(empty)* | Local MLX chat model path |
| Audio | `AUDIO_MODEL_ID` | `local-audio` | External TTS model name |
| Audio | `AUDIO_BACKEND` | `auto` | `auto`, `macos-say`, `piper`, `mlx-audio-plus` |
| Audio | `AUDIO_MODEL_PATH` | *(empty)* | Piper: `.onnx` file/folder. MLX: local folder or HF repo id |
| Audio | `AUDIO_REF_AUDIO` | *(empty)* | Default `ref_audio` (path or base64/data URL) used when request omits it |
| Audio | `AUDIO_REF_TEXT` | *(empty)* | Default `ref_text` (optional) |
| Audio | `AUDIO_INSTRUCT_TEXT` | *(empty)* | Default `instruct_text` (optional) |
| Audio | `AUDIO_SOURCE_AUDIO` | *(empty)* | Default `source_audio` (optional, voice conversion) |
| Compat | `MODEL_ID`/`MODEL_PATH` | *(empty)* | Legacy vars mapped to chat model config |

---

## API

### `GET /v1/models`

Lists registered model ids (chat + audio) as a flat list.

### Chat Completions

Route: `POST /v1/chat/completions`

Non-streaming:

```bash
curl http://127.0.0.1:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"local-chat","messages":[{"role":"user","content":"Hi"}],"stream":false,"max_tokens":128}'
```

Streaming SSE:

```bash
curl http://127.0.0.1:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H 'Accept: text/event-stream' \
  -d '{"model":"local-chat","messages":[{"role":"user","content":"Explain MLX in one sentence"}],"stream":true,"max_tokens":128}'
```

### Audio Speech (TTS)

Route: `POST /v1/audio/speech`

Returns raw audio bytes (not JSON):

```bash
curl http://127.0.0.1:8000/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -d '{"model":"local-audio","input":"Hello from local TTS.","voice":"Ting-Ting","format":"wav"}' \
  --output out.wav
```

---

## Project Layout

- `main.py`: Uvicorn entry
- `app/app_factory.py`: creates the FastAPI app, registers models
- `app/registry.py`: the model registry (chat/tts separated)
- `app/api/v1/openai.py`: OpenAI-style chat/models routes
- `app/api/v1/audio.py`: OpenAI-style TTS route
- `app/engine/mlx_engine.py`: MLX chat engine (via `mlx-lm`)
- `app/engine/macos_say_tts.py`: macOS `say` TTS engine
- `tests/`: pytest suite
- `test_main.http`: PyCharm HTTP Client samples

---

## Tests

```bash
uv run pytest -q
```
