"""Offline rhythm measurements on exact onset and beat coordinates."""

from __future__ import annotations

from bisect import bisect_right
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from fractions import Fraction
from math import ceil, floor, isfinite
from typing import Literal, Optional, Sequence, Union

from reference_beat_tracking import BeatRun
from reference_onset_detection import OnsetEvent
from reference_oscilloscope import MAX_SAMPLE_INDEX, ScopeEpoch


MAX_EVENTS = 4096
MAX_ANCHORS = 4096
MAX_SUBDIVISIONS = 64
Scalar = Union[int, float, Fraction]
AnchorKind = Literal["supplied", "supported", "inferred", "predicted"]
PhaseStatus = Literal[
    "mapped", "no_grid", "outside_grid", "no_right_anchor", "beat_gap",
    "inferred_anchor", "predicted_anchor",
]
SwingStatus = Literal["measured", "phase_unavailable", "endpoint", "ambiguous_offbeat"]


def _integer(value: int, name: str, low: int, high: int) -> None:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in [{low}, {high}]")


def _label(value: str, name: str) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{name} must be a nonempty label")


@dataclass(frozen=True)
class Availability:
    """End-exclusive data and measured delivery boundaries on one sample clock."""

    ready_sample_exclusive: Optional[int] = None
    observed_release_sample_exclusive: Optional[int] = None

    def __post_init__(self) -> None:
        ready, observed = self.ready_sample_exclusive, self.observed_release_sample_exclusive
        if ready is not None:
            _integer(ready, "ready boundary", 0, MAX_SAMPLE_INDEX)
        if observed is not None:
            _integer(observed, "observed release boundary", 0 if ready is None else ready, MAX_SAMPLE_INDEX)


def _joint_availability(*inputs: Availability) -> Availability:
    ready = [item.ready_sample_exclusive for item in inputs]
    observed = [item.observed_release_sample_exclusive for item in inputs]
    return Availability(
        None if None in ready else max(ready),
        None if None in observed else max(observed),
    )


@dataclass(frozen=True)
class RhythmCapture:
    """One interval of continuous acquisition on the declared comparison clock."""

    epoch: ScopeEpoch
    start_sample: int
    end_sample_exclusive: int

    def __post_init__(self) -> None:
        if type(self.epoch) is not ScopeEpoch:
            raise ValueError("supply a ScopeEpoch for the comparison clock")
        _integer(self.start_sample, "capture start", self.epoch.origin_sample, MAX_SAMPLE_INDEX)
        _integer(self.end_sample_exclusive, "capture end", self.start_sample + 1, MAX_SAMPLE_INDEX)

    def contains(self, sample_twice: int) -> bool:
        return 2 * self.start_sample <= sample_twice < 2 * self.end_sample_exclusive


def _point_in_capture(
    sample_twice: int, timing: Availability, capture: RhythmCapture, *, allow_end: bool = False,
) -> None:
    at_boundary = allow_end and sample_twice == 2 * capture.end_sample_exclusive
    if not capture.contains(sample_twice) and not at_boundary:
        raise ValueError("position must lie within its capture")
    for boundary in (timing.ready_sample_exclusive, timing.observed_release_sample_exclusive):
        if boundary is not None and boundary < capture.epoch.origin_sample:
            raise ValueError("availability boundary precedes the clock epoch")


def _point(sample_twice: int, timing: Availability) -> None:
    _integer(sample_twice, "doubled sample position", 0, 2 * MAX_SAMPLE_INDEX)
    if type(timing) is not Availability:
        raise ValueError("supply Availability on the comparison clock")


@dataclass(frozen=True)
class RhythmEvent:
    event_id: str
    voice: str
    capture: RhythmCapture
    sample_twice: int
    timing: Availability = Availability()
    offbeat: bool = False

    def __post_init__(self) -> None:
        _label(self.event_id, "event ID")
        _label(self.voice, "voice")
        _point(self.sample_twice, self.timing)
        if type(self.capture) is not RhythmCapture or type(self.offbeat) is not bool:
            raise ValueError("supply a capture interval and a Boolean offbeat label")
        _point_in_capture(self.sample_twice, self.timing, self.capture)


@dataclass(frozen=True)
class BeatAnchor:
    anchor_id: str
    sample_twice: int
    kind: AnchorKind = "supplied"
    timing: Availability = Availability()

    def __post_init__(self) -> None:
        _label(self.anchor_id, "anchor ID")
        _point(self.sample_twice, self.timing)
        if type(self.kind) is not str or self.kind not in ("supplied", "supported", "inferred", "predicted"):
            raise ValueError("invalid anchor kind")


