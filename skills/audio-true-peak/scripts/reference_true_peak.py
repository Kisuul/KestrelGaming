"""Experimental finite-buffer intersample peak estimate; NOT BS.1770 compliant.

Deliberately slow, standard-library Lanczos-windowed sinc interpolation with
zero extension. No realtime callbacks, normative FIR or calibration.
"""
from __future__ import annotations

import math
from typing import Optional

MAX_REFERENCE_SAMPLES = 512
SUPPORTED_FACTORS = (4, 8, 16)


def _sinc(value: float) -> float:
    if value == 0.0:
        return 1.0
    theta = math.pi * value
    return math.sin(theta) / theta


def _db(amplitude: float, reference: float) -> float:
    return -math.inf if amplitude == 0.0 else (
        20 * (math.log10(amplitude) - math.log10(reference))
    )


def experimental_peak_estimate(
    samples: list[float],
    sample_rate_hz: float = 48000.0,
    oversample_factor: int = 8,
    radius: int = 32,
    reference: float = 1.0,
    origin_sample: int = 0,
) -> dict:
    """Evaluate a finite record on an oversampled grid, with an interior result.

    The Lanczos kernel and zero extension are not normative true-peak filters.
    Returned subsample indices are exact integers, even for large origins.
    """
    n = len(samples)
    if not 2 <= n <= MAX_REFERENCE_SAMPLES:
        raise ValueError("reference accepts 2 to 512 samples")
    if any(not math.isfinite(x) for x in samples):
        raise ValueError("all input samples must be finite")
    if (isinstance(oversample_factor, bool)
            or oversample_factor not in SUPPORTED_FACTORS):
        raise ValueError("oversample_factor must be 4, 8 or 16")
    if (not isinstance(radius, int) or isinstance(radius, bool)
            or not 8 <= radius <= 64):
        raise ValueError("radius must be an integer from 8 to 64")
    if not math.isfinite(sample_rate_hz) or sample_rate_hz <= 0:
        raise ValueError("sample rate must be finite and positive")
    grid_rate = sample_rate_hz * oversample_factor
    if not math.isfinite(grid_rate):
        raise ValueError("evaluation rate exceeds representable range")
    if not math.isfinite(reference) or reference <= 0:
        raise ValueError("reference amplitude must be finite and positive")
    if not isinstance(origin_sample, int) or isinstance(origin_sample, bool) or origin_sample < 0:
        raise ValueError("origin_sample must be a nonnegative integer")

    sample_peak = max(abs(x) for x in samples)
    sample_index = next(i for i, x in enumerate(samples) if abs(x) == sample_peak)
    signal = [x / sample_peak for x in samples] if sample_peak else [0.] * n
    # Start at the earliest actual sample peak; an interpolated higher peak
    # replaces this only with a strict improvement.
    best = (1.0, sample_index * oversample_factor) if sample_peak else (0.0, 0)
    interior: Optional[tuple[float, int]] = None

    for q in range((n - 1) * oversample_factor + 1):
        t = q / oversample_factor
        if q % oversample_factor == 0:
            magnitude = abs(signal[q // oversample_factor])
        else:
            low = max(0, math.floor(t - radius) + 1)
            high = min(n, math.ceil(t + radius))
            magnitude = abs(math.fsum(
                signal[j] * _sinc(t - j) * _sinc((t - j) / radius)
                for j in range(low, high)
            ))
        if magnitude > best[0]:
            best = (magnitude, q)
        if radius <= t <= n - 1 - radius:
            if interior is None or magnitude > interior[0]:
                interior = (magnitude, q)

    def describe(candidate: tuple[float, int]) -> dict:
        mag, q = candidate
        value = mag * sample_peak
        if not math.isfinite(value):
            raise ValueError("estimated peak exceeds finite output range")
        return {
            "peak_amplitude": value,
            "peak_position_subsample_index": origin_sample * oversample_factor + q,
            "level_db_re_reference": _db(value, reference),
        }

    return {
        "maturity": "experimental_not_bs1770_compliant",
        "method": "zero_extended_lanczos_windowed_sinc",
        "sample_peak_amplitude": sample_peak,
        "sample_peak_at_sample": origin_sample + sample_index,
        "estimated": describe(best),
        "supported_interior_estimate": describe(interior) if interior is not None else None,
        "peak_in_boundary_region": not (
            radius * oversample_factor <= best[1]
            <= (n - 1 - radius) * oversample_factor
        ),
        "origin_sample": origin_sample,
        "sample_count": n,
        "oversample_factor": oversample_factor,
        "sample_rate_hz": sample_rate_hz,
        "evaluation_rate_hz": grid_rate,
        "radius_samples": radius,
        "reference_amplitude": reference,
    }
