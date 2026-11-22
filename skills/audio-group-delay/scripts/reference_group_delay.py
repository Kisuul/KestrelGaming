"""Offline group delay of a filter model or a qualified sampled transfer."""

from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction
from math import atan2, isfinite, tau
from typing import Literal, Union

from reference_phase_coherence import PhaseCoherenceAnalysis, _negative_root


Scalar = Union[int, float, Fraction]
ExactComplex = tuple[Fraction, Fraction]
MAX_COEFFICIENTS = 129
MAX_SECTIONS = 4
MAX_FREQUENCIES = 1024
MAX_MODEL_TERMS = 262_144
HALF_TURN = Fraction(1, 2)
TURN_RADIANS = Fraction(tau)
# Covers binary64 angle and rotation rounding in the observed-step comparison.
PHASE_ROUNDOFF_TURNS = Fraction(1, 2**48)

ModelStatus = Literal["valid", "numerator_zero", "denominator_zero", "common_zero", "below_polynomial_floor"]
SampledStatus = Literal[
    "valid", "unqualified_interval", "rejected_bin", "zero_response",
    "unresolved_branch", "phase_mismatch", "phase_underflow",
]


def _exact(value: Scalar, label: str) -> Fraction:
    if type(value) not in (int, float, Fraction) or (type(value) is float and not isfinite(value)):
        raise ValueError(f"{label} must be a finite real value")
    return Fraction(value)


def _positive_rate(value: Scalar) -> Fraction:
    rate = _exact(value, "sample rate")
    if rate <= 0:
        raise ValueError("sample rate must be positive")
    return rate


def _check_grid(hz: tuple[Fraction, ...], rate: Fraction) -> None:
    if (any(f < 0 or 2 * f > rate for f in hz)
            or any(a >= b for a, b in zip(hz, hz[1:]))):
        raise ValueError("frequencies must increase strictly from DC through Nyquist")


def _rotation(turns: Fraction) -> ExactComplex:
    """Return the represented negative-exponent rotation after exact reduction."""
    cycles = turns % 1
    return _negative_root(cycles.numerator, cycles.denominator)


@dataclass(frozen=True)
class RationalSection:
    numerator: tuple[Scalar, ...]
    denominator: tuple[Scalar, ...] = (1,)

    def __post_init__(self) -> None:
        for name in ("numerator", "denominator"):
            values = getattr(self, name)
            if type(values) not in (tuple, list) or not 1 <= len(values) <= MAX_COEFFICIENTS:
                raise ValueError("coefficient arrays must contain 1 to 129 values")
            object.__setattr__(self, name, tuple(_exact(x, name) for x in values))
        if not self.denominator[0]:
            raise ValueError("leading denominator coefficient must be nonzero")


@dataclass(frozen=True)
class ModelDelayPoint:
    frequency_hz: Fraction
    delay_samples: Fraction | None
    delay_seconds: Fraction | None
    status: ModelStatus


@dataclass(frozen=True)
class ModelGroupDelay:
    sample_rate_hz: Fraction
    sections: tuple[RationalSection, ...]
    bulk_delay_samples: int
    relative_polynomial_floor: Fraction
    points: tuple[ModelDelayPoint, ...]


def _polynomial_delay(
    coefficients: tuple[Scalar, ...], rotations: tuple[ExactComplex, ...],
) -> tuple[Fraction | None, Fraction]:
    real = imag = moment_real = moment_imag = Fraction(0)
    for index, (coefficient, (cosine, minus_sine)) in enumerate(zip(coefficients, rotations)):
        real_term, imag_term = coefficient * cosine, coefficient * minus_sine
        real += real_term
        imag += imag_term
        moment_real += index * real_term
        moment_imag += index * imag_term
    square = real * real + imag * imag
    result = (moment_real * real + moment_imag * imag) / square if square else None
    return result, square


