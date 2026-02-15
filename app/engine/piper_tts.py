from __future__ import annotations

from pathlib import Path

from .tts_base import TTSParams, TTSEngine


class PiperTTSEngine(TTSEngine):
    """Local TTS engine backed by `piper-tts`.

    `AUDIO_MODEL_PATH` should point to either:
    - a `.onnx` model file, or
    - a directory containing exactly one `.onnx` model

    Piper outputs raw audio; we wrap it into a WAV container.
    """

    def __init__(self, model_id: str, model_path: str) -> None:
        self.model_id = model_id

        self._model_file = self._resolve_model_file(model_path)

        # Import lazily so the rest of the service can still run without piper.
        from piper.voice import PiperVoice  # type: ignore

        self._voice = PiperVoice.load(str(self._model_file))

    @staticmethod
    def _resolve_model_file(model_path: str) -> Path:
        p = Path(model_path).expanduser()
        if not p.exists():
            raise FileNotFoundError(f"AUDIO_MODEL_PATH not found: {p}")

        if p.is_file():
            if p.suffix.lower() != ".onnx":
                raise ValueError(f"Piper model must be a .onnx file, got: {p.name}")
            return p

        # Directory: pick a single onnx file.
        onnx = sorted(p.glob("*.onnx"))
        if len(onnx) == 0:
            raise FileNotFoundError(f"No .onnx model found under directory: {p}")
        if len(onnx) > 1:
            raise ValueError(
                f"Multiple .onnx models found under {p}. Please set AUDIO_MODEL_PATH to the specific .onnx file."
            )
        return onnx[0]

    @staticmethod
    def _wav_bytes(samples: list[int], sample_rate: int) -> bytes:
        """Build a minimal PCM16 mono WAV file."""
        import io
        import wave
        import struct

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # int16
            wf.setframerate(int(sample_rate))
            wf.writeframes(struct.pack("<" + "h" * len(samples), *samples))
        return buf.getvalue()

    def synthesize(self, text: str, params: TTSParams, *, format: str = "wav", **kwargs) -> bytes:
        fmt = (format or "wav").lower()
        if fmt != "wav":
            raise ValueError("PiperTTSEngine currently supports only 'wav' output")

        # PiperVoice.synthesize yields chunks of (audio, sample_rate) depending on version.
        # We collect to a single list of int16.
        samples: list[int] = []
        sample_rate: int | None = None

        # The API differs slightly across piper versions; handle both.
        if hasattr(self._voice, "synthesize"):
            out = self._voice.synthesize(text)  # type: ignore[attr-defined]
            # Possible outputs:
            # - tuple[list[int], int]
            # - generator yielding tuple[list[int], int]
            if isinstance(out, tuple) and len(out) == 2:
                chunk, sr = out
                samples.extend(list(chunk))
                sample_rate = int(sr)
            else:
                for chunk, sr in out:  # type: ignore[assignment]
                    samples.extend(list(chunk))
                    sample_rate = int(sr)
        else:
            raise RuntimeError("Unsupported piper-tts version: PiperVoice has no synthesize()")

        if sample_rate is None:
            raise RuntimeError("Piper returned no audio")

        return self._wav_bytes(samples, sample_rate)
