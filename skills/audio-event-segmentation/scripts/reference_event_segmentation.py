"""Bounded two-sided novelty and interval coverage on one feature grid."""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from fractions import Fraction
from typing import Literal, Optional, Sequence

from reference_oscilloscope import MAX_SAMPLE_INDEX, ScopeEpoch, _check_integer, _is_label
from reference_pitch_tracking import Scalar, _scalar
from reference_tuning_analysis import TuningSupport


MAX_FEATURE_FRAMES = 4096
MAX_FEATURE_DIMENSIONS = 64
MAX_CONTEXT_FRAMES = 128
_ZERO = Fraction()
Interval = tuple[int, int]
Decision = Literal[
    "comparison_edge", "feature_gap", "flank_unavailable", "outside_analysis",
    "below_threshold", "not_peak", "selected",
]


@dataclass(frozen=True)
class FeatureGrid:
    epoch: ScopeEpoch
    window_samples: int
    hop_samples: int
    feature_profile: str
    units: tuple[str, ...]
    first_start_sample: Optional[int] = None

    def __post_init__(self) -> None:
        if type(self.epoch) is not ScopeEpoch or not _is_label(self.feature_profile):
            raise ValueError("supply a sample epoch and a named feature profile")
        _check_integer(self.window_samples, "window length", 1, MAX_SAMPLE_INDEX)
        _check_integer(self.hop_samples, "hop", 1, self.window_samples)
        if (type(self.units) is not tuple or not 1 <= len(self.units) <= MAX_FEATURE_DIMENSIONS
                or not all(_is_label(unit) for unit in self.units)):
            raise ValueError("declare units for each feature component")
        start = self.epoch.origin_sample if self.first_start_sample is None else self.first_start_sample
        _check_integer(start, "first window start", self.epoch.origin_sample, MAX_SAMPLE_INDEX - self.window_samples)
        object.__setattr__(self, "first_start_sample", start)

    def start_sample(self, index: int) -> int:
        last = (MAX_SAMPLE_INDEX - self.window_samples - self.first_start_sample) // self.hop_samples
        _check_integer(index, "feature index", 0, last)
        return self.first_start_sample + index * self.hop_samples

    def center_sample_twice(self, index: int) -> int:
        return 2 * self.start_sample(index) + self.window_samples - 1


@dataclass(frozen=True)
class FeatureFrame:
    grid: FeatureGrid
    index: int
    support: TuningSupport
    values: Optional[tuple[Scalar, ...]]

    def __post_init__(self) -> None:
        if type(self.grid) is not FeatureGrid or type(self.support) is not TuningSupport:
            raise ValueError("supply a feature grid and the frame's sample support")
        start = self.grid.start_sample(self.index)
        if (self.support.epoch != self.grid.epoch or self.support.start_sample != start
                or self.support.end_sample_exclusive != start + self.grid.window_samples):
            raise ValueError("feature support must align with the grid and epoch")
        if self.values is None:
            return
        if type(self.values) is not tuple or len(self.values) != len(self.grid.units):
            raise ValueError("supply a tuple with one value per declared feature component")
        if self.support.ready_sample_exclusive is None:
            raise ValueError("measured features require complete, ready support")
        object.__setattr__(self, "values", tuple(_scalar(value, "feature component") for value in self.values))


@dataclass(frozen=True)
class SegmentationProfile:
    side_frames: int = 2
    peak_radius: int = 1
    minimum_score: Scalar = 1

    def __post_init__(self) -> None:
        _check_integer(self.side_frames, "comparison width", 1, MAX_CONTEXT_FRAMES)
        _check_integer(self.peak_radius, "peak radius", 1, MAX_CONTEXT_FRAMES)
        threshold = _scalar(self.minimum_score, "minimum score")
        if threshold <= 0:
            raise ValueError("minimum score must be positive")
        object.__setattr__(self, "minimum_score", threshold)


@dataclass(frozen=True)
class ChangeScore:
    left_sample_support: Interval
    right_sample_support: Interval
    mean_change: tuple[Fraction, ...]
    squared_novelty: Fraction
    ready_sample_exclusive: int
    evidence_release_sample_exclusive: Optional[int]