def _model_point(
    frequency: Fraction, rate: Fraction, sections: tuple[RationalSection, ...],
    rotations: tuple[ExactComplex, ...], floors: tuple[tuple[Fraction, Fraction], ...],
    bulk_delay: int,
) -> ModelDelayPoint:
    delay = Fraction(bulk_delay)
    numerator_zero = denominator_zero = below_floor = False
    for section, (b_floor, a_floor) in zip(sections, floors):
        b, b_square = _polynomial_delay(section.numerator, rotations)
        a, a_square = _polynomial_delay(section.denominator, rotations)
        numerator_zero |= b is None
        denominator_zero |= a is None
        below_floor |= b_square < b_floor or a_square < a_floor
        if b is not None and a is not None:
            delay += b - a
    if numerator_zero and denominator_zero:
        status = "common_zero"
    elif numerator_zero:
        status = "numerator_zero"
    elif denominator_zero:
        status = "denominator_zero"
    elif below_floor:
        status = "below_polynomial_floor"
    else:
        return ModelDelayPoint(frequency, delay, delay / rate, "valid")
    return ModelDelayPoint(frequency, None, None, status)


def model_group_delay(
    sections: tuple[RationalSection, ...], frequencies_hz: tuple[Scalar, ...], *,
    sample_rate_hz: Scalar, bulk_delay_samples: int = 0, relative_polynomial_floor: Scalar = 0,
) -> ModelGroupDelay:
    """Evaluate the section derivatives for a model on one frequency grid."""
    if (type(sections) not in (tuple, list) or not 1 <= len(sections) <= MAX_SECTIONS
            or any(type(section) is not RationalSection for section in sections)):
        raise ValueError("provide 1 to 4 RationalSection values")
    if type(frequencies_hz) not in (tuple, list) or not 1 <= len(frequencies_hz) <= MAX_FREQUENCIES:
        raise ValueError("provide 1 to 1024 frequencies")
    if type(bulk_delay_samples) is not int or bulk_delay_samples < 0:
        raise ValueError("bulk delay must be a nonnegative integer sample count")
    rate = _positive_rate(sample_rate_hz)
    grid = tuple(_exact(f, "frequency") for f in frequencies_hz)
    _check_grid(grid, rate)
    floor = _exact(relative_polynomial_floor, "polynomial floor")
    if not 0 <= floor <= 1:
        raise ValueError("relative polynomial floor must be in [0, 1]")
    sections = tuple(sections)
    arrays = tuple(poly for section in sections for poly in (section.numerator, section.denominator))
    if len(grid) * sum(map(len, arrays)) > MAX_MODEL_TERMS:
        raise ValueError("model exceeds the coefficient-frequency work limit")
    longest = max(map(len, arrays))
    floors = tuple(
        ((floor * sum(map(abs, section.numerator)))**2, (floor * sum(map(abs, section.denominator)))**2)
        for section in sections
    )
    points = []
    for frequency in grid:
        rotations = tuple(_rotation(n * frequency / rate) for n in range(longest))
        points.append(_model_point(frequency, rate, sections, rotations, floors, bulk_delay_samples))
    return ModelGroupDelay(rate, sections, bulk_delay_samples, floor, tuple(points))


@dataclass(frozen=True)
class TransferSample:
    frequency_hz: Scalar
    real: Scalar
    imag: Scalar
    usable: bool = True

    def __post_init__(self) -> None:
        if type(self.usable) is not bool:
            raise ValueError("sample validity must be boolean")
        for name in ("frequency_hz", "real", "imag"):
            object.__setattr__(self, name, _exact(getattr(self, name), name))


@dataclass(frozen=True)
class SlopeProfile:
    sample_rate_hz: Scalar
    residual_bound_samples: Scalar | None
    phase_margin_turns: Scalar = 0
    aperture_steps: int = 1
    input_advance_samples: Scalar = 0
    fit_advance_samples: Scalar = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "sample_rate_hz", _positive_rate(self.sample_rate_hz))
        if self.residual_bound_samples is not None:
            bound = _exact(self.residual_bound_samples, "residual bound")
            if bound < 0:
                raise ValueError("residual bound must be nonnegative")
            object.__setattr__(self, "residual_bound_samples", bound)
        for name in ("phase_margin_turns", "input_advance_samples", "fit_advance_samples"):
            object.__setattr__(self, name, _exact(getattr(self, name), name))
        if not 0 <= self.phase_margin_turns < HALF_TURN:
            raise ValueError("phase margin must be nonnegative and less than half a turn")
        if type(self.aperture_steps) is not int or not 1 <= self.aperture_steps < MAX_FREQUENCIES:
            raise ValueError("aperture steps must be an integer from 1 to 1023")


