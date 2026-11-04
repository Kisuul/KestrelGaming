"""Pure-Python reference for sample-peak and rolling peak-window fixtures.

Explicit sample time, deterministic ties, no inferred clipping or true peak.
Clarity over performance; NOT suitable for realtime audio callbacks.
"""
from __future__ import annotations

from collections import deque
import math


def amplitude_level_db(peak: float, reference: float = 1.0) -> float:
    """20 log10(peak/reference); zero maps to -inf, not a display floor."""
    if not math.isfinite(reference) or reference <= 0:
        raise ValueError("reference must be finite and positive")
    if not math.isfinite(peak) or peak < 0:
        raise ValueError("peak must be finite and nonnegative")
    return -math.inf if peak == 0 else 20 * math.log10(peak / reference)


def scan_peak(samples: list[float], start_sample: int = 0,
              reference: float = 1.0) -> dict:
    """One channel, finite nonempty block; earliest tie wins."""
    if not isinstance(start_sample, int) or isinstance(start_sample, bool) or start_sample < 0:
        raise ValueError("start_sample must be a nonnegative integer")
    if not math.isfinite(reference) or reference <= 0:
        raise ValueError("reference must be finite and positive")
    if not samples or any(not math.isfinite(value) for value in samples):
        raise ValueError("samples must be nonempty and finite")

    best_index = 0
    best_value = samples[0]
    for j, value in enumerate(samples[1:], start=1):
        if abs(value) > abs(best_value):
            best_value = value
            best_index = j
    magnitude = abs(best_value)
    return {
        "peak": magnitude,
        "at_sample": start_sample + best_index,
        "signed_value": best_value,
        "level_db_re_reference": amplitude_level_db(magnitude, reference),
        "reference_hits": sum(abs(x) >= reference for x in samples),
        "strict_reference_exceedances": sum(abs(x) > reference for x in samples),
    }


class RollingPeakMeter:
    """Per-channel program peak and rolling last-H-samples peak, contiguous audio.

    Every update is planar data [channel][sample]. Returned per-channel block
    peaks are scoped to the *current update*; program/held peaks span updates.
    Rolling maxima use amortized O(1) monotonic deques per sample per channel.
    """

    def __init__(self, channels: int, hold_samples: int,
                 reference: float = 1.0, sample_rate_hz: float = 48000.0):
        if not isinstance(channels, int) or isinstance(channels, bool) or channels < 1:
            raise ValueError("channels must be a positive integer")
        if not isinstance(hold_samples, int) or isinstance(hold_samples, bool) or hold_samples < 1:
            raise ValueError("hold_samples must be a positive integer")
        if not math.isfinite(reference) or reference <= 0:
            raise ValueError("reference must be finite and positive")
        if not math.isfinite(sample_rate_hz) or sample_rate_hz <= 0:
            raise ValueError("sample rate must be finite and positive")
        self.channels = channels
        self.hold_samples = hold_samples
        self.reference = reference
        self.sample_rate_hz = sample_rate_hz
        self.reset()

    def reset(self) -> None:
        """Begin a new epoch; caller must explicitly signal seeks/gaps/changes."""
        self._next_sample = None
        self._queues = [deque() for _ in range(self.channels)]
        self._program = [None] * self.channels

    def update(self, planar: list[list[float]], start_sample: int) -> dict:
        """Apply one contiguous equal-size multichannel block atomically after validation."""
        if not isinstance(start_sample, int) or isinstance(start_sample, bool) or start_sample < 0:
            raise ValueError("start_sample must be a nonnegative integer")
        if self._next_sample is not None and start_sample != self._next_sample:
            raise ValueError("sample discontinuity; reset before starting new epoch")
        if len(planar) != self.channels:
            raise ValueError("channel count does not match meter")
        counts = [len(channel) for channel in planar]
        if not counts or counts[0] == 0 or any(n != counts[0] for n in counts):
            raise ValueError("all channels require equal nonzero sample counts")

        # A validation pass for ALL channels precedes any state mutation.
        blocks = [
            scan_peak(channel, start_sample=start_sample, reference=self.reference)
            for channel in planar
        ]
        length = counts[0]
        out = []
        for index, channel in enumerate(planar):
            queue = self._queues[index]
            old_program = self._program[index]
            block = blocks[index]
            if old_program is None or block["peak"] > old_program["peak"]:
                self._program[index] = {
                    "peak": block["peak"], "at_sample": block["at_sample"],
                    "signed_value": block["signed_value"]
                }
            for j, value in enumerate(channel):
                when = start_sample + j
                magnitude = abs(value)
                # Only strictly smaller entries can be discarded: ties favor earliest.
                while queue and queue[-1][1] < magnitude:
                    queue.pop()
                queue.append((when, magnitude, value))
                expiration = when - self.hold_samples
                while queue and queue[0][0] <= expiration:
                    queue.popleft()
            held = queue[0]
            out.append({
                "block": block,
                "program_peak": dict(self._program[index]),
                "rolling_peak": {
                    "peak": held[1], "at_sample": held[0],
                    "signed_value": held[2],
                    "level_db_re_reference": amplitude_level_db(held[1], self.reference),
                },
            })
        self._next_sample = start_sample + length
        return {
            "start_sample": start_sample,
            "end_sample_exclusive": self._next_sample,
            "sample_rate_hz": self.sample_rate_hz,
            "hold_samples": self.hold_samples,
            "channels": out,
        }