@dataclass(frozen=True)
class CutEvidence:
    index: int
    left_center_sample_twice: int
    right_center_sample_twice: int
    disposition: Decision
    score: Optional[ChangeScore] = None
    peak_sample_support: Optional[Interval] = None
    peak_ready_sample_exclusive: Optional[int] = None
    peak_evidence_release_sample_exclusive: Optional[int] = None

    @property
    def position_sample_twice(self) -> int:
        return (self.left_center_sample_twice + self.right_center_sample_twice) // 2


@dataclass(frozen=True)
class Segment:
    start_sample_twice: int
    end_sample_twice: int
    feature_available: bool


@dataclass(frozen=True)
class SegmentationResult:
    grid: FeatureGrid
    profile: SegmentationProfile
    frame_index_span: Interval
    analysis_span_twice: Interval
    source_frames: tuple[FeatureFrame, ...]
    candidates: tuple[CutEvidence, ...]
    segments: tuple[Segment, ...]
    peak_eligible_spans_twice: tuple[Interval, ...]

    @property
    def boundaries(self) -> tuple[CutEvidence, ...]:
        return tuple(cut for cut in self.candidates if cut.disposition == "selected")


def _valid_runs(
    frames_by_index: dict[int, FeatureFrame], first: int, end: int,
) -> list[list[FeatureFrame]]:
    runs = []
    current = []
    for index in range(first, end):
        frame = frames_by_index.get(index)
        if frame is None or frame.values is None:
            if current:
                runs.append(current)
                current = []
        else:
            current.append(frame)
    if current:
        runs.append(current)
    return runs


def _latest_reported(boundaries: Sequence[Optional[int]]) -> Optional[int]:
    return max(boundaries) if all(boundary is not None for boundary in boundaries) else None


def _score_run(run: list[FeatureFrame], width: int) -> dict[int, ChangeScore]:
    if len(run) < 2 * width:
        return {}
    prefix = [(_ZERO,) * len(run[0].grid.units)]
    for frame in run:
        prefix.append(tuple(a + b for a, b in zip(prefix[-1], frame.values)))
    scores = {}
    for cut in range(width, len(run) - width + 1):
        low, high = cut - width, cut + width
        delta = tuple((end - 2 * mid + start) / width
                      for start, mid, end in zip(prefix[low], prefix[cut], prefix[high]))
        supports = [row.support for row in run[low:high]]
        scores[run[cut].index] = ChangeScore(
            (supports[0].start_sample, supports[width - 1].end_sample_exclusive),
            (supports[width].start_sample, supports[-1].end_sample_exclusive),
            delta, sum((value**2 for value in delta), _ZERO),
            max(item.ready_sample_exclusive for item in supports),
            _latest_reported([item.observed_release_sample_exclusive for item in supports]),
        )
    return scores


def _cut_evidence(
    grid: FeatureGrid, profile: SegmentationProfile, index: int, frame_index_span: Interval,
    scores: dict[int, ChangeScore], analysis_span: Interval,
) -> CutEvidence:
    before, after = grid.center_sample_twice(index - 1), grid.center_sample_twice(index)
    width, radius = profile.side_frames, profile.peak_radius
    score = scores.get(index)
    if score is None:
        status = ("comparison_edge" if index - width < frame_index_span[0]
                  or index + width > frame_index_span[1] else "feature_gap")
        return CutEvidence(index, before, after, status)
    if not analysis_span[0] < (before + after) // 2 < analysis_span[1]:
        return CutEvidence(index, before, after, "outside_analysis", score)
    flank = [scores.get(b) for b in range(index - radius, index + radius + 1)]
    if any(value is None for value in flank):
        return CutEvidence(index, before, after, "flank_unavailable", score)
    current = score.squared_novelty
    if current < profile.minimum_score:
        status = "below_threshold"
    elif (any(current <= left.squared_novelty for left in flank[:radius])
          or any(current < right.squared_novelty for right in flank[radius + 1:])):
        status = "not_peak"
    else:
        status = "selected"
    return CutEvidence(
        index, before, after, status, score,
        (flank[0].left_sample_support[0], flank[-1].right_sample_support[1]),
        max(point.ready_sample_exclusive for point in flank),
        _latest_reported([point.evidence_release_sample_exclusive for point in flank]),
    )


