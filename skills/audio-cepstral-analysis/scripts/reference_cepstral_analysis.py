"""Offline real cepstrum and symmetric magnitude-envelope reference."""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from itertools import chain
import math

MAX_NFFT = 1024
MAX_SAMPLE_RATE = 384000
MAX_SAMPLE_INDEX = (1 << 256) - 1


def _integer(value: int, low: int, high: int, name: str) -> None:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in [{low}, {high}]")


def _nonnegative(value: float, name: str) -> float:
    if type(value) not in (int, float) or value < 0:
        raise ValueError(f"{name} must be finite and nonnegative")
    try:
        number = float(value)
    except OverflowError as error:
        raise ValueError(f"{name} must fit in binary64") from error
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite and nonnegative")
    return number


@dataclass(frozen=True)
class MagnitudeFrame:
    """Packed raw DFT magnitudes of one real, prepared analysis frame."""

    clock_id: str
    epoch_id: str
    source_tap: str
    channel: str
    amplitude_unit: str
    window_id: str
    sample_rate_hz: int
    window_samples: int
    nfft: int
    hop_samples: int
    start_sample: int
    magnitudes: tuple[float, ...]
    detrend: str = "none"

    def __post_init__(self) -> None:
        for name in ("clock_id", "epoch_id", "source_tap", "channel",
                     "amplitude_unit", "window_id", "detrend"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip() or len(value) > 128:
                raise ValueError(f"{name} must be a nonblank string of at most 128 characters")
        _integer(self.sample_rate_hz, 2, MAX_SAMPLE_RATE, "sample_rate_hz")
        _integer(self.nfft, 2, MAX_NFFT, "nfft")
        _integer(self.window_samples, 2, self.nfft, "window_samples")
        _integer(self.hop_samples, 1, MAX_NFFT, "hop_samples")
        _integer(self.start_sample, 0, MAX_SAMPLE_INDEX - self.window_samples, "start_sample")
        if not isinstance(self.magnitudes, tuple) or len(self.magnitudes) != self.nfft // 2 + 1:
            raise ValueError("magnitudes must be a tuple with nfft//2+1 bins")
        object.__setattr__(self, "magnitudes",
                           tuple(_nonnegative(value, "magnitude") for value in self.magnitudes))

    @property
    def end_sample_exclusive(self) -> int:
        return self.start_sample + self.window_samples

    @property
    def center_sample_twice(self) -> int:
        return 2 * self.start_sample + self.window_samples - 1


@dataclass(frozen=True)
class CepstrumResult:
    frame: MagnitudeFrame
    magnitude_reference: float
    relative_floor: float | None
    status: str
    coefficients: tuple[float, ...] | None = None
    floored_bins: tuple[int, ...] = ()
    log_floor: float | None = None
    _mean_relative_to_peak: float | None = field(default=None, repr=False)

    @property
    def floor_count(self) -> int:
        return len(self.floored_bins)

    @property
    def quefrency_seconds(self) -> tuple[float, ...]:
        return tuple(q / self.frame.sample_rate_hz for q in range(self.frame.nfft // 2 + 1))


@dataclass(frozen=True)
class EnvelopeResult:
    cepstrum: CepstrumResult
    cutoff: int
    status: str
    log_magnitudes: tuple[float, ...] | None = None
    magnitudes: tuple[float | None, ...] | None = None
    underflow_bins: tuple[int, ...] = ()
    overflow_bins: tuple[int, ...] = ()


def _log_ratio(numerator: float, denominator: float) -> float:
    if numerator >= denominator / 2 and denominator >= numerator / 2:
        return math.log1p((numerator - denominator) / denominator)
    return math.log(numerator) - math.log(denominator)


def _cosine(phase: int, nfft: int) -> float:
    phase = min(phase, nfft - phase)
    # Compute the complementary angle from the integer phase. This preserves
    # the exact quadrature zero and uses the same argument for opposite signs.
    return math.sin(math.pi * (nfft - 4 * phase) / (2 * nfft))


def _even_transform(values: tuple[float, ...], nfft: int) -> tuple[float, ...]:
    """Unnormalized cosine sum of an even sequence, returned on its packed side."""
    midpoint = values[-1] if nfft % 2 == 0 and len(values) == nfft // 2 + 1 else 0.0
    paired_stop = (nfft + 1) // 2
    pairs = tuple((index, 2 * value) for index, value in enumerate(values[1:paired_stop], 1)
                  if value != 0)
    cosines = tuple(_cosine(phase, nfft) for phase in range(nfft))
    transformed = []
    for k in range(nfft // 2 + 1):
        endpoint = -midpoint if k % 2 else midpoint
        pair_terms = (value * cosines[k * index % nfft] for index, value in pairs)
        transformed.append(math.fsum(chain((values[0], endpoint), pair_terms)))
    return tuple(transformed)


def real_cepstrum(
    frame: MagnitudeFrame, *, magnitude_reference: float, relative_floor: float | None = None,
) -> CepstrumResult:
    """Compute signed coefficients of an explicit-length, packed real cepstrum."""
    if not isinstance(frame, MagnitudeFrame):
        raise ValueError("expected one MagnitudeFrame")
    reference = _nonnegative(magnitude_reference, "magnitude reference")
    if reference == 0:
        raise ValueError("magnitude reference must be positive")
    if relative_floor is not None:
        relative_floor = _nonnegative(relative_floor, "relative floor")
        if not 0 < relative_floor < 1:
            raise ValueError("relative floor must be strictly between zero and one")

    peak = max(frame.magnitudes)
    if peak == 0:
        return CepstrumResult(frame, reference, relative_floor, "silent")
    if relative_floor is None and 0 in frame.magnitudes:
        return CepstrumResult(frame, reference, None, "spectral_null")

    log_peak = _log_ratio(peak, reference)
    floored_bins = []
    relative_logs = []
    log_floor_to_peak = None
    if relative_floor is not None:
        exact_floor = Fraction(peak) * Fraction(relative_floor)
        log_floor_to_peak = math.log(relative_floor)
    for index, value in enumerate(frame.magnitudes):
        if log_floor_to_peak is not None and Fraction(value) < exact_floor:
            relative_logs.append(log_floor_to_peak)
            floored_bins.append(index)
        else:
            relative_logs.append(_log_ratio(value, peak))

    # Keep the common log offset in c[0] to preserve small nonzero quefrencies.
    centered = tuple(value / frame.nfft for value in _even_transform(tuple(relative_logs), frame.nfft))
    coefficients = (math.fsum((log_peak, centered[0])), *centered[1:])
    log_floor = math.fsum((log_peak, log_floor_to_peak)) if log_floor_to_peak is not None else None
    return CepstrumResult(frame, reference, relative_floor, "ok", coefficients,
                          tuple(floored_bins), log_floor, centered[0])


def _positive_exp(value: float) -> float:
    try:
        return math.exp(value)
    except OverflowError:
        return math.inf


def spectral_envelope(cepstrum: CepstrumResult, *, cutoff: int) -> EnvelopeResult:
    """Apply a symmetric low-quefrency lifter and recover a magnitude envelope."""
    if not isinstance(cepstrum, CepstrumResult):
        raise ValueError("expected a real_cepstrum result")
    frame = cepstrum.frame
    _integer(cutoff, 0, frame.nfft // 2, "lifter cutoff")
    if cepstrum.status != "ok":
        return EnvelopeResult(cepstrum, cutoff, cepstrum.status)
    if cepstrum.coefficients is None or cepstrum._mean_relative_to_peak is None:
        raise ValueError("successful cepstrum requires coefficients and a relative mean")

    peak = max(frame.magnitudes)
    if cutoff == frame.nfft // 2:
        # The full lifter is the identity on the floor-processed spectrum.
        floored = set(cepstrum.floored_bins)
        floor = peak * cepstrum.relative_floor if cepstrum.relative_floor is not None else 0.0
        log_magnitudes = tuple(cepstrum.log_floor if k in floored
                               else _log_ratio(value, cepstrum.magnitude_reference)
                               for k, value in enumerate(frame.magnitudes))
        values = tuple(floor if k in floored else value for k, value in enumerate(frame.magnitudes))
    else:
        kept = (cepstrum._mean_relative_to_peak, *cepstrum.coefficients[1:cutoff+1])
        relative_logs = _even_transform(kept, frame.nfft)
        log_peak = _log_ratio(peak, cepstrum.magnitude_reference)
        log_magnitudes = tuple(math.fsum((log_peak, value)) for value in relative_logs)
        log_absolute_peak = math.log(peak)
        values = tuple(peak if value == 0 else _positive_exp(math.fsum((log_absolute_peak, value)))
                       for value in relative_logs)

    underflow = tuple(k for k, value in enumerate(values) if value == 0)
    overflow = tuple(k for k, value in enumerate(values) if math.isinf(value))
    magnitudes = tuple(value if value > 0 and math.isfinite(value) else None for value in values)
    status = "partial" if underflow or overflow else "ok"
    return EnvelopeResult(cepstrum, cutoff, status, log_magnitudes, magnitudes, underflow, overflow)
