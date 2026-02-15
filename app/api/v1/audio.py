from __future__ import annotations

import base64
import binascii
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from ...engine.tts_base import TTSParams
from ...schemas.openai import AudioSpeechRequest

router = APIRouter()


def _maybe_write_base64_audio_to_tmp(val: str | None, *, suffix: str = ".wav") -> tuple[str | None, list[Path]]:
    """If val looks like base64 audio bytes, write to a temp file and return that path.

    Otherwise treat it as a normal path and return as-is.

    Returns: (path_or_original, tmp_files_to_cleanup)
    """
    if val is None:
        return None, []

    # Heuristic: if it's a file that exists, keep as path.
    try:
        if os.path.exists(val):
            return val, []
    except Exception:
        pass

    # Heuristic: data URL prefix
    if val.startswith("data:") and "," in val:
        val = val.split(",", 1)[1]

    # Try base64 decode. If it fails, keep original string.
    try:
        data = base64.b64decode(val, validate=True)
    except (binascii.Error, ValueError):
        return val, []

    fd, p = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    path = Path(p)
    path.write_bytes(data)
    return str(path), [path]


@router.post("/audio/speech")
async def audio_speech(request: Request, body: AudioSpeechRequest):
    registry = request.app.state.registry
    settings = request.app.state.settings

    try:
        engine = registry.get_tts(body.model)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    fmt = (body.format or "wav").lower()
    voice = body.voice or "default"
    speed = float(body.speed) if body.speed is not None else 1.0

    # Collect extra params for backend-specific features
    extra = body.model_dump(exclude_none=True)
    extra.pop("model", None)
    text = extra.pop("input", "")
    extra.pop("voice", None)
    extra.pop("format", None)
    extra.pop("speed", None)

    # Apply defaults from env if not provided
    if "ref_audio" not in extra and getattr(settings, "audio_ref_audio", None):
        extra["ref_audio"] = settings.audio_ref_audio
    if "ref_text" not in extra and getattr(settings, "audio_ref_text", None):
        extra["ref_text"] = settings.audio_ref_text
    if "instruct_text" not in extra and getattr(settings, "audio_instruct_text", None):
        extra["instruct_text"] = settings.audio_instruct_text
    if "source_audio" not in extra and getattr(settings, "audio_source_audio", None):
        extra["source_audio"] = settings.audio_source_audio

    # Non-standard but useful: speaker_id (piper multi speaker)
    speaker_id = None
    if "speaker_id" in extra and extra.get("speaker_id") is not None:
        try:
            speaker_id = int(extra.pop("speaker_id"))
        except Exception:
            speaker_id = None

    # Support base64 audio payloads for ref_audio/source_audio
    tmp_files: list[Path] = []
    if "ref_audio" in extra:
        ref_audio_path, created = _maybe_write_base64_audio_to_tmp(extra.get("ref_audio"))
        extra["ref_audio"] = ref_audio_path
        tmp_files.extend(created)
    if "source_audio" in extra:
        src_audio_path, created = _maybe_write_base64_audio_to_tmp(extra.get("source_audio"))
        extra["source_audio"] = src_audio_path
        tmp_files.extend(created)

    audio: bytes | None = None

    try:
        try:
            audio = engine.synthesize(
                text,
                TTSParams(voice=voice, speed=speed, speaker_id=speaker_id),
                format=fmt,
                **extra,
            )
        except TypeError:
            # Backward compatible for engines that don't accept **extra
            audio = engine.synthesize(
                text,
                TTSParams(voice=voice, speed=speed, speaker_id=speaker_id),
                format=fmt,
            )
    except ValueError as e:
        # Surface common user input errors as 400
        msg = str(e)
        if "ref_audio" in msg and "required" in msg:
            msg += (
                " (提示：当前 MLX TTS 模型需要 ref_audio 用于音色/说话人条件。"
                "你可以传本地路径 ref_audio=\"/path/to.wav\" 或 base64 字符串。)"
            )
        raise HTTPException(status_code=400, detail=msg)
    except Exception as e:
        # Treat common missing-parameter errors as 400 even if wrapped.
        msg = str(e)
        if "ref_audio" in msg and "required" in msg:
            msg += (
                " (提示：当前 MLX TTS 模型需要 ref_audio 用于音色/说话人条件。"
                "你可以传本地路径 ref_audio=\"/path/to.wav\" 或 base64 字符串。)"
            )
            raise HTTPException(status_code=400, detail=msg)
        raise HTTPException(status_code=500, detail=f"TTS failed: {e.__class__.__name__}: {e}")
    finally:
        for p in tmp_files:
            try:
                p.unlink(missing_ok=True)
            except Exception:
                pass

    assert audio is not None

    media_type = {
        "wav": "audio/wav",
        "mp3": "audio/mpeg",
        "aiff": "audio/aiff",
    }.get(fmt, "application/octet-stream")

    return Response(content=audio, media_type=media_type)