@dataclass(frozen=True)
class BeatGridSegment:
    capture: RhythmCapture
    anchors: tuple[BeatAnchor, ...]
    _ticks: tuple[int, ...] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if type(self.capture) is not RhythmCapture:
            raise ValueError("supply a continuous capture for this grid segment")
        if type(self.anchors) not in (list, tuple) or not 1 <= len(self.anchors) <= MAX_ANCHORS:
            raise ValueError("supply a bounded list or tuple of beat anchors")
        anchors = tuple(self.anchors)
        if any(type(anchor) is not BeatAnchor for anchor in anchors):
            raise ValueError("grid segments require BeatAnchor records")
        ticks = tuple(a.sample_twice for a in anchors)
        if any(left >= right for left, right in zip(ticks, ticks[1:])):
            raise ValueError("beat anchors must increase strictly within a grid segment")
        for anchor in anchors:
            _point_in_capture(anchor.sample_twice, anchor.timing, self.capture, allow_end=True)
        object.__setattr__(self, "anchors", anchors)
        object.__setattr__(self, "_ticks", ticks)


@dataclass(frozen=True)
class RhythmProfile:
    subdivisions: tuple[int, ...] = (2, 3, 4)
    tolerance: Scalar = 0
    tolerance_units: Literal["samples", "beats"] = "samples"
    allow_inferred_anchors: bool = True

    def __post_init__(self) -> None:
        if type(self.subdivisions) not in (tuple, list) or not 1 <= len(self.subdivisions) <= MAX_SUBDIVISIONS:
            raise ValueError("supply a bounded list or tuple of subdivision counts")
        counts = tuple(self.subdivisions)
        for q in counts:
            _integer(q, "subdivision count", 1, MAX_SUBDIVISIONS)
        if len(set(counts)) != len(counts):
            raise ValueError("subdivision counts must be unique")
        if type(self.tolerance) not in (int, float, Fraction):
            raise ValueError("supply a finite nonnegative tolerance")
        if type(self.tolerance) is float and not isfinite(self.tolerance):
            raise ValueError("supply a finite nonnegative tolerance")
        tolerance = Fraction(self.tolerance)
        if tolerance < 0 or self.tolerance_units not in ("samples", "beats"):
            raise ValueError("use nonnegative tolerance in samples or beats")
        if type(self.allow_inferred_anchors) is not bool:
            raise ValueError("inferred anchor policy must be Boolean")
        object.__setattr__(self, "subdivisions", counts)
        object.__setattr__(self, "tolerance", tolerance)


@dataclass(frozen=True)
class InterOnsetInterval:
    earlier: RhythmEvent
    later: RhythmEvent
    timing: Availability

    @property
    def samples(self) -> Fraction:
        return Fraction(self.later.sample_twice - self.earlier.sample_twice, 2)

    @property
    def seconds(self) -> Fraction:
        return self.samples / self.earlier.capture.epoch.rate_hz


@dataclass(frozen=True)
class BeatBracket:
    beat_index: int
    left: BeatAnchor
    right: BeatAnchor

    @property
    def length_samples(self) -> Fraction:
        return Fraction(self.right.sample_twice - self.left.sample_twice, 2)


@dataclass(frozen=True)
class GridSlot:
    anchor: BeatAnchor
    slot: int
    position_sample_twice: Fraction
    residual_samples: Fraction
    residual_beats: Fraction


@dataclass(frozen=True)
class SubdivisionFit:
    subdivisions: int
    slots: tuple[GridSlot, ...]
    matched: bool


@dataclass(frozen=True)
class EventRhythm:
    event: RhythmEvent
    status: PhaseStatus
    bracket: Optional[BeatBracket] = None
    phase: Optional[Fraction] = None
    fits: tuple[SubdivisionFit, ...] = ()
    timing: Availability = Availability()


@dataclass(frozen=True)
class GridEvidence:
    subdivisions: int
    eligible_events: int
    matched_events: int
    tied_matches: int
    hits_by_slot: tuple[int, ...]
    distinct_beats_by_slot: tuple[int, ...]
    absolute_residual_samples: tuple[Fraction, ...]
    absolute_residual_beats: tuple[Fraction, ...]


@dataclass(frozen=True)
class SwingObservation:
    event: RhythmEvent
    status: SwingStatus
    ratio: Optional[Fraction] = None


@dataclass(frozen=True)
class RhythmAnalysis:
    profile: RhythmProfile
    intervals: tuple[InterOnsetInterval, ...]
    positions: tuple[EventRhythm, ...]
    grids: tuple[GridEvidence, ...]
    offbeats: tuple[SwingObservation, ...]


