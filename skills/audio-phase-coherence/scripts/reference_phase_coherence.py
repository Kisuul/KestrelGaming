"""Bounded offline Welch phase and coherence from one aligned PCM capture."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import atan2, cos, isfinite, pi, sin, sqrt
from typing import Literal

from reference_oscilloscope import CaptureWindow, ScopeEpoch


MAX_TRANSFORM_LENGTH = 1024
MAX_SAMPLE_BIN_TERMS = 262_144  # Per channel, across the complete segments.
ExactComplex = tuple[Fraction, Fraction]


@dataclass(frozen=True)
class WelchProfile:
    window: tuple[float, ...]
    hop: int
    fft_length: int
    detrend: Literal["none", "mean"] = "none"

    def __post_init__(self) -> None:
        if type(self.window) not in (list, tuple) or not 2 <= len(self.window) <= MAX_TRANSFORM_LENGTH:
            raise ValueError("window must have 2 to 1024 coefficients")
        if any(type(w) not in (int, float) for w in self.window):
            raise ValueError("window coefficients must be real numbers")
        try:
            coefficients = tuple(float(w) for w in self.window)
        except OverflowError:
            raise ValueError("window coefficients must be finite binary64 values") from None
        if not all(map(isfinite, coefficients)) or not any(coefficients):
            raise ValueError("window must have finite coefficients and positive energy")
        if type(self.hop) is not int or not 1 <= self.hop <= len(coefficients):
            raise ValueError("hop must be an integer from 1 to the window length")
        if type(self.fft_length) is not int or not len(coefficients) <= self.fft_length <= MAX_TRANSFORM_LENGTH:
            raise ValueError("DFT length must be an integer from the window length to 1024")
        if type(self.detrend) is not str or self.detrend not in ("none", "mean"):
            raise ValueError("detrend must be 'none' or 'mean'")
        object.__setattr__(self, "window", coefficients)


@dataclass(frozen=True)
class PhaseCoherenceBin:
    index: int
    frequency_hz: Fraction
    reference_density: Fraction
    measurement_density: Fraction
    cross_density_real: Fraction
    cross_density_imag: Fraction
    magnitude_squared_coherence: Fraction | None
    phase_radians: float | None
    energized_pairs: int

    @property
    def status(self) -> Literal["zero_auto_power", "zero_cross_density", "defined"]:
        if self.magnitude_squared_coherence is None:
            return "zero_auto_power"
        if self.phase_radians is None:
            return "zero_cross_density"
        return "defined"


@dataclass(frozen=True)
class PhaseCoherenceAnalysis:
    epoch: ScopeEpoch
    start_sample: int
    end_sample_exclusive: int
    profile: WelchProfile
    reference_channel: str
    measurement_channel: str
    segment_starts: tuple[int, ...]
    bins: tuple[PhaseCoherenceBin, ...]

    @property
    def segment_count(self) -> int:
        return len(self.segment_starts)

    @property
    def warming_up(self) -> bool:
        return self.segment_count < 2

    @property
    def used_end_sample_exclusive(self) -> int | None:
        if not self.segment_starts:
            return None
        return self.segment_starts[-1] + len(self.profile.window)


def _negative_root(turn: int, length: int) -> ExactComplex:
    """Represent a DFT root with exact axes and quadrant symmetries."""
    quadrant, offset = divmod(4 * turn, length)
    # Evaluate in the first octant. Swap coordinates for the second octant.
    mirrored = 2 * offset > length
    acute = min(offset, length - offset)
    if acute == 0:
        cosine, sine = 1.0, 0.0
    elif 2 * acute == length:
        cosine = sine = sqrt(0.5)
    else:
        angle = (pi / 2) * (acute / length)
        cosine, sine = cos(angle), sin(angle)
    if mirrored:
        cosine, sine = sine, cosine
    real, imag = ((cosine, -sine), (-sine, -cosine), (-cosine, sine), (sine, cosine))[quadrant]
    return Fraction(real), Fraction(imag)


def _tapered_segments(
    plane: tuple[int | float, ...], offsets: range, taper: tuple[Fraction, ...], subtract_mean: bool,
) -> tuple[tuple[Fraction, ...], ...]:
    size = len(taper)
    samples = tuple(Fraction(value) for value in plane[:offsets[-1] + size])
    segments = []
    for offset in offsets:
        segment = samples[offset:offset + size]
        mean = sum(segment) / size if subtract_mean else 0
        segments.append(tuple((value - mean) * weight for value, weight in zip(segment, taper)))
    return tuple(segments)


def _dft_bin(segment: tuple[Fraction, ...], weights: tuple[ExactComplex, ...]) -> ExactComplex:
    real = sum(sample * weight[0] for sample, weight in zip(segment, weights))
    imag = sum(sample * weight[1] for sample, weight in zip(segment, weights))
    return real, imag


def _measure_bin(
    index: int, frequency_hz: Fraction, density_scale: Fraction,
    reference: tuple[tuple[Fraction, ...], ...], measurement: tuple[tuple[Fraction, ...], ...],
    weights: tuple[ExactComplex, ...],
) -> PhaseCoherenceBin:
    reference_power = measurement_power = cross_real = cross_imag = Fraction(0)
    energized_pairs = 0
    for a, b in zip(reference, measurement):
        xr, xi = _dft_bin(a, weights)
        yr, yi = _dft_bin(b, weights)
        reference_power += xr * xr + xi * xi
        measurement_power += yr * yr + yi * yi
        cross_real += xr * yr + xi * yi
        cross_imag += xr * yi - xi * yr
        if (xr or xi) and (yr or yi):
            energized_pairs += 1

    coherence: Fraction | None = None
    phase: float | None = None
    if reference_power and measurement_power:
        coherence = (cross_real**2 + cross_imag**2) / (reference_power * measurement_power)
        if coherence:
            scale = max(abs(cross_real), abs(cross_imag))
            phase = atan2(float(cross_imag / scale), float(cross_real / scale))
            if phase == -pi:
                phase = pi
    return PhaseCoherenceBin(
        index, frequency_hz,
        reference_power * density_scale, measurement_power * density_scale,
        cross_real * density_scale, cross_imag * density_scale,
        coherence, phase, energized_pairs,
    )


def analyze_phase_coherence(
    capture: CaptureWindow, profile: WelchProfile, *, reference_channel: str, measurement_channel: str,
) -> PhaseCoherenceAnalysis:
    """Pool paired Welch products and return their density, coherence, and phase."""
    if type(capture) is not CaptureWindow or type(profile) is not WelchProfile:
        raise ValueError("phase and coherence require a CaptureWindow and WelchProfile")
    labels = capture.epoch.channel_ids
    if (type(reference_channel) is not str or reference_channel not in labels
            or type(measurement_channel) is not str or measurement_channel not in labels):
        raise ValueError("reference and measurement must name channels in the capture")
    if reference_channel == measurement_channel:
        raise ValueError("reference and measurement channels must be distinct")

    size, length = len(profile.window), profile.fft_length
    offsets = range(0, capture.frame_count - size + 1, profile.hop)
    bins = []
    if len(offsets) >= 2:
        bin_count = length // 2 + 1
        if len(offsets) * size * bin_count > MAX_SAMPLE_BIN_TERMS:
            raise ValueError("profile exceeds the offline sample-bin work limit")
        taper = tuple(Fraction(weight) for weight in profile.window)
        exact_rate = capture.epoch.rate_hz
        density_scale = 1 / (exact_rate * sum(w * w for w in taper) * len(offsets))
        subtract_mean = profile.detrend == "mean"
        reference = _tapered_segments(capture.planes[labels.index(reference_channel)], offsets, taper, subtract_mean)
        measurement = _tapered_segments(capture.planes[labels.index(measurement_channel)], offsets, taper, subtract_mean)
        roots = tuple(_negative_root(turn, length) for turn in range(length))
        for index in range(bin_count):
            single = index == 0 or 2 * index == length
            weights = tuple(roots[(index * sample) % length] for sample in range(size))
            bins.append(_measure_bin(
                index, exact_rate * index / length, density_scale * (1 if single else 2),
                reference, measurement, weights,
            ))
    return PhaseCoherenceAnalysis(
        capture.epoch, capture.start_sample, capture.end_sample_exclusive, profile,
        reference_channel, measurement_channel, tuple(capture.start_sample + i for i in offsets), tuple(bins),
    )
