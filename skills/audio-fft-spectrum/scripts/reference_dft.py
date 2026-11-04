"""Small, dependency-free reference DFT for deterministic audio test fixtures.

O(N^2) by design; not for real-time audio or large production transforms.
"""
from __future__ import annotations

import cmath
import math


def periodic_hann(n: int) -> list[float]:
    """N-sample periodic Hann; intended for N >= 4 in test fixtures."""
    if not isinstance(n, int) or n < 4:
        raise ValueError("periodic_hann requires integer n >= 4")
    return [0.5 - 0.5 * math.cos(2 * math.pi * j / n) for j in range(n)]


def window_gains(window: list[float], sample_rate_hz: float) -> dict[str, float]:
    """Coherent gain, mean-square gain, and ENBW in bins and Hz."""
    n = len(window)
    if n == 0 or not math.isfinite(sample_rate_hz) or sample_rate_hz <= 0:
        raise ValueError("window must be nonempty and sample rate positive and finite")
    if any(not math.isfinite(w) for w in window):
        raise ValueError("window contains non-finite values")
    total = math.fsum(window)
    squared = math.fsum(w * w for w in window)
    if total == 0 or squared == 0:
        raise ValueError("window has zero sum or zero power")
    enbw_bins = n * squared / (total * total)
    return {
        "coherent_gain": total / n,
        "mean_square_gain": squared / n,
        "enbw_bins": enbw_bins,
        "enbw_hz": sample_rate_hz * squared / (total * total),
    }


def one_sided_dft(samples: list[float], window: list[float]) -> list[complex]:
    """Unnormalized real-input DFT, nonnegative bins only."""
    n = len(samples)
    if n < 2 or len(window) != n:
        raise ValueError("sample and window lengths must match and be >= 2")
    if any(not math.isfinite(v) for v in samples + window):
        raise ValueError("non-finite signal or window")
    return [
        sum((samples[j] * window[j] * cmath.exp(-2j * math.pi * k * j / n)
             for j in range(n)), 0j)
        for k in range(n // 2 + 1)
    ]


def one_sided_amplitude(samples: list[float], window: list[float]) -> list[float]:
    """Window-corrected peak-amplitude bins; exact for appropriate on-bin tones."""
    n = len(samples)
    total = math.fsum(window)
    if not math.isfinite(total) or total <= 0:
        raise ValueError("window must have positive finite sum for amplitude calibration")
    bins = one_sided_dft(samples, window)
    return [
        abs(value) * (1 if k == 0 or (n % 2 == 0 and k == n // 2) else 2) / total
        for k, value in enumerate(bins)
    ]
