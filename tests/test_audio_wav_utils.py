from __future__ import annotations

from app.utils.audio_wav import read_wav_mono_pcm16, trim_repeat_prefix_pcm16, write_wav_pcm16


def test_trim_repeat_prefix_pcm16_removes_duplicated_prefix():
    sr = 16000

    # Build a fake PCM16 stream: A + A + B
    # A: 0..999, B: 1000..1499
    def s16(n: int) -> bytes:
        return int(n).to_bytes(2, "little", signed=True)

    a = b"".join(s16(i % 300) for i in range(8000))  # 0.5s
    b = b"".join(s16((i + 123) % 300) for i in range(4000))  # 0.25s
    pcm = a + a + b

    trimmed = trim_repeat_prefix_pcm16(pcm, sample_rate=sr, max_prefix_seconds=1.0)

    # Should drop the first A (exact duplicate)
    assert trimmed == a + b


def test_read_write_roundtrip_wav_pcm16():
    sr = 22050
    pcm = b"\x01\x00" * 1000
    wav = write_wav_pcm16(sr, pcm)
    sr2, pcm2 = read_wav_mono_pcm16(wav)
    assert sr2 == sr
    assert pcm2 == pcm

