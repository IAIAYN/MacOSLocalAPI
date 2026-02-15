from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from .tts_base import TTSParams, TTSEngine


class MacOSSayTTSEngine(TTSEngine):
    """TTS engine backed by macOS `say`.

    This is a pragmatic local default on macOS. It outputs AIFF; we convert to WAV
    using `afconvert` (also available by default on macOS).

    Note: OpenAI's /v1/audio/speech supports mp3/wav/opus/aac/flac.
    We implement `wav` reliably and also accept `mp3` if `afconvert` supports it.
    """

    def __init__(self, model_id: str = "macos-say") -> None:
        self.model_id = model_id

        if shutil.which("say") is None:
            raise RuntimeError("macOS 'say' command not found")
        if shutil.which("afconvert") is None:
            raise RuntimeError("macOS 'afconvert' command not found")

    @staticmethod
    def _map_voice(voice: str) -> str:
        # Let users pass through native voices; default means do not specify.
        return voice

    def synthesize(self, text: str, params: TTSParams, *, format: str = "wav", **kwargs) -> bytes:
        fmt = (format or "wav").lower()
        if fmt not in {"wav", "mp3", "aiff"}:
            # Keep it explicit for now.
            raise ValueError(f"Unsupported format: {format}. Supported: wav, mp3, aiff")

        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            aiff_path = td_path / "out.aiff"

            cmd = ["say", "-o", str(aiff_path)]
            v = self._map_voice(params.voice)
            if v and v != "default":
                cmd.extend(["-v", v])

            # Note: `say` doesn't support continuous speed parameter, so we ignore params.speed.
            cmd.append(text)

            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            if fmt == "aiff":
                return aiff_path.read_bytes()

            out_path = td_path / f"out.{fmt}"

            # Convert using afconvert
            # - WAV: format WAVE + 16-bit LE PCM
            # - MP3: format 'mp3f'
            if fmt == "wav":
                conv = [
                    "afconvert",
                    "-f",
                    "WAVE",
                    "-d",
                    "LEI16",
                    str(aiff_path),
                    str(out_path),
                ]
            else:  # mp3
                conv = [
                    "afconvert",
                    "-f",
                    "mp3f",
                    str(aiff_path),
                    str(out_path),
                ]

            subprocess.run(conv, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return out_path.read_bytes()
