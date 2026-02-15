from __future__ import annotations

import os
import tempfile
from pathlib import Path

from .tts_base import TTSParams, TTSEngine
from app.utils.audio_wav import read_wav_mono_pcm16, trim_repeat_prefix_pcm16, write_wav_pcm16


class MLXAudioPlusTTSEngine(TTSEngine):
    """TTS engine backed by `mlx-audio-plus`.

    `mlx-audio-plus` is installed as the Python package `mlx_audio`.

    This engine treats `model_path` as either:
    - a local directory path containing the MLX TTS model, or
    - a HuggingFace repo id like `mlx-community/Fun-CosyVoice3-0.5B-2512-4bit`

    The underlying library writes audio to a file; we read and return bytes.
    """

    def __init__(self, model_id: str, model_path: str) -> None:
        self.model_id = model_id
        self.model_path = model_path

        # Validate import early for clear startup errors.
        try:
            from mlx_audio.tts.generate import generate_audio  # noqa: F401
        except Exception as e:  # pragma: no cover
            raise RuntimeError(
                "mlx-audio-plus is required for AUDIO_BACKEND=mlx-audio-plus. "
                "Install with: uv add mlx-audio-plus"
            ) from e

    @staticmethod
    def _guess_audio_format(fmt: str | None) -> str:
        f = (fmt or "wav").lower()
        if f in {"wav", "mp3", "flac", "aac", "opus"}:
            return f
        return "wav"

    @staticmethod
    def _pick_output_file(tmp_dir: Path, out_prefix: str, audio_format: str) -> Path:
        """Pick the best output file produced by mlx_audio.

        Some versions/models produce numbered outputs like `speech_000.wav`.
        """
        direct = Path(f"{out_prefix}.{audio_format}")
        if direct.exists():
            return direct

        # Common fallback
        wav = Path(f"{out_prefix}.wav")
        if wav.exists():
            return wav

        # Search for numbered outputs
        candidates = sorted(tmp_dir.glob(f"speech_*.{audio_format}"))
        if not candidates and audio_format != "wav":
            candidates = sorted(tmp_dir.glob("speech_*.wav"))

        if candidates:
            # Pick the first segment by default to avoid overlap/repetition.
            return candidates[0]

        # Last resort: any audio file in tmp dir
        any_files = sorted(tmp_dir.glob(f"*.{audio_format}"))
        if not any_files and audio_format != "wav":
            any_files = sorted(tmp_dir.glob("*.wav"))
        if any_files:
            return any_files[-1]

        raise RuntimeError("mlx_audio did not produce an output audio file")

    def synthesize(self, text: str, params: TTSParams, *, format: str = "wav", **kwargs) -> bytes:  # type: ignore[override]
        from mlx_audio.tts.generate import generate_audio

        audio_format = self._guess_audio_format(format)

        # Some models need reference audio; we accept either file paths or bytes.
        # For bytes we persist to a temp wav.
        tmp_files: list[Path] = []

        def _ensure_path(val):
            if val is None:
                return None
            if isinstance(val, (str, os.PathLike)):
                return str(val)
            if isinstance(val, (bytes, bytearray)):
                fd, p = tempfile.mkstemp(suffix=".wav")
                os.close(fd)
                path = Path(p)
                path.write_bytes(bytes(val))
                tmp_files.append(path)
                return str(path)
            return str(val)

        ref_audio = _ensure_path(kwargs.pop("ref_audio", None))
        source_audio = _ensure_path(kwargs.pop("source_audio", None))
        ref_text = kwargs.pop("ref_text", None)
        instruct_text = kwargs.pop("instruct_text", None)

        try:
            with tempfile.TemporaryDirectory() as td:
                tmp_dir = Path(td)
                out_prefix = str(tmp_dir / "speech")

                call_kwargs = dict(
                    model=self.model_path,
                    ref_audio=ref_audio,
                    source_audio=source_audio,
                    ref_text=ref_text,
                    instruct_text=instruct_text,
                    file_prefix=out_prefix,
                    audio_format=audio_format,
                    join_audio=True,
                    verbose=False,
                )
                # Voice conversion mode may not provide text.
                if text:
                    call_kwargs["text"] = text

                generate_audio(**call_kwargs)

                out_file = self._pick_output_file(tmp_dir, out_prefix, audio_format)
                audio_bytes = out_file.read_bytes()

                # Heuristic de-duplication for repeated prefix (wav only)
                if audio_format == "wav":
                    try:
                        sr, pcm = read_wav_mono_pcm16(audio_bytes)
                        trimmed = trim_repeat_prefix_pcm16(pcm, sample_rate=sr)
                        if trimmed != pcm:
                            audio_bytes = write_wav_pcm16(sr, trimmed)
                    except Exception:
                        # Never fail the request because of post-processing.
                        pass

                return audio_bytes
        finally:
            # Cleanup temp refs
            for p in tmp_files:
                try:
                    p.unlink(missing_ok=True)
                except Exception:
                    pass

