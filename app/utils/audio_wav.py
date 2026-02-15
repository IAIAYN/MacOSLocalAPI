from __future__ import annotations

import io
import wave


def read_wav_mono_pcm16(data: bytes) -> tuple[int, bytes]:
    """Read a WAV file and return (sample_rate, pcm16_bytes).

    Supports mono or multi-channel; multi-channel will be returned interleaved as-is.
    Only PCM16 is supported.
    """
    with wave.open(io.BytesIO(data), "rb") as wf:
        if wf.getsampwidth() != 2:
            raise ValueError(f"Only PCM16 wav supported, got sampwidth={wf.getsampwidth()}")
        sample_rate = wf.getframerate()
        frames = wf.readframes(wf.getnframes())
        return sample_rate, frames


def write_wav_pcm16(sample_rate: int, pcm16: bytes, *, n_channels: int = 1) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(n_channels)
        wf.setsampwidth(2)
        wf.setframerate(int(sample_rate))
        wf.writeframes(pcm16)
    return buf.getvalue()


def trim_repeat_prefix_pcm16(pcm16: bytes, *, sample_rate: int, max_prefix_seconds: float = 2.5) -> bytes:
    """Heuristic: remove an immediate repeated prefix.

    Detect pattern A + A + ... at the start and remove the first A.

    This is conservative and only attempts exact byte equality on PCM16.
    """

    if not pcm16:
        return pcm16

    total_frames = len(pcm16) // 2
    max_prefix = int(sample_rate * max_prefix_seconds)

    # Bail out for very short audio
    if total_frames < int(sample_rate * 0.4):
        return pcm16

    # Scan candidate prefix lengths (frames)
    step = max(1, int(sample_rate * 0.02))  # 20ms
    start_min = int(sample_rate * 0.2)
    start_max = min(max_prefix, total_frames // 2)

    for prefix_len in range(start_min, start_max, step):
        a0 = 0
        a1 = prefix_len * 2
        a2 = (prefix_len * 2) * 2
        if a2 > len(pcm16):
            break

        first = pcm16[a0:a1]
        second = pcm16[a1:a2]
        if first and first == second:
            return pcm16[a1:]

    return pcm16

