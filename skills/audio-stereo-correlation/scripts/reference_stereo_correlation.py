"""Exact window moments and rounded measurements for aligned stereo PCM."""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from struct import pack, unpack
from typing import Literal

from reference_oscilloscope import CaptureWindow, ScopeEpoch


_MAX_FINITE_BITS = 0x7FEF_FFFF_FFFF_FFFF
_HALF_MINIMUM_SQUARED = Fraction(1, 2**2150)

CoefficientStatus = Literal[
    "both_zero_energy",
    "left_zero_energy",
    "right_zero_energy",
    "exact_zero",
    "rounded_to_zero",
    "exact_endpoint",
    "rounded_to_endpoint",
    "finite",
]


def _from_bits(bits: int) -> float:
    return unpack(">d", pack(">Q", bits))[0]


def _sqrt_binary64(square: Fraction) -> float:
    """Round a nonnegative root within binary64 range to nearest, ties to even."""
    if square <= _HALF_MINIMUM_SQUARED:
        return 0.0

    # Nonnegative finite binary64 values increase with their bit patterns.
    # Find the last representable value whose exact square fits.
    low = 0
    high = _MAX_FINITE_BITS
    while low < high:
        middle = (low + high + 1) // 2
        candidate = Fraction(_from_bits(middle))
        if candidate * candidate <= square:
            low = middle
        else:
            high = middle - 1

    lower = _from_bits(low)
    if low == _MAX_FINITE_BITS:
        return lower
    upper = _from_bits(low + 1)
    midpoint = (Fraction(lower) + Fraction(upper)) / 2
    boundary = midpoint * midpoint
    # Adjacent values have opposite low-bit parity, including at binade edges.
    if square > boundary or (square == boundary and low & 1):
        return upper
    return lower


@dataclass(frozen=True)
class WindowLevel:
    mean_square: Fraction
    rms: float

    @property
    def status(self) -> Literal["exact_zero", "rounded_to_zero", "finite"]:
        if self.mean_square == 0:
            return "exact_zero"
        if self.rms == 0:
            return "rounded_to_zero"
        return "finite"


@dataclass(frozen=True)
class StereoCorrelation:
    epoch: ScopeEpoch
    start_sample: int
    end_sample_exclusive: int
    left_channel: str
    right_channel: str
    left: WindowLevel
    right: WindowLevel
    mono: WindowLevel
    mean_cross_product: Fraction
    coefficient: float | None
    coefficient_status: CoefficientStatus
    mono_retention: Fraction | None
    estimator: Literal["raw_zero_lag"] = field(init=False, default="raw_zero_lag")

    @property
    def frame_count(self) -> int:
        return self.end_sample_exclusive - self.start_sample

    @property
    def center_sample_twice(self) -> int:
        return self.start_sample + self.end_sample_exclusive - 1


def _level(square_sum: Fraction, count: int) -> WindowLevel:
    power = square_sum / count
    return WindowLevel(power, _sqrt_binary64(power))


def _coefficient(
    left_squares: Fraction, right_squares: Fraction, cross: Fraction
) -> tuple[float | None, CoefficientStatus]:
    if left_squares == 0:
        return None, "left_zero_energy" if right_squares else "both_zero_energy"
    if right_squares == 0:
        return None, "right_zero_energy"
    if cross == 0:
        return 0.0, "exact_zero"

    square = cross * cross / (left_squares * right_squares)
    if square == 1:
        return (-1.0 if cross < 0 else 1.0), "exact_endpoint"
    magnitude = _sqrt_binary64(square)
    value = -magnitude if cross < 0 else magnitude
    if magnitude == 0:
        return value, "rounded_to_zero"
    if magnitude == 1:
        return value, "rounded_to_endpoint"
    return value, "finite"


def measure_stereo_correlation(
    capture: CaptureWindow, *, left_channel: str, right_channel: str
) -> StereoCorrelation:
    """Measure every pair in a capture, with DC retained and no level gate."""
    if type(capture) is not CaptureWindow:
        raise ValueError("stereo correlation requires a CaptureWindow")
    labels = capture.epoch.channel_ids
    if (type(left_channel) is not str or left_channel not in labels
            or type(right_channel) is not str or right_channel not in labels):
        raise ValueError("left and right must name channels in the capture")
    if left_channel == right_channel:
        raise ValueError("left and right channels must be distinct")

    left = capture.planes[labels.index(left_channel)]
    right = capture.planes[labels.index(right_channel)]
    left_squares = right_squares = cross = mono_squares = Fraction(0)
    for left_pcm, right_pcm in zip(left, right):
        l, r = Fraction(left_pcm), Fraction(right_pcm)
        mono = (l + r) / 2
        left_squares += l * l
        right_squares += r * r
        cross += l * r
        mono_squares += mono * mono

    count = capture.frame_count
    coefficient, status = _coefficient(left_squares, right_squares, cross)
    input_squares = left_squares + right_squares
    retention = 2 * mono_squares / input_squares if input_squares else None
    return StereoCorrelation(
        epoch=capture.epoch,
        start_sample=capture.start_sample,
        end_sample_exclusive=capture.end_sample_exclusive,
        left_channel=left_channel,
        right_channel=right_channel,
        left=_level(left_squares, count),
        right=_level(right_squares, count),
        mono=_level(mono_squares, count),
        mean_cross_product=cross / count,
        coefficient=coefficient,
        coefficient_status=status,
        mono_retention=retention,
    )
