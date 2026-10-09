"""PCM helpers: resampling, WAV framing, G.711 mu-law (for the Twilio bridge), mixing."""
from __future__ import annotations

import io
import wave

import numpy as np

PCM16_MAX = 32767


def resample_pcm16(pcm: bytes, src_rate: int, dst_rate: int) -> bytes:
    if src_rate == dst_rate or not pcm:
        return pcm
    x = np.frombuffer(pcm, dtype=np.int16).astype(np.float32)
    n_out = int(round(len(x) * dst_rate / src_rate))
    if n_out <= 0:
        return b""
    xi = np.linspace(0, len(x) - 1, n_out)
    y = np.interp(xi, np.arange(len(x)), x)
    return np.clip(y, -PCM16_MAX - 1, PCM16_MAX).astype(np.int16).tobytes()


def wav_bytes(pcm: bytes, rate: int) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm)
    return buf.getvalue()


def read_wav(data: bytes) -> tuple[bytes, int]:
    with wave.open(io.BytesIO(data), "rb") as w:
        rate = w.getframerate()
        pcm = w.readframes(w.getnframes())
        if w.getnchannels() == 2:
            arr = np.frombuffer(pcm, dtype=np.int16).reshape(-1, 2).mean(axis=1).astype(np.int16)
            pcm = arr.tobytes()
        if w.getsampwidth() != 2:
            raise ValueError("only 16-bit WAV supported")
    return pcm, rate


def mix_pcm16(a: bytes, b: bytes) -> bytes:
    if not a:
        return b
    if not b:
        return a
    n = max(len(a), len(b))
    xa = np.frombuffer(a.ljust(n, b"\x00"), dtype=np.int16).astype(np.int32)
    xb = np.frombuffer(b.ljust(n, b"\x00"), dtype=np.int16).astype(np.int32)
    return np.clip(xa + xb, -32768, 32767).astype(np.int16).tobytes()


def rms_pcm16(pcm: bytes) -> float:
    if not pcm:
        return 0.0
    x = np.frombuffer(pcm, dtype=np.int16).astype(np.float32)
    return float(np.sqrt(np.mean(x * x)) / PCM16_MAX)


# --- G.711 mu-law ------------------------------------------------------------
_MU = 255.0


def mulaw_to_pcm16(data: bytes) -> bytes:
    u = np.frombuffer(data, dtype=np.uint8).astype(np.int16)
    u = ~u & 0xFF
    sign = u & 0x80
    exponent = (u >> 4) & 0x07
    mantissa = u & 0x0F
    sample = ((mantissa << 3) + 0x84) << exponent
    sample = sample - 0x84
    sample = np.where(sign != 0, -sample, sample)
    return np.clip(sample, -32768, 32767).astype(np.int16).tobytes()


def pcm16_to_mulaw(pcm: bytes) -> bytes:
    x = np.frombuffer(pcm, dtype=np.int16).astype(np.int32)
    BIAS, CLIP = 0x84, 32635
    sign = np.where(x < 0, 0x80, 0)
    x = np.abs(x)
    x = np.minimum(x, CLIP) + BIAS
    exponent = np.floor(np.log2(x)).astype(np.int32) - 7
    exponent = np.clip(exponent, 0, 7)
    mantissa = (x >> (exponent + 3)) & 0x0F
    u = ~(sign | (exponent << 4) | mantissa) & 0xFF
    return u.astype(np.uint8).tobytes()
