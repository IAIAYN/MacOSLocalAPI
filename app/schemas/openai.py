from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, ConfigDict


# --- Shared ---


class OpenAIModel(BaseModel):
    id: str
    object: Literal["model"] = "model"
    created: int | None = None
    owned_by: str | None = None


class ListModelsResponse(BaseModel):
    object: Literal["list"] = "list"
    data: list[OpenAIModel]


# --- Chat Completions ---


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str | None = None
    name: str | None = None
    tool_call_id: str | None = None
    # We don't implement tool calls yet but keep it permissive.
    tool_calls: list[dict[str, Any]] | None = None


class ChatCompletionRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    model: str | None = None
    messages: list[ChatMessage]

    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = Field(default=None, ge=1)

    stream: bool | None = False


class ChatCompletionResponseMessage(BaseModel):
    role: Literal["assistant"] = "assistant"
    content: str | None = None


class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatCompletionResponseMessage
    finish_reason: str | None = None


class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatCompletionResponse(BaseModel):
    id: str
    object: Literal["chat.completion"] = "chat.completion"
    created: int
    model: str
    choices: list[ChatCompletionChoice]
    usage: Usage = Field(default_factory=Usage)


# --- Streaming (SSE chunks) ---


class DeltaMessage(BaseModel):
    role: Literal["assistant"] | None = None
    content: str | None = None


class ChatCompletionChunkChoice(BaseModel):
    index: int
    delta: DeltaMessage
    finish_reason: str | None = None


class ChatCompletionChunk(BaseModel):
    id: str
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    created: int
    model: str
    choices: list[ChatCompletionChunkChoice]


# --- Audio / Speech (TTS) ---


class AudioSpeechRequest(BaseModel):
    model: str
    input: str
    voice: str | None = None
    format: str | None = "wav"
    speed: float | None = 1.0

    # Extensions for local TTS backends (mlx-audio-plus / cosyvoice / chatterbox)
    # You may pass either a local file path, or a base64-encoded audio bytes string.
    ref_audio: str | None = None
    ref_text: str | None = None
    instruct_text: str | None = None
    source_audio: str | None = None

    # Generic multi-speaker hint (used by some backends)
    speaker_id: int | None = None

    class Config:
        extra = "allow"
