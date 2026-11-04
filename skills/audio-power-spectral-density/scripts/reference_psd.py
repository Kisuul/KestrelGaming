"""Small, intentionally O(M*Nfft) PSD and Welch mathematical reference.

For deterministic fixtures only, not realtime use or calibrated measurements.
Python 3.9+, standard library only.
"""
from __future__ import annotations

import cmath
import math
from typing import Optional

MAX_REFERENCE_NFFT = 1024


def periodogram(
    samples: list[float],
    window: list[float],
    sample_rate_hz: float,
    nfft: Optional[int] = None,
    detrend_mean: bool = False,
) -> tuple[list[float], list[float]]:
    """Return (Hz frequencies, one-sided PSD in sample²/Hz)."""
    m = len(samples)
    nfft = m if nfft is None else nfft
    if m < 2 or len(window) != m:
        raise ValueError("samples and window must have equal length >= 2")
    if not isinstance(nfft, int) or isinstance(nfft, bool) or not (m <= nfft <= MAX_REFERENCE_NFFT):
        raise ValueError("nfft must be an integer >= frame length, <= oracle limit")
    if not math.isfinite(sample_rate_hz) or sample_rate_hz <= 0:
        raise ValueError("sample rate must be positive and finite")
    if any(not math.isfinite(v) for v in samples) or any(not math.isfinite(w) for w in window):
        raise ValueError("samples and window must be finite")
    energy = math.fsum(w * w for w in window)
    if energy <= 0 or not math.isfinite(energy):
        raise ValueError("window energy must be positive and finite")

    mean = math.fsum(samples) / m if detrend_mean else 0.0
    weighted = [(value - mean) * weight for value, weight in zip(samples, window)]
    if any(not math.isfinite(v) for v in weighted):
        raise ValueError("detrending/windowing produced a non-finite value")
    norm = sample_rate_hz * energy
    spectrum = []
    frequencies = []
    for k in range(nfft // 2 + 1):
        value = sum(
            (weighted[j] * cmath.exp(-2j * math.pi * k * j / nfft)
             for j in range(m)), 0j
        )
        multiplier = 1 if k == 0 or (nfft % 2 == 0 and k == nfft // 2) else 2
        spectrum.append(multiplier * (abs(value) ** 2) / norm)
        frequencies.append(k * sample_rate_hz / nfft)
    return frequencies, spectrum


def welch_mean(
    samples: list[float],
    window: list[float],
    sample_rate_hz: float,
    hop: int,
    nfft: Optional[int] = None,
    detrend_mean: bool = False,
) -> tuple[list[float], list[float], int]:
    """Mean of complete, contiguous frames; returns (frequencies, PSD, segment count).

    hop may exceed frame length (gapped sampling); the caller must record that policy.
    """
    m = len(window)
    if not isinstance(hop, int) or isinstance(hop, bool) or hop <= 0:
        raise ValueError("hop must be a positive integer")
    if m < 2 or len(samples) < m:
        raise ValueError("not enough samples for one complete segment")
    if any(not math.isfinite(x) for x in samples):
        raise ValueError("non-finite input samples")
    total = []
    frequencies = []
    count = 0
    for start in range(0, len(samples) - m + 1, hop):
        frequencies, power = periodogram(
            samples[start:start + m], window, sample_rate_hz,
            nfft=nfft, detrend_mean=detrend_mean
        )
        if not total:
            total = [0.0] * len(power)
        for k, value in enumerate(power):
            total[k] += value
        count += 1
    return frequencies, [value / count for value in total], count