def _eligible_spans(cuts: tuple[CutEvidence, ...], span: Interval, hop: int) -> tuple[Interval, ...]:
    intervals = []
    for cut in cuts:
        if cut.peak_ready_sample_exclusive is None:
            continue
        center = cut.position_sample_twice
        left, right = max(span[0], center - hop), min(span[1], center + hop)
        if intervals and intervals[-1][1] == left:
            intervals[-1] = (intervals[-1][0], right)
        else:
            intervals.append((left, right))
    return tuple(intervals)


def _segments(
    grid: FeatureGrid, runs: list[list[FeatureFrame]], cuts: tuple[CutEvidence, ...], span: Interval,
) -> tuple[Segment, ...]:
    positions = [cut.position_sample_twice for cut in cuts if cut.disposition == "selected"]
    hop = grid.hop_samples
    current, end = span
    segments = []
    for run in runs:
        left = max(span[0], grid.center_sample_twice(run[0].index) - hop)
        right = min(end, grid.center_sample_twice(run[-1].index) + hop)
        if left >= right:
            continue
        if current < left:
            segments.append(Segment(current, left, False))
        included = positions[bisect_right(positions, left):bisect_left(positions, right)]
        edges = [left, *included, right]
        segments.extend(Segment(a, b, True) for a, b in zip(edges, edges[1:]))
        current = right
    if current < end:
        segments.append(Segment(current, end, False))
    return tuple(segments)


def analyze_segments(
    grid: FeatureGrid, frames: Sequence[FeatureFrame], profile: SegmentationProfile = SegmentationProfile(),
    *, first_index: int = 0, frame_count: int, analysis_span_twice: Interval,
) -> SegmentationResult:
    """Analyze a requested grid span, preserving missing slots and exact clocks."""
    if type(grid) is not FeatureGrid or type(profile) is not SegmentationProfile:
        raise ValueError("supply a FeatureGrid and SegmentationProfile")
    _check_integer(first_index, "first feature index", 0, MAX_SAMPLE_INDEX)
    _check_integer(frame_count, "requested feature count", 0, MAX_FEATURE_FRAMES)
    end = first_index + frame_count
    if frame_count:
        grid.start_sample(end - 1)
    if type(analysis_span_twice) is not tuple or len(analysis_span_twice) != 2:
        raise ValueError("supply a half-open analysis span in doubled samples")
    start_twice, end_twice = analysis_span_twice
    _check_integer(start_twice, "analysis start", 2 * grid.epoch.origin_sample, 2 * MAX_SAMPLE_INDEX - 1)
    _check_integer(end_twice, "analysis end", start_twice + 1, 2 * MAX_SAMPLE_INDEX)
    if type(frames) not in (list, tuple) or len(frames) > frame_count:
        raise ValueError("supply at most one frame per requested slot")

    by_index = {}
    for frame in frames:
        if (type(frame) is not FeatureFrame or frame.grid != grid
                or not first_index <= frame.index < end or frame.index in by_index):
            raise ValueError("supply unique frames on the requested grid and index span")
        by_index[frame.index] = frame

    runs = _valid_runs(by_index, first_index, end)
    scores = {}
    for run in runs:
        scores.update(_score_run(run, profile.side_frames))
    index_span = (first_index, end)
    cuts = tuple(_cut_evidence(grid, profile, index, index_span, scores, analysis_span_twice)
                 for index in range(first_index + 1, end))
    return SegmentationResult(
        grid, profile, index_span, analysis_span_twice, tuple(by_index[i] for i in sorted(by_index)),
        cuts, _segments(grid, runs, cuts, analysis_span_twice),
        _eligible_spans(cuts, analysis_span_twice, grid.hop_samples),
    )