def _validate_captures(events: Sequence[RhythmEvent], segments: Sequence[BeatGridSegment]) -> None:
    captures = {event.capture for event in events} | {segment.capture for segment in segments}
    by_epoch = defaultdict(list)
    for capture in captures:
        epoch = capture.epoch
        by_epoch[epoch.clock_domain, epoch.epoch_id].append(capture)
    for group in by_epoch.values():
        epoch = group[0].epoch
        if any(span.epoch != epoch for span in group):
            raise ValueError("a clock epoch requires consistent mapped provenance")
        ordered = sorted(group, key=lambda span: span.start_sample)
        if any(left.end_sample_exclusive > right.start_sample for left, right in zip(ordered, ordered[1:])):
            raise ValueError("capture intervals in one clock epoch must be disjoint")


def _intervals(events: Sequence[RhythmEvent]) -> tuple[InterOnsetInterval, ...]:
    by_voice = defaultdict(list)
    for event in events:
        by_voice[event.capture, event.voice].append(event)
    intervals = []
    for voice_events in by_voice.values():
        ordered = sorted(voice_events, key=lambda event: event.sample_twice)
        for left, right in zip(ordered, ordered[1:]):
            timing = _joint_availability(left.timing, right.timing)
            intervals.append(InterOnsetInterval(left, right, timing))
    return tuple(intervals)


GridIndex = tuple[tuple[int, ...], tuple[BeatGridSegment, ...]]


def _index_grids(segments: Sequence[BeatGridSegment]) -> dict[RhythmCapture, GridIndex]:
    by_capture = defaultdict(list)
    definitions = {}
    for segment in segments:
        by_capture[segment.capture].append(segment)
        for anchor in segment.anchors:
            key = segment.capture, anchor.anchor_id
            if definitions.setdefault(key, anchor) != anchor:
                raise ValueError("one anchor ID must identify one position and provenance")
    indexed = {}
    for capture, grids in by_capture.items():
        ordered = tuple(sorted(grids, key=lambda grid: grid._ticks[0]))
        if any(left._ticks[-1] > right._ticks[0] or left._ticks[0] == right._ticks[0]
               for left, right in zip(ordered, ordered[1:])):
            raise ValueError("beat grid segments overlap within one capture")
        indexed[capture] = tuple(grid._ticks[0] for grid in ordered), ordered
    return indexed


def _fit(tick: int, bracket: BeatBracket, phase: Fraction, q: int, profile: RhythmProfile) -> SubdivisionFit:
    place = phase * q
    candidates = sorted({floor(place), ceil(place)})
    distance = min(abs(place - k) for k in candidates)
    left, right = bracket.left, bracket.right
    width = right.sample_twice - left.sample_twice
    slots = []
    for k in candidates:
        if abs(place - k) == distance:
            position = left.sample_twice + Fraction(k * width, q)
            residual = tick - position
            anchor = right if k == q else left
            slots.append(GridSlot(anchor, k % q, position, residual / 2, residual / width))
    magnitude = slots[0].residual_samples if profile.tolerance_units == "samples" else slots[0].residual_beats
    return SubdivisionFit(q, tuple(slots), abs(magnitude) <= profile.tolerance)


def _position(event: RhythmEvent, grid_index: Optional[GridIndex], profile: RhythmProfile) -> EventRhythm:
    if grid_index is None:
        return EventRhythm(event, "no_grid")
    starts, segments = grid_index
    tick = event.sample_twice
    segment_index = bisect_right(starts, tick) - 1
    if segment_index < 0:
        return EventRhythm(event, "outside_grid")
    grid = segments[segment_index]
    j = bisect_right(grid._ticks, tick) - 1
    if j == len(grid.anchors) - 1:
        if tick == grid._ticks[-1]:
            return EventRhythm(event, "no_right_anchor")
        status = "beat_gap" if segment_index + 1 < len(segments) else "outside_grid"
        return EventRhythm(event, status)
    left, right = grid.anchors[j:j + 2]
    bracket = BeatBracket(j, left, right)
    kinds = left.kind, right.kind
    if "predicted" in kinds:
        return EventRhythm(event, "predicted_anchor", bracket)
    if "inferred" in kinds and not profile.allow_inferred_anchors:
        return EventRhythm(event, "inferred_anchor", bracket)
    phase = Fraction(tick - left.sample_twice, right.sample_twice - left.sample_twice)
    fits = tuple(_fit(tick, bracket, phase, q, profile) for q in profile.subdivisions)
    timing = _joint_availability(event.timing, left.timing, right.timing)
    return EventRhythm(event, "mapped", bracket, phase, fits, timing)