@dataclass(frozen=True)
class TransferProvenance:
    reference_tap: str
    measurement_tap: str
    clock_domain: str
    epoch_id: str
    reference_interval: tuple[int, int]
    measurement_interval: tuple[int, int]

    def __post_init__(self) -> None:
        labels = (self.reference_tap, self.measurement_tap, self.clock_domain, self.epoch_id)
        if any(type(x) is not str or not x.strip() for x in labels):
            raise ValueError("tap, clock, and epoch labels must be nonempty strings")
        for interval in (self.reference_interval, self.measurement_interval):
            if (type(interval) is not tuple or len(interval) != 2
                    or any(type(x) is not int for x in interval) or not 0 <= interval[0] < interval[1]):
                raise ValueError("original sample intervals must be nonempty and half-open")


@dataclass(frozen=True)
class PhaseIncrement:
    residual_turns: Fraction | None
    status: SampledStatus


@dataclass(frozen=True)
class SampledDelayPoint:
    frequency_hz: Fraction
    low_hz: Fraction
    high_hz: Fraction
    residual_delay_samples: Fraction | None
    delay_samples: Fraction | None
    delay_seconds: Fraction | None
    status: SampledStatus
    first_failed_edge: int | None

    @property
    def aperture_hz(self) -> Fraction:
        return self.high_hz - self.low_hz


@dataclass(frozen=True)
class WelchQuality:
    minimum_coherence: Scalar = 0
    reference_density_floor: Scalar = 0
    measurement_density_floor: Scalar = 0

    def __post_init__(self) -> None:
        for name in ("minimum_coherence", "reference_density_floor", "measurement_density_floor"):
            value = _exact(getattr(self, name), name)
            if value < 0 or (name == "minimum_coherence" and value > 1):
                raise ValueError("coherence must be in [0, 1] and density floors must be nonnegative")
            object.__setattr__(self, name, value)


@dataclass(frozen=True)
class SampledGroupDelay:
    samples: tuple[TransferSample, ...]
    supported_edges: tuple[bool, ...]
    profile: SlopeProfile
    increments: tuple[PhaseIncrement, ...]
    points: tuple[SampledDelayPoint, ...]
    provenance: TransferProvenance | None
    welch: PhaseCoherenceAnalysis | None = None
    quality: WelchQuality | None = None


def _adjacent_increment(
    left: TransferSample, right: TransferSample, supported: bool, profile: SlopeProfile,
) -> PhaseIncrement:
    if not supported:
        return PhaseIncrement(None, "unqualified_interval")
    if not (left.usable and right.usable):
        return PhaseIncrement(None, "rejected_bin")
    if not ((left.real or left.imag) and (right.real or right.imag)):
        return PhaseIncrement(None, "zero_response")
    width = (right.frequency_hz - left.frequency_hz) / profile.sample_rate_hz
    bound = profile.residual_bound_samples
    if bound is None:
        return PhaseIncrement(None, "unresolved_branch")
    allowed = bound * width + profile.phase_margin_turns
    if allowed >= HALF_TURN:
        return PhaseIncrement(None, "unresolved_branch")

    re = right.real * left.real + right.imag * left.imag
    im = right.imag * left.real - right.real * left.imag
    if profile.fit_advance_samples:
        cosine, sine = _rotation(-profile.fit_advance_samples * width)
        re, im = re * cosine - im * sine, re * sine + im * cosine
    scale = max(abs(re), abs(im))
    angle = atan2(float(im / scale), float(re / scale))
    if angle == 0 and im:
        return PhaseIncrement(None, "phase_underflow")
    turns = Fraction(angle) / TURN_RADIANS
    if abs(turns) >= HALF_TURN:
        return PhaseIncrement(None, "unresolved_branch")
    if abs(turns) > allowed + PHASE_ROUNDOFF_TURNS:
        return PhaseIncrement(None, "phase_mismatch")
    return PhaseIncrement(turns, "valid")


