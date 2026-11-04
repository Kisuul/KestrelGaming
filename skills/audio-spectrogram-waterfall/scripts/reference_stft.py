"""Tiny, dependency-free STFT reference for deterministic audio-analysis fixtures.

This is a *left-aligned, unpadded, complete-frame* oracle. Runtime is intentionally
O(frames * window_length * fft_length). Not for production or realtime audio.
"""
from __future__ import annotations

import cmath
import math
from typing import Optional

MAX_REFERENCE_NFFT = 512
MAX_REFERENCE_FRAMES = 128


def _settings(window, fs, hop, nfft, scaling, origin):
    m = len(window)
    if m < 2:
        raise ValueError("window must have at least two samples")
    if not isinstance(hop, int) or isinstance(hop, bool) or not (1 <= hop <= m):
        raise ValueError("hop must be an integer between one and window length")
    if not isinstance(nfft, int) or isinstance(nfft, bool) or not (m <= nfft <= MAX_REFERENCE_NFFT):
        raise ValueError("nfft must be an integer >= window length and <= oracle limit")
    if not math.isfinite(fs) or fs <= 0:
        raise ValueError("sample rate must be positive and finite")
    if not isinstance(origin, int) or isinstance(origin, bool) or origin < 0:
        raise ValueError("origin_sample must be a nonnegative integer")
    if scaling not in ("amplitude", "psd"):
        raise ValueError("scaling must be amplitude or psd")
    if any(not math.isfinite(w) for w in window):
        raise ValueError("window must be finite")
    total = math.fsum(window)
    square = math.fsum(w*w for w in window)
    if not math.isfinite(square) or square <= 0:
        raise ValueError("window energy must be positive and finite")
    if scaling == "amplitude" and (not math.isfinite(total) or total <= 0):
        raise ValueError("amplitude calibration requires positive finite coherent sum")
    if scaling == "psd" and (not math.isfinite(fs * square) or fs * square <= 0):
        raise ValueError("PSD normalization must be positive and finite")
    return m, total, square


def _frame(segment, window, fs, nfft, scaling, origin_sample, total, square):
    m = len(window)
    weights = [v*w for v, w in zip(segment, window)]
    if any(not math.isfinite(v) for v in weights):
        raise ValueError("windowing resulted in nonfinite samples")
    values = []
    for k in range(nfft//2 + 1):
        z = sum(
            (weights[j] * cmath.exp(-2j*math.pi*k*j/nfft)
             for j in range(m)), 0j
        )
        factor = 1 if k == 0 or (nfft % 2 == 0 and k == nfft//2) else 2
        if scaling == "amplitude":
            values.append(factor*abs(z)/total)
        else:
            values.append(factor*abs(z)**2/(fs*square))
    center = origin_sample + (m - 1) / 2
    return {
        "start_sample": origin_sample,
        "end_sample_exclusive": origin_sample + m,
        "center_sample_twice": 2 * origin_sample + m - 1,
        "center_sample": center,
        "center_seconds": center / fs,
        "values": values,
    }


def _pack(frames, fs, m, nfft, hop, scaling):
    return {
        "frequencies_hz": [k*fs/nfft for k in range(nfft//2 + 1)],
        "frames": frames,
        "sample_rate_hz": fs,
        "window_length": m,
        "fft_length": nfft,
        "hop_samples": hop,
        "scaling": scaling,
    }


def stft_frames(
    samples: list[float], window: list[float], sample_rate_hz: float,
    hop: int, nfft: Optional[int] = None, scaling: str = "psd",
    origin_sample: int = 0,
) -> dict:
    """Calculate complete frames starting at origin_sample, origin_sample+hop, ..."""
    m = len(window)
    nfft = m if nfft is None else nfft
    m, total, square = _settings(window, sample_rate_hz, hop, nfft, scaling, origin_sample)
    if any(not math.isfinite(v) for v in samples):
        raise ValueError("samples must be finite")
    count = max(0, 1 + (len(samples)-m)//hop)
    if count > MAX_REFERENCE_FRAMES:
        raise ValueError("too many frames for reference oracle")
    frames = [
        _frame(samples[start:start+m], window, sample_rate_hz, nfft, scaling,
               origin_sample + start, total, square)
        for start in range(0, len(samples)-m+1, hop)
    ]
    return _pack(frames, sample_rate_hz, m, nfft, hop, scaling)


def stft_chunked(
    chunks: list[list[float]], window: list[float], sample_rate_hz: float,
    hop: int, nfft: Optional[int] = None, scaling: str = "psd",
    origin_sample: int = 0,
) -> dict:
    """Incremental *contiguous* chunks; sample discontinuities must be handled by caller.

    The list-backed oracle is intentionally not bounded-realtime or allocation-free.
    """
    m = len(window)
    nfft = m if nfft is None else nfft
    m, total, square = _settings(window, sample_rate_hz, hop, nfft, scaling, origin_sample)
    pending = []
    next_start = origin_sample
    frames = []
    for chunk in chunks:
        if any(not math.isfinite(v) for v in chunk):
            raise ValueError("chunks must contain finite samples")
        pending.extend(chunk)
        while len(pending) >= m:
            if len(frames) >= MAX_REFERENCE_FRAMES:
                raise ValueError("too many frames for reference oracle")
            frames.append(_frame(pending[:m], window, sample_rate_hz, nfft,
                                 scaling, next_start, total, square))
            del pending[:hop]
            next_start += hop
    return _pack(frames, sample_rate_hz, m, nfft, hop, scaling)