def _grid_evidence(positions: tuple[EventRhythm, ...], q: int, index: int) -> GridEvidence:
    hits = [0] * q
    anchors = [set() for _ in range(q)]
    residual_samples, residual_beats = [], []
    matched = ties = 0
    for item in positions:
        if item.phase is None:
            continue
        fit = item.fits[index]
        slot = fit.slots[0]
        residual_samples.append(abs(slot.residual_samples))
        residual_beats.append(abs(slot.residual_beats))
        if fit.matched:
            matched += 1
            if len(fit.slots) == 1:
                hits[slot.slot] += 1
                anchors[slot.slot].add((item.event.capture, slot.anchor.sample_twice))
            else:
                ties += 1
    return GridEvidence(
        q, len(residual_samples), matched, ties, tuple(hits),
        tuple(len(group) for group in anchors), tuple(residual_samples), tuple(residual_beats),
    )


def _offbeat_group(item: EventRhythm) -> tuple[RhythmCapture, str, int]:
    return item.event.capture, item.event.voice, item.bracket.left.sample_twice


def _swing(positions: tuple[EventRhythm, ...]) -> tuple[SwingObservation, ...]:
    labelled = [item for item in positions if item.event.offbeat]
    counts = Counter(_offbeat_group(item) for item in labelled if item.phase is not None and item.phase > 0)
    result = []
    for item in labelled:
        event, phase = item.event, item.phase
        if phase is None:
            result.append(SwingObservation(event, "phase_unavailable"))
        elif phase == 0:
            result.append(SwingObservation(event, "endpoint"))
        elif counts[_offbeat_group(item)] != 1:
            result.append(SwingObservation(event, "ambiguous_offbeat"))
        else:
            result.append(SwingObservation(event, "measured", phase / (1 - phase)))
    return tuple(result)


def analyze_rhythm(
    events: Sequence[RhythmEvent], beat_segments: Sequence[BeatGridSegment],
    profile: RhythmProfile = RhythmProfile(),
) -> RhythmAnalysis:
    """Measure same-voice IOIs and event positions on qualified beat intervals."""
    if type(profile) is not RhythmProfile:
        raise ValueError("supply a RhythmProfile")
    if type(events) not in (list, tuple) or len(events) > MAX_EVENTS:
        raise ValueError("supply a bounded list or tuple of rhythm events")
    if type(beat_segments) not in (list, tuple) or len(beat_segments) > MAX_ANCHORS:
        raise ValueError("supply a bounded list or tuple of beat grid segments")
    if any(type(event) is not RhythmEvent for event in events):
        raise ValueError("supply RhythmEvent records")
    if any(type(segment) is not BeatGridSegment for segment in beat_segments):
        raise ValueError("supply BeatGridSegment records")
    if sum(len(segment.anchors) for segment in beat_segments) > MAX_ANCHORS:
        raise ValueError("the run exceeds the total anchor limit")
    if len({event.event_id for event in events}) != len(events):
        raise ValueError("event IDs must be unique")
    _validate_captures(events, beat_segments)
    indexed = _index_grids(beat_segments)
    positions = tuple(_position(event, indexed.get(event.capture), profile) for event in events)
    evidence = tuple(_grid_evidence(positions, q, i) for i, q in enumerate(profile.subdivisions))
    return RhythmAnalysis(profile, _intervals(events), positions, evidence, _swing(positions))


def event_from_onset(
    onset: OnsetEvent, capture: RhythmCapture, event_id: str, voice: str, *, offbeat: bool = False,
) -> RhythmEvent:
    """Retain the onset estimate and the boundaries from Skill #36."""
    if type(onset) is not OnsetEvent or type(capture) is not RhythmCapture:
        raise ValueError("supply an onset event and a continuous capture")
    if onset.peak.frame.grid.epoch != capture.epoch:
        raise ValueError("map onset and capture to the same clock and tap")
    timing = Availability(onset.ready_sample_exclusive, onset.observed_release_sample_exclusive)
    return RhythmEvent(event_id, voice, capture, onset.estimated_sample_twice, timing, offbeat)


def beat_segments_from_track(track: BeatRun, capture: RhythmCapture) -> tuple[BeatGridSegment, ...]:
    """Retain Skill #37's qualified segments and their whole-run readiness."""
    if type(track) is not BeatRun or type(capture) is not RhythmCapture:
        raise ValueError("supply a beat run and a continuous capture")
    if track.novelty and track.novelty[0].frame.grid.epoch != capture.epoch:
        raise ValueError("map beat run and capture to the same clock and tap")
    timing = Availability(track.ready_sample_exclusive, track.observed_release_sample_exclusive)
    grids = []
    for segment in track.segments:
        if segment.beats:
            anchors = tuple(
                BeatAnchor(f"beat-{beat.center_sample_twice}", beat.center_sample_twice,
                           "supported" if beat.supported else "inferred", timing)
                for beat in segment.beats
            )
            grids.append(BeatGridSegment(capture, anchors))
    return tuple(grids)
