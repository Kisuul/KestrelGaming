"""Bounded integer-lag cross-correlation on sample-clocked PCM captures."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import isfinite
from typing import Literal

from reference_oscilloscope import CaptureWindow, ScopeEpoch
from reference_stereo_correlation import _sqrt_binary64


ScoreMode = Literal["raw", "mean_product", "cosine", "pearson"]
PeakRule = Literal["positive", "absolute"]
Eligibility = Literal["eligible", "insufficient_pairs", "zero_power", "below_level"]
SampleBounds = tuple[int, int]


def _power_floor(value: int | float | Fraction) -> Fraction:
    if type(value) not in (int, float, Fraction):
        raise ValueError("level floors must be nonnegative finite real powers")
    if (type(value) is float and not isfinite(value)) or value < 0:
        raise ValueError("level floors must be nonnegative finite real powers")
    return Fraction(value)


@dataclass(frozen=True)
class LagProfile:
    delay_bounds: SampleBounds
    minimum_pairs: int
    score_mode: ScoreMode = "raw"
    peak_rule: PeakRule = "positive"
    reference_power_floor: int | float | Fraction = 0
    measurement_power_floor: int | float | Fraction = 0

    def __post_init__(self) -> None:
        bounds = self.delay_bounds
        if (type(bounds) is not tuple or len(bounds) != 2
                or any(type(edge) is not int for edge in bounds) or bounds[0] > bounds[1]):
            raise ValueError("delay bounds must be two ordered inclusive integer sample delays")
        if type(self.minimum_pairs) is not int or self.minimum_pairs < 1:
            raise ValueError("minimum_pairs must be a positive integer")
        if type(self.score_mode) is not str or self.score_mode not in ("raw", "mean_product", "cosine", "pearson"):
            raise ValueError("invalid score mode")
        if type(self.peak_rule) is not str or self.peak_rule not in ("positive", "absolute"):
            raise ValueError("invalid peak rule")
        object.__setattr__(self, "reference_power_floor", _power_floor(self.reference_power_floor))
        object.__setattr__(self, "measurement_power_floor", _power_floor(self.measurement_power_floor))


@dataclass(frozen=True)
class LagScore:
    """An exact score key. Normalized keys carry the signed squared ratio."""

    rank_value: Fraction
    normalized: bool

    @property
    def sign(self) -> int:
        return (self.rank_value > 0) - (self.rank_value < 0)

    @property
    def value(self) -> Fraction | float:
        if not self.normalized:
            return self.rank_value
        magnitude = _sqrt_binary64(abs(self.rank_value))
        return -magnitude if self.rank_value < 0 else magnitude

    @property
    def status(self) -> Literal["exact", "exact_zero", "exact_endpoint", "rounded_to_zero", "rounded_to_endpoint", "finite"]:
        if not self.normalized:
            return "exact"
        magnitude = abs(self.rank_value)
        if magnitude == 0:
            return "exact_zero"
        if magnitude == 1:
            return "exact_endpoint"
        rounded = abs(self.value)
        if rounded == 0:
            return "rounded_to_zero"
        if rounded == 1:
            return "rounded_to_endpoint"
        return "finite"


@dataclass(frozen=True)
class LagMeasurement:
    local_lag: int
    delay_samples: int
    delay_seconds: Fraction
    reference_interval: SampleBounds
    measurement_interval: SampleBounds
    raw_sum: Fraction
    reference_power: Fraction
    measurement_power: Fraction
    score: LagScore | None
    eligibility: Eligibility

    @property
    def pair_count(self) -> int:
        return self.reference_interval[1] - self.reference_interval[0]


@dataclass(frozen=True)
class CrossCorrelation:
    reference_epoch: ScopeEpoch
    measurement_epoch: ScopeEpoch
    reference_channel: str
    measurement_channel: str
    reference_interval: SampleBounds
    measurement_interval: SampleBounds
    profile: LagProfile
    evaluated_delay_bounds: SampleBounds | None
    curve: tuple[LagMeasurement, ...]
    peaks: tuple[LagMeasurement, ...]
    next_best: tuple[LagMeasurement, ...]

    @property
    def status(self) -> Literal["empty_search", "no_eligible_peak", "ambiguous", "selected"]:
        if not self.curve:
            return "empty_search"
        if not self.peaks:
            return "no_eligible_peak"
        return "selected" if len(self.peaks) == 1 else "ambiguous"

    @property
    def on_search_edge(self) -> bool:
        bounds = self.evaluated_delay_bounds
        return bounds is not None and any(row.delay_samples in bounds for row in self.peaks)


def _clock(epoch: ScopeEpoch) -> tuple[str, str, int, Fraction]:
    return epoch.clock_domain, epoch.epoch_id, epoch.origin_sample, epoch.rate_hz


def _select_plane(capture: CaptureWindow, channel: str) -> tuple[Fraction, ...]:
    labels = capture.epoch.channel_ids
    if type(channel) is not str or channel not in labels:
        raise ValueError("each channel ID must name a plane in its capture")
    return tuple(Fraction(sample) for sample in capture.planes[labels.index(channel)])


def _prefix_moments(samples: tuple[Fraction, ...]) -> tuple[list[Fraction], list[Fraction]]:
    sums, squares = [Fraction(0)], [Fraction(0)]
    for sample in samples:
        sums.append(sums[-1] + sample)
        squares.append(squares[-1] + sample * sample)
    return sums, squares


def _score_lag(
    profile: LagProfile, count: int, cross: Fraction, x_sum: Fraction, y_sum: Fraction,
    x_squares: Fraction, y_squares: Fraction,
) -> tuple[LagScore | None, Fraction, Fraction, Eligibility]:
    mode = profile.score_mode
    numerator = cross
    power_divisor = count
    if mode == "pearson":
        numerator = count * cross - x_sum * y_sum
        x_squares = count * x_squares - x_sum**2
        y_squares = count * y_squares - y_sum**2
        power_divisor = count**2
    reference_power, measurement_power = x_squares / power_divisor, y_squares / power_divisor

    if mode == "raw":
        score = LagScore(cross, False)
    elif mode == "mean_product":
        score = LagScore(cross / count, False)
    elif x_squares and y_squares:
        signed_square = numerator * abs(numerator) / (x_squares * y_squares)
        score = LagScore(signed_square, True)
    else:
        score = None

    if count < profile.minimum_pairs:
        eligibility = "insufficient_pairs"
    elif not reference_power or not measurement_power:
        eligibility = "zero_power"
    elif reference_power < profile.reference_power_floor or measurement_power < profile.measurement_power_floor:
        eligibility = "below_level"
    else:
        eligibility = "eligible"
    return score, reference_power, measurement_power, eligibility


def _select_peaks(
    curve: tuple[LagMeasurement, ...], rule: PeakRule,
) -> tuple[tuple[LagMeasurement, ...], tuple[LagMeasurement, ...]]:
    by_rank: dict[Fraction, list[LagMeasurement]] = {}
    for row in curve:
        if row.eligibility != "eligible" or row.score is None:
            continue
        rank = row.score.rank_value
        if rule == "absolute":
            rank = abs(rank)
        if rank > 0:
            by_rank.setdefault(rank, []).append(row)
    best = sorted(by_rank, reverse=True)[:2]
    peaks = tuple(by_rank[best[0]]) if best else ()
    next_best = tuple(by_rank[best[1]]) if len(best) > 1 else ()
    return peaks, next_best


def correlate_captures(
    reference: CaptureWindow, measurement: CaptureWindow, profile: LagProfile, *,
    reference_channel: str, measurement_channel: str,
) -> CrossCorrelation:
    """Score every feasible lag in the inclusive clock-delay search range."""
    if type(reference) is not CaptureWindow or type(measurement) is not CaptureWindow or type(profile) is not LagProfile:
        raise ValueError("cross-correlation requires two CaptureWindow values and a LagProfile")
    if _clock(reference.epoch) != _clock(measurement.epoch):
        raise ValueError("captures must share the clock domain, epoch ID, origin, and exact sample rate")
    x = _select_plane(reference, reference_channel)
    y = _select_plane(measurement, measurement_channel)
    sx, sy = reference.start_sample, measurement.start_sample
    origin_delta = sy - sx
    first = max(1 - len(x), profile.delay_bounds[0] - origin_delta)
    last = min(len(y) - 1, profile.delay_bounds[1] - origin_delta)
    rate = reference.epoch.rate_hz

    rows = []
    if first <= last:
        x_sums, x_powers = _prefix_moments(x)
        y_sums, y_powers = _prefix_moments(y)
        for lag in range(first, last + 1):
            lo, hi = max(0, -lag), min(len(x), len(y) - lag)
            y_lo, y_hi = lo + lag, hi + lag
            cross = sum(x[n] * y[n + lag] for n in range(lo, hi))
            score, x_power, y_power, eligibility = _score_lag(
                profile, hi - lo, cross,
                x_sums[hi] - x_sums[lo], y_sums[y_hi] - y_sums[y_lo],
                x_powers[hi] - x_powers[lo], y_powers[y_hi] - y_powers[y_lo],
            )
            delay = origin_delta + lag
            rows.append(LagMeasurement(
                lag, delay, delay / rate, (sx + lo, sx + hi), (sy + y_lo, sy + y_hi),
                cross, x_power, y_power, score, eligibility,
            ))
    curve = tuple(rows)
    peaks, next_best = _select_peaks(curve, profile.peak_rule)
    return CrossCorrelation(
        reference_epoch=reference.epoch, measurement_epoch=measurement.epoch,
        reference_channel=reference_channel, measurement_channel=measurement_channel,
        reference_interval=(sx, reference.end_sample_exclusive),
        measurement_interval=(sy, measurement.end_sample_exclusive),
        profile=profile,
        evaluated_delay_bounds=(first + origin_delta, last + origin_delta) if curve else None,
        curve=curve, peaks=peaks, next_best=next_best,
    )
