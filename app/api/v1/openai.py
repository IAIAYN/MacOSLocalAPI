from __future__ import annotations

import json
import time
import uuid
import traceback
from collections.abc import AsyncIterator

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from ...engine.base import GenerationParams
from ...schemas.openai import (
    ChatCompletionChunk,
    ChatCompletionChunkChoice,
    ChatCompletionChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionResponseMessage,
    DeltaMessage,
    ListModelsResponse,
    OpenAIModel,
)

router = APIRouter()


@router.get("/models")
def list_models(request: Request) -> ListModelsResponse:
    registry = request.app.state.registry
    return ListModelsResponse(
        data=[OpenAIModel(id=m, owned_by="local") for m in registry.list_model_ids()]
    )


def _generation_params(req: ChatCompletionRequest) -> GenerationParams:
    return GenerationParams(
        max_tokens=req.max_tokens or 256,
        temperature=req.temperature if req.temperature is not None else 0.7,
        top_p=req.top_p if req.top_p is not None else 0.95,
    )


@router.post("/chat/completions")
async def chat_completions(request: Request, req: ChatCompletionRequest):
    registry = request.app.state.registry

    model = req.model or request.app.state.settings.chat_model_id

    try:
        engine = registry.get_chat(model)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    params = _generation_params(req)

    created = int(time.time())
    resp_id = f"chatcmpl-{uuid.uuid4().hex}"

    if req.stream:

        async def event_iter() -> AsyncIterator[bytes]:
            try:
                first = ChatCompletionChunk(
                    id=resp_id,
                    created=created,
                    model=model,
                    choices=[
                        ChatCompletionChunkChoice(
                            index=0,
                            delta=DeltaMessage(role="assistant"),
                            finish_reason=None,
                        )
                    ],
                )
                yield f"data: {first.model_dump_json()}\n\n".encode("utf-8")

                for piece in engine.stream_generate_chat(req.messages, params):
                    if not piece:
                        continue
                    chunk = ChatCompletionChunk(
                        id=resp_id,
                        created=created,
                        model=model,
                        choices=[
                            ChatCompletionChunkChoice(
                                index=0,
                                delta=DeltaMessage(content=piece),
                                finish_reason=None,
                            )
                        ],
                    )
                    yield f"data: {chunk.model_dump_json()}\n\n".encode("utf-8")

                done = ChatCompletionChunk(
                    id=resp_id,
                    created=created,
                    model=model,
                    choices=[
                        ChatCompletionChunkChoice(
                            index=0,
                            delta=DeltaMessage(),
                            finish_reason="stop",
                        )
                    ],
                )
                yield f"data: {done.model_dump_json()}\n\n".encode("utf-8")
                yield b"data: [DONE]\n\n"
            except Exception as e:
                traceback.print_exc()
                err = {
                    "error": {
                        "message": str(e),
                        "repr": repr(e),
                        "type": e.__class__.__name__,
                    }
                }
                yield f"data: {json.dumps(err, ensure_ascii=False)}\n\n".encode("utf-8")
                yield b"data: [DONE]\n\n"

        return StreamingResponse(event_iter(), media_type="text/event-stream")

    try:
        text = engine.generate_chat(req.messages, params)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail={
                "message": str(e),
                "repr": repr(e),
                "type": e.__class__.__name__,
            },
        )

    response = ChatCompletionResponse(
        id=resp_id,
        created=created,
        model=model,
        choices=[
            ChatCompletionChoice(
                index=0,
                message=ChatCompletionResponseMessage(content=text),
                finish_reason="stop",
            )
        ],
    )
    return JSONResponse(content=json.loads(response.model_dump_json()))
