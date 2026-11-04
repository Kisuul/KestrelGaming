"""Deterministic, bounded PCM fixture generation for mathematical DSP tests.

No device, randomness service, NumPy, codec, or realtime functionality.
Test expectations must come from mathematics or an *independent* implementation.
"""
from __future__ import annotations

import math

MAX_SAMPLES = 256
KINDS = ("silence", "dc", "alternating", "impulse", "coherent_sine",
         "offbin_sine", "seeded_noise", "adjacent_pair")
CHANNEL_MODES = ("mono", "stereo_inphase", "stereo_antiphase")


def _positive_integer(value: int, name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(f"{name} must be a positive integer")


def make_fixture(
    kind: str,
    sample_count: int = 64,
    sample_rate_hz: float = 48000.0,
    amplitude: float = 0.5,
    bin_index: float = 2.0,
    phase_rad: float = 0.0,
    impulse_index: int = 0,
    seed: int = 1729,
    origin_sample: int = 0,
    channel_mode: str = "mono",
) -> dict:
    """Create small planar PCM with explicit clock, configuration, and provenance.

    Off-bin test uses bin_index + 0.25 cycles per sample_count.
    Seeded noise uses a specified 32-bit LCG and dyadic float conversion,
    not Python Random's implementation-dependent sampling sequences.
    """
    if kind not in KINDS:
        raise ValueError("unknown fixture kind")
    if channel_mode not in CHANNEL_MODES:
        raise ValueError("unknown channel mode")
    _positive_integer(sample_count, "sample_count")
    if not 8 <= sample_count <= MAX_SAMPLES:
        raise ValueError("sample_count must be between 8 and 256")
    if not isinstance(origin_sample, int) or isinstance(origin_sample, bool) or origin_sample < 0:
        raise ValueError("origin_sample must be a nonnegative integer")
    if not math.isfinite(sample_rate_hz) or sample_rate_hz <= 0:
        raise ValueError("sample_rate_hz must be finite and positive")
    if not math.isfinite(amplitude) or amplitude < 0 or amplitude > 1:
        raise ValueError("amplitude must be finite and in [0, 1] for normalized fixtures")
    if not math.isfinite(bin_index) or not (0 < bin_index < sample_count / 2 - 0.25):
        raise ValueError("bin_index out of valid interior frequency range")
    if not math.isfinite(phase_rad):
        raise ValueError("phase_rad must be finite")
    if not isinstance(impulse_index, int) or isinstance(impulse_index, bool) or not 0 <= impulse_index < sample_count:
        raise ValueError("impulse_index must locate a sample in the fixture")
    if not isinstance(seed, int) or isinstance(seed, bool) or not 0 <= seed < 2**32:
        raise ValueError("seed must be a uint32 integer")

    if kind == "adjacent_pair" and impulse_index + 1 >= sample_count:
        raise ValueError("adjacent_pair requires a following sample")
    n = sample_count
    if kind == "silence":
        samples = [0.0] * n
    elif kind == "dc":
        samples = [amplitude] * n
    elif kind == "alternating":
        samples = [amplitude * (1 if j % 2 == 0 else -1) for j in range(n)]
    elif kind == "impulse":
        samples = [amplitude if j == impulse_index else 0.0 for j in range(n)]
    elif kind == "adjacent_pair":
        samples = [amplitude if j in (impulse_index, impulse_index + 1) else 0.0 for j in range(n)]
    elif kind in ("coherent_sine", "offbin_sine"):
        cycles = bin_index + (0.25 if kind == "offbin_sine" else 0.0)
        samples = [amplitude * math.sin(2 * math.pi * cycles * j / n + phase_rad)
                   for j in range(n)]
    else:
        state = seed
        samples = []
        for _ in range(n):
            state = (1664525 * state + 1013904223) & 0xFFFFFFFF
            samples.append(amplitude * ((state / 2**32) * 2 - 1))
    if any(not math.isfinite(v) for v in samples):
        raise ValueError("generated fixture is not finite")
    planar = [samples]
    if channel_mode == "stereo_inphase":
        planar.append(list(samples))
    elif channel_mode == "stereo_antiphase":
        planar.append([-v for v in samples])
    return {
        "schema_version": 1,
        "kind": kind,
        "sample_rate_hz": sample_rate_hz,
        "origin_sample": origin_sample,
        "sample_count": n,
        "channel_mode": channel_mode,
        "planar_samples": planar,
        "parameters": {
            "amplitude": amplitude,
            "bin_index": bin_index,
            "phase_rad": phase_rad,
            "impulse_index": impulse_index,
            "seed_uint32": seed,
        },
        "provenance": "synthetic_deterministic_lcg_v1",
    }


def partition_contiguous(planar_samples: list[list[float]], origin_sample: int,
                         chunk_sizes: list[int]) -> list[dict]:
    """Partition without adding/removing samples; cycle requested positive sizes."""
    if not isinstance(origin_sample, int) or isinstance(origin_sample, bool) or origin_sample < 0:
        raise ValueError("origin_sample must be a nonnegative integer")
    if not planar_samples or not planar_samples[0]:
        raise ValueError("requires nonempty planar audio")
    n = len(planar_samples[0])
    if any(len(channel) != n or any(not math.isfinite(v) for v in channel)
           for channel in planar_samples):
        raise ValueError("channels must be equal length and finite")
    if not chunk_sizes:
        raise ValueError("chunk_sizes cannot be empty")
    for size in chunk_sizes:
        _positive_integer(size, "chunk size")
    chunks = []
    pos = 0
    index = 0
    while pos < n:
        size = min(chunk_sizes[index % len(chunk_sizes)], n - pos)
        chunks.append({
            "start_sample": origin_sample + pos,
            "planar_samples": [channel[pos:pos + size] for channel in planar_samples],
        })
        pos += size
        index += 1
    return chunks
