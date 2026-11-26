"""Bounded offline beat tracking on sample-clocked spectral novelty."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from itertools import groupby
from math import ceil, floor, isfinite, log, log1p
from typing import Literal, Optional, Sequence, Union

from reference_onset_detection import NoveltyPoint, OnsetFrame, OnsetProfile
from reference_oscilloscope import MAX_SAMPLE_INDEX


MAX_FEATURE_FRAMES = 4096
Scalar = Union[int, float, Fraction]
TempoStatus = Literal[
    "insufficient_support", "flat_input", "flat_scores", "no_positive_peak",
    "ambiguous", "prior_selected", "selected",
]
SegmentStatus = Literal["isolated", "tempo_unavailable", "insufficient_alignment", "tracked"]
_ZERO = Fraction()
_LN2 = Fraction(log(2))


def _integer(value: int, name: str, lower: int, upper: int) -> None:
    if type(value) is not int or not lower <= value <= upper:
        raise ValueError(f"{name} must be an integer in [{lower}, {upper}]")


def _number(value: Scalar, name: str) -> Fraction:
    if type(value) not in (int, float, Fraction) or (type(value) is float and not isfinite(value)):
        raise ValueError(f"{name} must be a finite real number")
    return Fraction(value)


def _nonnegative(value: Scalar, name: str) -> Fraction:
    exact = _number(value, name)
    if exact < 0:
        raise ValueError(f"{name} must be nonnegative")
    return exact


def _positive(value: Scalar, name: str) -> Fraction:
    exact = _number(value, name)
    if exact <= 0:
        raise ValueError(f"{name} must be positive")
    return exact


def _values(novelty: Sequence[Scalar]) -> tuple[Fraction, ...]:
    if type(novelty) not in (list, tuple) or len(novelty) > MAX_FEATURE_FRAMES:
        raise ValueError("supply a bounded list or tuple of novelty scores")
    return tuple(_nonnegative(v, "novelty score") for v in novelty)


def _log_ratio(ratio: Fraction) -> Fraction:
    """Round a log ratio without overflowing or subtracting nearby logs."""
    if Fraction(1, 2) <= ratio <= 2:
        return Fraction(log1p(float(ratio - 1)))
    exponent = ratio.numerator.bit_length() - ratio.denominator.bit_length()
    mantissa = ratio / Fraction(2)**exponent
    return Fraction(log(float(mantissa))) + exponent * _LN2


@dataclass(frozen=True)
class TempoPrior:
    center_bpm: Scalar
    width_octaves: Scalar

    def __post_init__(self) -> None:
        object.__setattr__(self, "center_bpm", _positive(self.center_bpm, "prior center"))
        object.__setattr__(self, "width_octaves", _positive(self.width_octaves, "prior width"))


@dataclass(frozen=True)
class TempoSearch:
    minimum_bpm: Scalar = 60
    maximum_bpm: Scalar = 240
    minimum_pairs: int = 8
    minimum_intervals: int = 2
    remove_mean: bool = False
    aggregation: Literal["sum", "mean"] = "mean"
    prior: Optional[TempoPrior] = None

    def __post_init__(self) -> None:
        lo = _positive(self.minimum_bpm, "minimum BPM")
        hi = _positive(self.maximum_bpm, "maximum BPM")
        if lo > hi:
            raise ValueError("tempo bounds are reversed")
        _integer(self.minimum_pairs, "minimum pairs", 1, MAX_FEATURE_FRAMES - 1)
        _integer(self.minimum_intervals, "minimum intervals", 1, MAX_FEATURE_FRAMES - 1)
        if type(self.remove_mean) is not bool or self.aggregation not in ("sum", "mean"):
            raise ValueError("invalid autocorrelation preprocessing or aggregation")
        if self.prior is not None and type(self.prior) is not TempoPrior:
            raise ValueError("supply a TempoPrior")
        object.__setattr__(self, "minimum_bpm", lo)
        object.__setattr__(self, "maximum_bpm", hi)


@dataclass(frozen=True)
class LagEvidence:
    lag_frames: int
    bpm: Fraction
    pairs: int
    complete_intervals: int
    raw_sum: Fraction
    mean_product: Fraction
    eligible: bool


@dataclass(frozen=True)
class TempoCandidate:
    lag: LagEvidence
    evidence: Fraction
    rank: Fraction


@dataclass(frozen=True)
class TempoEstimate:
    status: TempoStatus
    lags: tuple[LagEvidence, ...]
    candidates: tuple[TempoCandidate, ...] = ()
    evidence_best_lags: tuple[int, ...] = ()
    selected: Optional[TempoCandidate] = None


def _lag_evidence(values: tuple[Fraction, ...], rate: Fraction, search: TempoSearch) -> tuple[LagEvidence, ...]:
    count = len(values)
    low = max(1, ceil(60 * rate / search.maximum_bpm))
    high = min(count - 1, floor(60 * rate / search.minimum_bpm))
    if search.remove_mean and count:
        mean = sum(values, _ZERO) / count
        values = tuple(value - mean for value in values)
    result = []
    for lag in range(low, high + 1):
        pairs = count - lag
        intervals = (count - 1) // lag
        raw = sum((a * b for a, b in zip(values, values[lag:])), _ZERO)
        eligible = pairs >= search.minimum_pairs and intervals >= search.minimum_intervals
        result.append(LagEvidence(lag, 60 * rate / lag, pairs, intervals, raw, raw / pairs, eligible))
    return tuple(result)


def _peaks(lags: tuple[LagEvidence, ...], aggregation: str) -> list[tuple[LagEvidence, Fraction]]:
    eligible = (
        (lag, lag.mean_product if aggregation == "mean" else lag.raw_sum)
        for lag in lags if lag.eligible
    )
    plateaus = [(value, list(group)) for value, group in groupby(eligible, key=lambda row: row[1])]
    peaks = []
    for i, (value, plateau) in enumerate(plateaus):
        if value <= 0:
            continue
        if i and value < plateaus[i - 1][0]:
            continue
        if i + 1 < len(plateaus) and value < plateaus[i + 1][0]:
            continue
        peaks.extend(plateau)
    return peaks


def _rank(
    peaks: list[tuple[LagEvidence, Fraction]], best: Fraction, prior: Optional[TempoPrior]
) -> tuple[TempoCandidate, ...]:
    candidates = []
    for lag, evidence in peaks:
        rank = evidence
        if prior is not None:
            octaves = _log_ratio(lag.bpm / prior.center_bpm) / _LN2
            rank = _log_ratio(evidence / best) - ((octaves / prior.width_octaves)**2) / 2
        candidates.append(TempoCandidate(lag, evidence, rank))
    return tuple(sorted(candidates, key=lambda item: (-item.rank, item.lag.lag_frames)))


def estimate_tempo(
    novelty: Sequence[Scalar], feature_rate_hz: Scalar, search: TempoSearch = TempoSearch(),
) -> TempoEstimate:
    """Return linear autocorrelation evidence and a qualified candidate, if any."""
    values = _values(novelty)
    rate = _positive(feature_rate_hz, "feature rate")
    if type(search) is not TempoSearch:
        raise ValueError("supply a TempoSearch")
    lags = _lag_evidence(values, rate, search)
    if not any(lag.eligible for lag in lags):
        return TempoEstimate("insufficient_support", lags)
    if min(values) == max(values):
        return TempoEstimate("flat_input", lags)
    peaks = _peaks(lags, search.aggregation)
    if not peaks:
        return TempoEstimate("no_positive_peak", lags)
    evidence_best = max(value for _, value in peaks)
    best_lags = tuple(lag.lag_frames for lag, value in peaks if value == evidence_best)
    if len(best_lags) > 1 and len(best_lags) == sum(lag.eligible for lag in lags):
        return TempoEstimate("flat_scores", lags, _rank(peaks, evidence_best, None), best_lags)
    ranked = _rank(peaks, evidence_best, search.prior)
    if len(ranked) > 1 and ranked[0].rank == ranked[1].rank:
        return TempoEstimate("ambiguous", lags, ranked, best_lags)
    selected = ranked[0]
    if best_lags != (selected.lag.lag_frames,):
        return TempoEstimate("prior_selected", lags, ranked, best_lags, selected)
    return TempoEstimate("selected", lags, ranked, best_lags, selected)


@dataclass(frozen=True)
class PhaseEvidence:
    offset_frames: int
    count: int
    score: Fraction


def phase_scores(novelty: Sequence[Scalar], period_frames: int) -> tuple[PhaseEvidence, ...]:
    """Sum each integer phase on the same number of complete cycles."""
    values = _values(novelty)
    _integer(period_frames, "phase period", 1, MAX_FEATURE_FRAMES)
    complete = len(values) // period_frames
    if complete == 0:
        return ()
    end = complete * period_frames
    return tuple(
        PhaseEvidence(i, complete, sum(values[i:end:period_frames], _ZERO))
        for i in range(period_frames)
    )


@dataclass(frozen=True)
class BeatPath:
    indices: tuple[int, ...]
    score: Fraction


def _period(value: Scalar) -> Fraction:
    period = _positive(value, "beat period")
    if not 1 <= period <= MAX_FEATURE_FRAMES:
        raise ValueError("beat period exceeds the supported frame interval")
    return period


def _periods(period: Union[Scalar, Sequence[Scalar]], count: int) -> tuple[Fraction, ...]:
    if type(period) in (list, tuple):
        if len(period) != count:
            raise ValueError("supply one period per input frame")
        return tuple(_period(value) for value in period)
    return (_period(period),) * count


def _align(values: tuple[Fraction, ...], periods: tuple[Fraction, ...], weight: Fraction) -> BeatPath:
    if not values:
        return BeatPath((), _ZERO)

    @lru_cache(maxsize=MAX_FEATURE_FRAMES)
    def penalty(step: int, period: Fraction) -> Fraction:
        return weight * _log_ratio(step / period)**2

    totals, parents = [], []
    for t, (strength, period) in enumerate(zip(values, periods)):
        best, parent = _ZERO, None
        first = max(0, t - floor(2 * period))
        last = t - ceil(period / 2)
        for s in range(first, last + 1):
            continuation = totals[s] - penalty(t - s, period)
            if continuation > best:
                best, parent = continuation, s
        totals.append(strength + best)
        parents.append(parent)

    end = max(range(len(values)), key=totals.__getitem__)
    score = totals[end]
    if score <= 0:
        return BeatPath((), _ZERO)
    path = []
    while end is not None:
        path.append(end)
        end = parents[end]
    return BeatPath(tuple(reversed(path)), score)


def align_beats(
    novelty: Sequence[Scalar], period_frames: Union[Scalar, Sequence[Scalar]],
    *, interval_penalty: Scalar = 8,
) -> BeatPath:
    """Optimize the bounded path objective for one contiguous feature array."""
    values = _values(novelty)
    return _align(values, _periods(period_frames, len(values)),
                  _nonnegative(interval_penalty, "interval penalty"))


@dataclass(frozen=True)
class BeatProfile:
    maximum_support_gap_samples: int
    support_floor: Scalar = 0
    interval_penalty: Scalar = 8
    tempo_search: TempoSearch = TempoSearch()

    def __post_init__(self) -> None:
        _integer(self.maximum_support_gap_samples, "support gap", 1, MAX_SAMPLE_INDEX)
        floor = _nonnegative(self.support_floor, "support floor")
        penalty = _nonnegative(self.interval_penalty, "interval penalty")
        if type(self.tempo_search) is not TempoSearch:
            raise ValueError("supply a TempoSearch")
        object.__setattr__(self, "support_floor", floor)
        object.__setattr__(self, "interval_penalty", penalty)


@dataclass(frozen=True)
class BeatPosition:
    frame_index: int
    novelty: NoveltyPoint
    period_frames: Fraction
    supported: bool

    @property
    def center_sample_twice(self) -> int:
        return self.novelty.center_sample_twice

    @property
    def target_bpm(self) -> Fraction:
        grid = self.novelty.frame.grid
        return 60 * grid.epoch.rate_hz / (grid.hop * self.period_frames)


@dataclass(frozen=True)
class BeatSegment:
    first_frame_index: int
    last_frame_index: int
    status: SegmentStatus
    tempo: Optional[TempoEstimate]
    path: BeatPath
    beats: tuple[BeatPosition, ...] = ()


@dataclass(frozen=True)
class BeatRun:
    novelty: tuple[NoveltyPoint, ...]
    profile: BeatProfile
    segments: tuple[BeatSegment, ...]
    ready_sample_exclusive: Optional[int]
    observed_release_sample_exclusive: Optional[int]


def _read_points(
    points: tuple[NoveltyPoint, ...],
) -> tuple[tuple[int, ...], tuple[Optional[Fraction], ...]]:
    for point in points:
        if type(point) is not NoveltyPoint or type(point.frame) is not OnsetFrame:
            raise ValueError("supply Skill #36 novelty points with complete frames")
    grid, profile = points[0].frame.grid, points[0].profile
    if type(profile) is not OnsetProfile:
        raise ValueError("supply the onset comparison profile")
    indices, scores = [], []
    for point in points:
        if point.frame.grid != grid or point.profile != profile:
            raise ValueError("a change of grid, epoch, or onset profile requires a new run")
        start = point.frame.start_sample
        index, extra = divmod(start - grid.first_start_sample, grid.hop)
        if extra or (indices and index <= indices[-1]):
            raise ValueError("points must be in increasing order on the declared frame grid")
        indices.append(index)
        earlier = point.reference_start_sample
        if point.flux is None:
            if earlier is not None:
                raise ValueError("unavailable flux must have unavailable comparison support")
            scores.append(None)
        else:
            if type(earlier) is not int or earlier != start - profile.lag * grid.hop:
                raise ValueError("flux comparison start must match the declared lag")
            if earlier < grid.first_start_sample:
                raise ValueError("flux comparison precedes the frame grid")
            scores.append(_nonnegative(point.flux, "flux"))
    return tuple(indices), tuple(scores)


def _supported_spans(
    indices: tuple[int, ...], scores: tuple[Optional[Fraction], ...], hop: int, profile: BeatProfile,
) -> list[tuple[int, int]]:
    spans = []
    first = last = None
    for i, value in enumerate(scores):
        if value is None or (i and indices[i] != indices[i - 1] + 1):
            if first is not None:
                spans.append((first, last))
            first = last = None
        if value is None or value <= profile.support_floor:
            continue
        if last is not None and (indices[i] - indices[last]) * hop > profile.maximum_support_gap_samples:
            spans.append((first, last))
            first = None
        if first is None:
            first = i
        last = i
    if first is not None:
        spans.append((first, last))
    return spans


def _track_span(
    points: tuple[NoveltyPoint, ...], indices: tuple[int, ...], values: tuple[Fraction, ...],
    periods: Optional[tuple[Fraction, ...]], profile: BeatProfile,
) -> BeatSegment:
    span = indices[0], indices[-1]
    empty = BeatPath((), _ZERO)
    if len(values) == 1:
        return BeatSegment(*span, "isolated", None, empty)
    tempo = None
    if periods is None:
        grid = points[0].frame.grid
        tempo = estimate_tempo(values, grid.epoch.rate_hz / grid.hop, profile.tempo_search)
        if tempo.selected is None:
            return BeatSegment(*span, "tempo_unavailable", tempo, empty)
        periods = (Fraction(tempo.selected.lag.lag_frames),) * len(values)
    path = _align(values, periods, profile.interval_penalty)
    beats = tuple(
        BeatPosition(indices[i], points[i], periods[i], values[i] > profile.support_floor)
        for i in path.indices
    )
    if sum(beat.supported for beat in beats) < 2:
        return BeatSegment(*span, "insufficient_alignment", tempo, path)
    return BeatSegment(*span, "tracked", tempo, path, beats)


def track_beats(
    points: Sequence[NoveltyPoint], profile: BeatProfile, *,
    period_frames: Optional[Union[Scalar, Sequence[Scalar]]] = None,
    observed_release_sample_exclusive: Optional[int] = None,
) -> BeatRun:
    """Track each qualified segment of one analysis run without crossing a gap."""
    if type(profile) is not BeatProfile:
        raise ValueError("supply a BeatProfile with an elapsed support limit")
    if type(points) not in (list, tuple) or len(points) > MAX_FEATURE_FRAMES:
        raise ValueError("supply a bounded list or tuple of novelty points")
    records = tuple(points)
    periods = None if period_frames is None else _periods(period_frames, len(records))
    if not records:
        if observed_release_sample_exclusive is not None:
            raise ValueError("an empty run has no observed release boundary")
        return BeatRun(records, profile, (), None, None)
    indices, scores = _read_points(records)
    ready = records[-1].frame.end_sample_exclusive
    if observed_release_sample_exclusive is not None:
        _integer(observed_release_sample_exclusive, "observed release boundary", ready, MAX_SAMPLE_INDEX)
    hop = records[0].frame.grid.hop
    segments = []
    for first, last in _supported_spans(indices, scores, hop, profile):
        selected = slice(first, last + 1)
        segments.append(_track_span(
            records[selected], indices[selected], scores[selected],
            None if periods is None else periods[selected], profile,
        ))
    return BeatRun(records, profile, tuple(segments), ready, observed_release_sample_exclusive)
