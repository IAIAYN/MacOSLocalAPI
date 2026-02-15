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
  <text x="46" y="98" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI" font-size="16" fill="#cbd5e1">FastAPI + MLX（可选 mlx-lm） · OpenAI 兼容 Chat & TTS · macOS 本地运行</text>

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

在 macOS 上把本地模型包装成 **OpenAI 风格 API**（Chat + TTS），方便你的应用/SDK 直接接入。

</div>

---

## ✨ 功能一览

- **Chat**：`POST /v1/chat/completions`
  - 支持 `stream=true` 的 SSE 流式输出
  - 优先使用 tokenizer 的 `apply_chat_template()`，并对输出做基础清洗（尽量只返回本轮 assistant 内容）
- **TTS**：`POST /v1/audio/speech`
  - 默认使用 macOS 自带 `say` + `afconvert`（不依赖额外大模型）
- **模型并存**：Chat 与 Audio(TTS) 模型独立配置
  - `CHAT_MODEL_ID` / `CHAT_MODEL_PATH`
  - `AUDIO_MODEL_ID` / `AUDIO_MODEL_PATH`

---

## 📌 目录

- [环境要求](#-环境要求)
- [安装与运行](#-安装与运行)
- [配置（环境变量）](#-配置环境变量)
- [接口](#-接口)
  - [Chat Completions](#chat-completions)
  - [Audio Speech (TTS)](#audio-speech-tts)
- [SDK 使用示例](#-sdk-使用示例)
- [项目结构](#-项目结构)
- [FAQ](#-faq)

---

## 🧩 环境要求

| 项目 | 说明 |
|---|---|
| OS | macOS（Apple Silicon 推荐） |
| Python | `>= 3.11`（项目声明；uv 也可能使用更高版本运行） |
| 依赖管理 | `uv` |

---

## 🚀 安装与运行

### 1) 安装依赖

```bash
uv sync
```

### 2) Echo 模式（推荐先跑通）

Echo 模式不加载模型，主要用于验证路由与 OpenAI 客户端兼容性。

```bash
ECHO_MODE=1 uv run uvicorn main:app --reload
```

默认模型名：
- Chat：`local-chat`
- Audio：`local-audio`

### 3) 启用本地 MLX Chat 模型

```bash
CHAT_MODEL_PATH=/path/to/mlx-chat-model \
uv run uvicorn main:app --reload
```

自定义对外模型名：

```bash
CHAT_MODEL_ID=qwen-chat CHAT_MODEL_PATH=/path/to/mlx-chat-model \
uv run uvicorn main:app --reload
```

> 需要 `mlx-lm` 才能加载/生成：
>
> ```bash
> uv add mlx-lm
> ```

### 4) 启用 TTS

#### 4.1 默认（macOS say）

不设置 `AUDIO_MODEL_PATH` 时，默认使用 macOS 自带 `say` + `afconvert`。

#### 4.2 使用本地 Piper 模型（AUDIO_MODEL_PATH）

本项目支持通过 `AUDIO_MODEL_PATH` 加载本地 **Piper TTS** 模型（ONNX）。

#### 4.3 统一的 MLX TTS（CosyVoice2/3、Chatterbox 等）

如果你的 TTS 模型是 **MLX 格式**（例如 CosyVoice2、CosyVoice3、Chatterbox），推荐使用 `mlx-audio-plus` 作为统一后端。

> 为什么有时需要 `ref_audio`？
>
> `mlx-audio-plus` 覆盖的不少模型并不是“固定音色的普通 TTS”，而是更偏 **语音克隆 / 说话人条件（speaker conditioning）** 的 TTS：
> - 模型需要一段参考音频来决定输出的音色/说话人特征（例如 CosyVoice3、Chatterbox 常见用法）。
> - 这不是服务端强制要求，而是**具体模型/模式的必需输入**。如果模型本身要求 `ref_audio`，请求里不提供就会报错。
>
> 如果你想要“纯文本直接合成、无需参考音频”的体验，有三种选择：
> 1) 使用 `macos-say` 后端（不需要模型，也不需要 `ref_audio`）
> 2) 使用 `piper` 后端（典型的固定音色 TTS，不需要 `ref_audio`）
> 3) 在 `mlx-audio-plus` 里选择支持“无 ref_audio 模式”的模型/配置（取决于模型本身）

启动示例（HF repo id）：

```bash
AUDIO_BACKEND=mlx-audio-plus \
AUDIO_MODEL_ID=local-audio \
AUDIO_MODEL_PATH=mlx-community/Fun-CosyVoice3-0.5B-2512-4bit \
uv run uvicorn main:app --reload
```

请求示例（CosyVoice3 zero-shot，包含参考音频与转写文本）：

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

支持透传的常用扩展字段（不同模型/模式需要其中部分）：
- `ref_audio`：参考音频路径（CosyVoice/Chatterbox 常用）
- `ref_text`：参考音频的文本（CosyVoice3 zero-shot 常用）
- `instruct_text`：风格/情绪控制（CosyVoice3 instruct 常用）
- `source_audio`：用于 voice conversion（CosyVoice3 VC）

> 这些字段不是 OpenAI 官方 `/v1/audio/speech` 标准的一部分，但在本地 TTS 场景中非常实用。

---

## 🔧 配置（环境变量）

| 类别 | 变量 | 默认值 | 说明 |
|---|---|---:|---|
| 通用 | `HOST` | `127.0.0.1` | 监听地址 |
| 通用 | `PORT` | `8000` | 监听端口 |
| Chat | `CHAT_MODEL_ID` | `local-chat` | Chat 对外模型名 |
| Chat | `CHAT_MODEL_PATH` | *(空)* | MLX Chat 模型路径（不填通常回退到 Echo chat） |
| Audio | `AUDIO_MODEL_ID` | `local-audio` | TTS 对外模型名 |
| Audio | `AUDIO_BACKEND` | `auto` | TTS 后端：`auto`、`macos-say`、`piper`、`mlx-audio-plus`（统一 MLX TTS） |
| Audio | `AUDIO_MODEL_PATH` | *(空)* | TTS 模型路径：`piper` 为 `.onnx` 文件或仅含一个 `.onnx` 的目录；`mlx-audio-plus` 为本地模型目录或 HF repo id。 |
| Audio | `AUDIO_REF_AUDIO` | *(空)* | 启动时默认参考音频（路径或 base64/data URL）。请求未提供 `ref_audio` 时自动使用。 |
| Audio | `AUDIO_REF_TEXT` | *(空)* | 启动时默认 `ref_text`（可选）。 |
| Audio | `AUDIO_INSTRUCT_TEXT` | *(空)* | 启动时默认 `instruct_text`（可选）。 |
| Audio | `AUDIO_SOURCE_AUDIO` | *(空)* | 启动时默认 `source_audio`（可选，voice conversion）。 |
| 兼容 | `MODEL_ID`/`MODEL_PATH` | *(空)* | 兼容旧变量：映射到 Chat 配置 |

---

## 🔌 接口

### `GET /v1/models`

返回当前服务已注册的模型 id（扁平 list，含 chat + audio）。

### Chat Completions

**路由**：`POST /v1/chat/completions`

最小请求（非流式）：

```bash
curl http://127.0.0.1:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"local-chat","messages":[{"role":"user","content":"你好"}],"stream":false,"max_tokens":128}'
```

流式 SSE：

```bash
curl http://127.0.0.1:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H 'Accept: text/event-stream' \
  -d '{"model":"local-chat","messages":[{"role":"user","content":"用一句话介绍 MLX"}],"stream":true,"max_tokens":128}'
```

### Audio Speech (TTS)

**路由**：`POST /v1/audio/speech`

返回音频 bytes（不是 JSON）。

```bash
curl http://127.0.0.1:8000/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -d '{"model":"local-audio","input":"你好，我是本地语音合成。","voice":"Ting-Ting","format":"wav"}' \
  --output out.wav
```

> 说明：
> - `macos-say` 后端下，`voice` 会透传给 macOS `say -v`。
> - `mlx-audio-plus` 后端下，可额外传 `ref_audio/ref_text/instruct_text/source_audio` 等字段（见上文 TTS 章节）。

---

## 🧪 SDK 使用示例

> 以下示例展示“如何把 OpenAI 客户端指向本地服务”。
> 代码请复制到你的业务项目中运行（你的业务项目里安装 `openai` SDK 即可）。
>
> ```bash
> uv add openai
> ```

示例（伪代码，展示关键参数）：

```python
# client = OpenAI(base_url="http://127.0.0.1:8000/v1", api_key="local")
# resp = client.chat.completions.create(
#     model="local-chat",
#     messages=[{"role": "user", "content": "你好"}],
# )
# print(resp.choices[0].message.content)
```

---

## 🗂️ 项目结构

- `main.py`：Uvicorn 入口
- `app/app_factory.py`：创建 FastAPI app，初始化并注册模型
- `app/registry.py`：模型注册表（chat/tts 分开管理）
- `app/api/v1/openai.py`：OpenAI 风格的 chat/models 路由
- `app/api/v1/audio.py`：OpenAI 风格的 TTS 路由
- `app/engine/mlx_engine.py`：MLX Chat 推理引擎（基于 `mlx-lm`）
- `app/engine/macos_say_tts.py`：macOS `say` 的 TTS 引擎
- `tests/`：pytest 用例
- `test_main.http`：PyCharm HTTP Client 示例

---

## ✅ 测试

```bash
uv run pytest -q
```
