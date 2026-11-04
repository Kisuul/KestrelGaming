"""Simple, deterministic RMS and sample-crest mathematical reference.

Not a VU, true-peak, LUFS, SPL, or AES17-conformant meter.
"""
from __future__ import annotations

import math
from typing import Optional


def level_db(amplitude: float, reference: float = 1.0) -> float:
    """Amplitude ratio in dB, with exact silence as negative infinity."""
    if not math.isfinite(amplitude) or amplitude < 0:
        raise ValueError("amplitude must be finite and nonnegative")
    if not math.isfinite(reference) or reference <= 0:
        raise ValueError("reference amplitude must be positive and finite")
    return -math.inf if amplitude == 0 else 20 * math.log10(amplitude / reference)


def sample_levels(samples: list[float]) -> dict[str, Optional[float]]:
    """Finite-window, unweighted levels in sample-amplitude units.

    crest_factor and crest_db are None for silence; do not replace with zero.
    """
    if not samples:
        raise ValueError("nonempty sample window required")
    if any(not math.isfinite(x) for x in samples):
        raise ValueError("non-finite samples")
    peak = max(abs(x) for x in samples)
    mean_square = math.fsum(x*x for x in samples) / len(samples)
    if not math.isfinite(mean_square):
        raise ValueError("non-finite accumulated energy")
    rms = math.sqrt(mean_square)
    crest = peak/rms if rms else None
    return {
        "sample_peak": peak,
        "mean_square": mean_square,
        "rms": rms,
        "crest_factor": crest,
        "crest_db": 20*math.log10(crest) if crest is not None else None,
        "sample_peak_db_re_1": level_db(peak),
        "rms_db_re_1": level_db(rms),
    }
