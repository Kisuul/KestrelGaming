"""Project aligned PCM pairs onto a linear, orthonormal vectorscope."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, DivisionByZero, InvalidOperation, Overflow, ROUND_HALF_EVEN
from fractions import Fraction
from math import isfinite
from sys import float_info

from reference_oscilloscope import CaptureWindow, ScopeEpoch


_MAX_AXIS_NUMERATOR_SQUARED = 2 * int(float_info.max) ** 2


@dataclass(frozen=True)
class VectorscopeViewport:
    """Continuous screen geometry, with rows increasing downward."""

    center_x: int | float
    center_y: int | float
    half_width: int | float
    half_height: int | float
    nominal_full_scale: int | float

    def __post_init__(self) -> None:
        fields = (
            ("center_x", self.center_x), ("center_y", self.center_y),
            ("half_width", self.half_width), ("half_height", self.half_height),
            ("nominal_full_scale", self.nominal_full_scale),
        )
        for name, value in fields:
            if type(value) is not int and (type(value) is not float or not isfinite(value)):
                raise ValueError(f"{name} must be a finite float or integer")
        if min(self.half_width, self.half_height, self.nominal_full_scale) <= 0:
            raise ValueError("half-extents and nominal full scale must be positive")


@dataclass(frozen=True)
class VectorscopePoint:
    sample_index: int
    x: float
    y: float


@dataclass(frozen=True)
class ViewportPoint:
    sample_index: int
    pixel_x: Fraction
    pixel_y: Fraction
    over_nominal: bool
    out_of_view: bool


@dataclass(frozen=True)
class VectorscopeFrame:
    epoch: ScopeEpoch
    start_sample: int
    end_sample_exclusive: int
    left_channel: str
    right_channel: str
    points: tuple[VectorscopePoint, ...]
    viewport: VectorscopeViewport | None
    view_points: tuple[ViewportPoint, ...]


def _channel_index(epoch: ScopeEpoch, label: str, side: str) -> int:
    if type(label) is not str or label not in epoch.channel_ids:
        raise ValueError(f"{side} channel must name a channel in the capture")
    return epoch.channel_ids.index(label)


def _coordinate(
    numerator: Fraction, index: int, axis: str, context: Context, scale: Decimal
) -> float:
    if numerator * numerator > _MAX_AXIS_NUMERATOR_SQUARED:
        raise ValueError(f"{axis} axis exceeds finite binary64 range at sample {index}")
    amplitude = context.divide(numerator.numerator, numerator.denominator)
    return float(context.divide(amplitude, scale))


def project_vectorscope(
    capture: CaptureWindow,
    *,
    left_channel: str,
    right_channel: str,
    viewport: VectorscopeViewport | None = None,
) -> VectorscopeFrame:
    """Return one point per measured pair and optional pre-raster view points."""
    if type(capture) is not CaptureWindow:
        raise ValueError("vectorscope requires a CaptureWindow")
    left_plane = _channel_index(capture.epoch, left_channel, "left")
    right_plane = _channel_index(capture.epoch, right_channel, "right")
    if left_plane == right_plane:
        raise ValueError("left and right channels must be distinct")
    if viewport is not None:
        if type(viewport) is not VectorscopeViewport:
            raise ValueError("viewport must be a VectorscopeViewport")
        center_x, center_y = Fraction(viewport.center_x), Fraction(viewport.center_y)
        half_width, half_height = Fraction(viewport.half_width), Fraction(viewport.half_height)
        nominal = Fraction(viewport.nominal_full_scale)
        pixel_factor = min(half_width, half_height) / (2 * nominal)

    context = Context(
        prec=80, rounding=ROUND_HALF_EVEN, Emin=-999, Emax=999, clamp=0,
        traps=[InvalidOperation, DivisionByZero, Overflow],
    )
    scale = context.sqrt(2)
    points = []
    view_points = []
    samples = zip(capture.planes[left_plane], capture.planes[right_plane])
    for index, (left, right) in enumerate(samples, capture.start_sample):
        l, r = Fraction(left), Fraction(right)
        horizontal = r - l
        vertical = l + r
        x = _coordinate(horizontal, index, "x", context, scale)
        y = _coordinate(vertical, index, "y", context, scale)
        points.append(VectorscopePoint(index, x, y))
        if viewport is not None:
            # Use exact unrotated numerators so view fit cancels the square roots.
            dx = pixel_factor * horizontal
            dy = -pixel_factor * vertical
            view_points.append(ViewportPoint(
                sample_index=index,
                pixel_x=center_x + dx,
                pixel_y=center_y + dy,
                over_nominal=abs(l) > nominal or abs(r) > nominal,
                out_of_view=abs(dx) > half_width or abs(dy) > half_height,
            ))

    return VectorscopeFrame(
        epoch=capture.epoch,
        start_sample=capture.start_sample,
        end_sample_exclusive=capture.end_sample_exclusive,
        left_channel=left_channel,
        right_channel=right_channel,
        points=tuple(points),
        viewport=viewport,
        view_points=tuple(view_points),
    )