def _aperture_point(
    grid: tuple[Scalar, ...], steps: tuple[PhaseIncrement, ...], start: int, profile: SlopeProfile,
) -> SampledDelayPoint:
    end = start + profile.aperture_steps
    low, high = grid[start], grid[end]
    center = (low + high) / 2
    turns = Fraction(0)
    for index in range(start, end):
        step = steps[index]
        if step.residual_turns is None:
            return SampledDelayPoint(center, low, high, None, None, None, step.status, index)
        turns += step.residual_turns
    residual = -turns * profile.sample_rate_hz / (high - low)
    delay = residual + profile.input_advance_samples + profile.fit_advance_samples
    return SampledDelayPoint(center, low, high, residual, delay, delay / profile.sample_rate_hz, "valid", None)


def sampled_group_delay(
    samples: tuple[TransferSample, ...], profile: SlopeProfile, *,
    supported_edges: tuple[bool, ...], provenance: TransferProvenance | None = None,
) -> SampledGroupDelay:
    """Measure aperture secants from adjacent phase increments on qualified intervals."""
    if type(profile) is not SlopeProfile:
        raise ValueError("sampled group delay requires a SlopeProfile")
    if (type(samples) not in (tuple, list) or len(samples) > MAX_FREQUENCIES
            or any(type(sample) is not TransferSample for sample in samples)):
        raise ValueError("provide up to 1024 TransferSample values")
    if (type(supported_edges) not in (tuple, list)
            or len(supported_edges) != max(0, len(samples) - 1)
            or any(type(edge) is not bool for edge in supported_edges)):
        raise ValueError("provide one boolean continuity decision for each adjacent interval")
    if provenance is not None and type(provenance) is not TransferProvenance:
        raise ValueError("provenance must be a TransferProvenance")
    samples = tuple(samples)
    grid = tuple(sample.frequency_hz for sample in samples)
    _check_grid(grid, profile.sample_rate_hz)
    supported_edges = tuple(supported_edges)
    increments = tuple(
        _adjacent_increment(a, b, supported, profile)
        for a, b, supported in zip(samples, samples[1:], supported_edges)
    )
    points = tuple(
        _aperture_point(grid, increments, start, profile)
        for start in range(len(samples) - profile.aperture_steps)
    )
    return SampledGroupDelay(samples, supported_edges, profile, increments, points, provenance)


def welch_group_delay(
    analysis: PhaseCoherenceAnalysis, profile: SlopeProfile, *,
    supported_edges: tuple[bool, ...], quality: WelchQuality = WelchQuality(),
    provenance: TransferProvenance | None = None,
) -> SampledGroupDelay:
    """Use H1 from the shared paired Welch analysis and retain its capture support."""
    if (type(analysis) is not PhaseCoherenceAnalysis or type(profile) is not SlopeProfile
            or type(quality) is not WelchQuality):
        raise ValueError("Welch group delay requires paired Welch analysis, slope profile, and quality gates")
    if analysis.epoch.rate_hz != profile.sample_rate_hz:
        raise ValueError("slope profile must use the Welch sample rate")
    if provenance is not None and (
        type(provenance) is not TransferProvenance
        or (provenance.clock_domain, provenance.epoch_id) != (analysis.epoch.clock_domain, analysis.epoch.epoch_id)
    ):
        raise ValueError("original sample intervals must use the Welch clock domain and epoch")
    samples = []
    for bin_value in analysis.bins:
        level = bin_value.reference_density
        coherence = bin_value.magnitude_squared_coherence
        usable = (
            level > 0 and bin_value.measurement_density > 0
            and level >= quality.reference_density_floor
            and bin_value.measurement_density >= quality.measurement_density_floor
            and coherence is not None and coherence >= quality.minimum_coherence
        )
        real = bin_value.cross_density_real / level if level else 0
        imag = bin_value.cross_density_imag / level if level else 0
        samples.append(TransferSample(bin_value.frequency_hz, real, imag, usable))
    result = sampled_group_delay(samples, profile, supported_edges=supported_edges, provenance=provenance)
    return replace(result, welch=analysis, quality=quality)
