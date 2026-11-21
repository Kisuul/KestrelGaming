"""Measure half-gain Mid and Side from a shared PCM capture."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import isqrt, ldexp
from typing import Literal

from reference_oscilloscope import CaptureWindow, ScopeEpoch


def _rms_binary64(power: Fraction) -> float:
    """Round the square root of an exact mean square to nearest, ties to even."""
    if power == 0:
        return 0.0

    # Find the power binade, then use the spacing of the root's binary64 binade.
    two = Fraction(2)
    exponent = power.numerator.bit_length() - power.denominator.bit_length()
    if power < two**exponent:
        exponent -= 1
    spacing_exponent = max(-1074, exponent // 2 - 52)

    # Work in units of that spacing. Compare the exact squared midpoint.
    scaled_square = power / two**(2 * spacing_exponent)
    significand = isqrt(scaled_square.numerator // scaled_square.denominator)
    midpoint_squared = Fraction((2 * significand + 1)**2, 4)
    if scaled_square > midpoint_squared or (scaled_square == midpoint_squared and significand & 1):
        significand += 1
    return ldexp(significand, spacing_exponent)


@dataclass(frozen=True)
class MidSideComponent:
    samples: tuple[Fraction, ...]
    mean_square: Fraction
    rms: float

    @property
    def rms_status(self) -> Literal["exact_zero", "rounded_to_zero", "finite"]:
        if self.mean_square == 0:
            return "exact_zero"
        if self.rms == 0:
            return "rounded_to_zero"
        return "finite"


@dataclass(frozen=True)
class MidSideAnalysis:
    epoch: ScopeEpoch
    start_sample: int
    end_sample_exclusive: int
    left_channel: str
    right_channel: str
    mid: MidSideComponent
    side: MidSideComponent
    side_power_fraction: Fraction | None

    @property
    def frame_count(self) -> int:
        return self.end_sample_exclusive - self.start_sample

    @property
    def center_sample_twice(self) -> int:
        return self.start_sample + self.end_sample_exclusive - 1


def _measure_component(samples: list[Fraction]) -> MidSideComponent:
    power = sum(sample * sample for sample in samples) / len(samples)
    return MidSideComponent(tuple(samples), power, _rms_binary64(power))


def analyze_mid_side(
    capture: CaptureWindow, *, left_channel: str, right_channel: str
) -> MidSideAnalysis:
    """Return exact component waveforms and window powers, with binary64 RMS."""
    if type(capture) is not CaptureWindow:
        raise ValueError("Mid/Side analysis requires a CaptureWindow")
    labels = capture.epoch.channel_ids
    if (type(left_channel) is not str or left_channel not in labels
            or type(right_channel) is not str or right_channel not in labels):
        raise ValueError("left and right must name channels in the capture")
    if left_channel == right_channel:
        raise ValueError("left and right channels must be distinct")

    left = capture.planes[labels.index(left_channel)]
    right = capture.planes[labels.index(right_channel)]
    mid_samples = []
    side_samples = []
    for left_pcm, right_pcm in zip(left, right):
        left_sample = Fraction(left_pcm)
        right_sample = Fraction(right_pcm)
        mid_samples.append((left_sample + right_sample) / 2)
        side_samples.append((left_sample - right_sample) / 2)

    mid = _measure_component(mid_samples)
    side = _measure_component(side_samples)
    total_power = mid.mean_square + side.mean_square
    side_fraction = side.mean_square / total_power if total_power else None
    return MidSideAnalysis(
        epoch=capture.epoch,
        start_sample=capture.start_sample,
        end_sample_exclusive=capture.end_sample_exclusive,
        left_channel=left_channel,
        right_channel=right_channel,
        mid=mid,
        side=side,
        side_power_fraction=side_fraction,
    )
