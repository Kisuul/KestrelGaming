"""Exact clock mapping, bounded audio-event association, and decision replay."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable, Literal, Optional, Sequence, Union

from reference_oscilloscope import MAX_SAMPLE_INDEX, ScopeEpoch, _check_integer, _is_label


MAX_SOURCES = 16
MAX_RECORDS = 512
MAX_STEPS = 128
MAX_INTERVALS = 64
Exact = Union[int, Fraction]
Span = tuple[Exact, Exact]
Key = tuple[str, str]
Role = Literal["observation", "estimate", "prediction"]
Disposition = Literal[
    "eligible", "context", "unmapped_source", "incompatible_epoch",
    "outside_mapping", "outside_run", "source_gap",
]


def _exact(value: Exact, name: str) -> Fraction:
    if type(value) not in (int, Fraction):
        raise ValueError(f"{name} must use an integer or exact rational")
    return Fraction(value)


def _coordinate(value: Exact, name: str, origin: Exact = 0) -> Fraction:
    position = _exact(value, name)
    if not origin <= position <= MAX_SAMPLE_INDEX:
        raise ValueError(f"{name} is outside the clock's sample range")
    return position


def _span(span: Span, name: str, origin: int = 0) -> tuple[Fraction, Fraction]:
    if type(span) is not tuple or len(span) != 2:
        raise ValueError(f"{name} must be a half-open pair")
    left, right = (_coordinate(value, name, origin) for value in span)
    if left >= right:
        raise ValueError(f"{name} must have positive duration")
    return left, right


def _validate_identity(source_id: str, event_id: str, revision: int) -> None:
    if not all(map(_is_label, (source_id, event_id))):
        raise ValueError("supply source and event IDs")
    _check_integer(revision, "revision", 0, MAX_SAMPLE_INDEX)


@dataclass(frozen=True)
class ClockMap:
    mapping_id: str
    source: ScopeEpoch
    master: ScopeEpoch
    valid_span: Span
    source_anchor: Exact
    master_anchor: Exact

    def __post_init__(self) -> None:
        if not _is_label(self.mapping_id) or any(
            type(epoch) is not ScopeEpoch for epoch in (self.source, self.master)
        ):
            raise ValueError("supply a named, locked clock mapping between two sample epochs")
        left, right = _span(self.valid_span, "mapping span", self.source.origin_sample)
        _coordinate(self.source_anchor, "source anchor", self.source.origin_sample)
        _coordinate(self.master_anchor, "master anchor", self.master.origin_sample)
        if self.source == self.master and self.source_anchor != self.master_anchor:
            raise ValueError("a mapping from an epoch to itself must preserve its coordinates")
        _span((self._transform(left), self._transform(right)), "mapped span", self.master.origin_sample)

    def _transform(self, value: Exact) -> Fraction:
        return self.master_anchor + (value - self.source_anchor) * (
            self.master.rate_hz / self.source.rate_hz
        )

    def map_position(self, value: Exact) -> Optional[Fraction]:
        point = _coordinate(value, "position", self.source.origin_sample)
        left, right = self.valid_span
        return self._transform(point) if left <= point < right else None

    def map_boundary(self, value: Exact) -> Optional[Fraction]:
        point = _coordinate(value, "boundary", self.source.origin_sample)
        left, right = self.valid_span
        return self._transform(point) if left <= point <= right else None


@dataclass(frozen=True)
class CoverageSpan:
    span: Span
    state: Literal["observed", "gap"]

    def __post_init__(self) -> None:
        _span(self.span, "coverage span")
        if self.state not in ("observed", "gap"):
            raise ValueError("declare observed or missing coverage")


@dataclass(frozen=True)
class SourceRoute:
    source_id: str
    mapping: Optional[ClockMap]
    coverage: tuple[CoverageSpan, ...] = ()

    def __post_init__(self) -> None:
        if not _is_label(self.source_id) or (self.mapping is not None and type(self.mapping) is not ClockMap):
            raise ValueError("supply a source ID and its clock mapping when known")
        if type(self.coverage) is not tuple or len(self.coverage) > MAX_INTERVALS:
            raise ValueError("supply a bounded tuple of coverage spans")
        end = 0
        for item in self.coverage:
            if type(item) is not CoverageSpan or item.span[0] < end:
                raise ValueError("coverage spans must be ordered and disjoint")
            end = item.span[1]
            if item.state == "observed":
                if self.mapping is None:
                    raise ValueError("observed coverage requires a clock mapping")
                first, last = (self.mapping.map_boundary(value) for value in self.mapping.valid_span)
                if not first <= item.span[0] < end <= last:
                    raise ValueError("observed coverage exceeds the clock mapping")


@dataclass(frozen=True)
class FusionRun:
    master: ScopeEpoch
    event_type: str
    span: Span
    maximum_span_samples: Exact
    sources: tuple[SourceRoute, ...]

    def __post_init__(self) -> None:
        if type(self.master) is not ScopeEpoch or not _is_label(self.event_type):
            raise ValueError("supply a master epoch and a target event definition")
        left, right = _span(self.span, "association span", self.master.origin_sample)
        _coordinate(self.maximum_span_samples, "maximum group span")
        if (type(self.sources) is not tuple or not 1 <= len(self.sources) <= MAX_SOURCES
                or any(type(source) is not SourceRoute for source in self.sources)):
            raise ValueError("supply a bounded tuple of source routes")
        if len({source.source_id for source in self.sources}) != len(self.sources):
            raise ValueError("each source must have a unique route")
        for source in self.sources:
            if source.mapping is not None and source.mapping.master != self.master:
                raise ValueError("all source mappings must target the declared master epoch")
            if any(item.span[0] < left or item.span[1] > right for item in source.coverage):
                raise ValueError("source coverage exceeds the association span")


@dataclass(frozen=True)
class Event:
    source_id: str
    event_id: str
    event_type: str
    epoch: ScopeEpoch
    position_sample: Exact
    support: tuple[Span, ...]
    ready_sample_exclusive: Optional[Exact]
    revision: int = 0
    role: Role = "estimate"
    weight: Exact = 1
    observed_release_sample_exclusive: Optional[Exact] = None

    def __post_init__(self) -> None:
        _validate_identity(self.source_id, self.event_id, self.revision)
        if not _is_label(self.event_type) or type(self.epoch) is not ScopeEpoch:
            raise ValueError("supply the native epoch and event definition")
        if self.role not in ("observation", "estimate", "prediction"):
            raise ValueError("declare an observation, estimate, or prediction")
        if _exact(self.weight, "weight") <= 0:
            raise ValueError("weight must be positive")
        origin = self.epoch.origin_sample
        _coordinate(self.position_sample, "event position", origin)
        if type(self.support) is not tuple or not 1 <= len(self.support) <= MAX_INTERVALS:
            raise ValueError("supply one or more native evidence intervals")
        required_end = max(_span(span, "native evidence span", origin)[1] for span in self.support)
        ready = self.ready_sample_exclusive
        if ready is not None:
            required_end = _coordinate(ready, "data readiness", required_end)
        release = self.observed_release_sample_exclusive
        if release is not None:
            _coordinate(release, "reported evidence delivery", required_end)


@dataclass(frozen=True)
class EventEvidence:
    event: Event
    disposition: Disposition
    mapping: Optional[ClockMap] = None
    position_sample: Optional[Fraction] = None
    support: tuple[Span, ...] = ()
    ready_sample_exclusive: Optional[Fraction] = None
    evidence_release_sample_exclusive: Optional[Fraction] = None


@dataclass(frozen=True)
class FusedGroup:
    anchor_sample: Fraction
    gate_end_sample: Fraction
    position_sample: Fraction
    members: tuple[EventEvidence, ...]
    competitors: tuple[EventEvidence, ...]
    residual_samples: tuple[Fraction, ...]
    support: tuple[Span, ...]
    incomplete_sources: tuple[str, ...]
    data_ready_sample_exclusive: Optional[Fraction]
    evidence_release_sample_exclusive: Optional[Fraction]


@dataclass(frozen=True)
class FusionResult:
    run: FusionRun
    groups: tuple[FusedGroup, ...]
    excluded: tuple[EventEvidence, ...]


def _map_event(event: Event, route: Optional[SourceRoute], run: FusionRun) -> EventEvidence:
    if route is None or route.mapping is None:
        return EventEvidence(event, "unmapped_source")
    clock = route.mapping
    if event.epoch != clock.source:
        return EventEvidence(event, "incompatible_epoch", clock)
    position = clock.map_position(event.position_sample)
    valid_start, valid_end = clock.valid_span
    if position is None or any(a < valid_start or b > valid_end for a, b in event.support):
        return EventEvidence(event, "outside_mapping", clock, position)

    if event.role == "prediction" or event.event_type != run.event_type:
        disposition = "context"
    elif not run.span[0] <= position < run.span[1]:
        disposition = "outside_run"
    elif any(item.state == "gap" and item.span[0] <= position < item.span[1] for item in route.coverage):
        disposition = "source_gap"
    else:
        disposition = "eligible"

    ready, release = event.ready_sample_exclusive, event.observed_release_sample_exclusive
    support = tuple((clock._transform(a), clock._transform(b)) for a, b in event.support)
    return EventEvidence(
        event, disposition, clock, position, support,
        None if ready is None else clock.map_boundary(ready),
        None if release is None else clock.map_boundary(release),
    )


def _union(spans: Iterable[Span]) -> tuple[Span, ...]:
    merged = []
    for left, right in sorted(spans):
        if merged and merged[-1][1] >= left:
            merged[-1] = (merged[-1][0], max(merged[-1][1], right))
        else:
            merged.append((left, right))
    return tuple(merged)


def _latest_known(values: Iterable[Optional[Exact]]) -> Optional[Fraction]:
    values = tuple(values)
    return Fraction(max(values)) if all(value is not None for value in values) else None


def _group(run: FusionRun, records: list[EventEvidence], competitors: list[EventEvidence],
           gate_end: Fraction, observed: dict[str, tuple[Span, ...]]) -> FusedGroup:
    anchor = records[0].position_sample
    weights = [row.event.weight for row in records]
    position = sum(row.position_sample * w for row, w in zip(records, weights)) / sum(weights)
    run_end = run.span[1]
    # The gate includes its right endpoint, except where the run ends.
    incomplete = tuple(
        source for source, spans in observed.items()
        if not any(left <= anchor and (right > gate_end or right == run_end)
                   for left, right in spans)
    )
    return FusedGroup(
        anchor, gate_end, position, tuple(records), tuple(competitors),
        tuple(row.position_sample - position for row in records),
        _union(span for row in records for span in row.support), incomplete,
        _latest_known(row.ready_sample_exclusive for row in records),
        _latest_known(row.evidence_release_sample_exclusive for row in records),
    )


def _summarize(run: FusionRun, records: Iterable[EventEvidence]) -> FusionResult:
    by_identity = sorted(records, key=lambda row: (row.event.source_id, row.event.event_id))
    remaining = sorted(
        (row for row in by_identity if row.disposition == "eligible"),
        key=lambda row: row.position_sample,
    )
    excluded = tuple(row for row in by_identity if row.disposition != "eligible")
    observed = {
        src.source_id: _union(item.span for item in src.coverage if item.state == "observed")
        for src in sorted(run.sources, key=lambda src: src.source_id)
    }
    groups = []
    while remaining:
        gate_end = remaining[0].position_sample + run.maximum_span_samples
        seen, members, competitors = set(), [], []
        consumed = 0
        for row in remaining:
            if row.position_sample > gate_end:
                break
            consumed += 1
            if row.event.source_id in seen:
                competitors.append(row)
            else:
                seen.add(row.event.source_id)
                members.append(row)
        groups.append(_group(run, members, competitors, gate_end, observed))
        remaining = competitors + remaining[consumed:]
    return FusionResult(run, tuple(groups), excluded)


def fuse_offline(run: FusionRun, events: Sequence[Event]) -> FusionResult:
    """Group a bounded snapshot containing one current revision per event ID and source."""
    if type(run) is not FusionRun or type(events) not in (list, tuple) or len(events) > MAX_RECORDS:
        raise ValueError("supply a fusion run and a bounded event snapshot")
    routes = {source.source_id: source for source in run.sources}
    records: dict[Key, EventEvidence] = {}
    for event in events:
        if type(event) is not Event:
            raise ValueError("an offline snapshot contains events only")
        key = event.source_id, event.event_id
        if key in records:
            raise ValueError("supply one current event per source and event ID")
        records[key] = _map_event(event, routes.get(event.source_id), run)
    return _summarize(run, records.values())


@dataclass(frozen=True)
class Retraction:
    source_id: str
    event_id: str
    revision: int

    def __post_init__(self) -> None:
        _validate_identity(self.source_id, self.event_id, self.revision)


@dataclass(frozen=True)
class Frontier:
    source_id: str
    position_sample: Optional[Exact]
    ready_sample_exclusive: Optional[Exact] = None

    def __post_init__(self) -> None:
        if not _is_label(self.source_id):
            raise ValueError("supply a source ID for the frontier")
        if self.position_sample is not None:
            _coordinate(self.position_sample, "frontier position")
        if self.ready_sample_exclusive is not None:
            _coordinate(self.ready_sample_exclusive, "frontier readiness")


@dataclass(frozen=True)
class DispatchStamp:
    clock_id: str
    seconds: Exact

    def __post_init__(self) -> None:
        if not _is_label(self.clock_id):
            raise ValueError("name the dispatch clock")
        _exact(self.seconds, "dispatch time")


@dataclass(frozen=True)
class ReplayStep:
    changes: tuple[Union[Event, Retraction], ...] = ()
    frontiers: tuple[Frontier, ...] = ()
    dispatch: Optional[DispatchStamp] = None


@dataclass(frozen=True)
class CommittedGroup:
    group: FusedGroup
    frontiers: tuple[Frontier, ...]
    decision_ready_sample_exclusive: Optional[Fraction]
    dispatch: Optional[DispatchStamp]


@dataclass(frozen=True)
class ReplayFrame:
    step: ReplayStep
    newly_committed: tuple[CommittedGroup, ...]
    provisional: tuple[FusedGroup, ...]
    excluded: tuple[EventEvidence, ...]


def _behind_frontier(row: Optional[EventEvidence], frontier: Optional[Frontier]) -> bool:
    return (row is not None and row.disposition == "eligible" and frontier is not None
            and (frontier.position_sample is None or row.position_sample < frontier.position_sample))


def _update_event(change: Union[Event, Retraction], run: FusionRun, routes: dict[str, SourceRoute],
                  progress: dict[str, Frontier], active: dict[Key, EventEvidence],
                  revisions: dict[Key, int]) -> None:
    if type(change) not in (Event, Retraction):
        raise ValueError("supply event records or retractions")
    key = change.source_id, change.event_id
    previous = active.get(key)
    if change.revision <= revisions.get(key, -1):
        raise ValueError("revisions must increase for each source and event ID")
    if type(change) is Retraction and previous is None:
        raise ValueError("a retraction requires an active event")
    current = _map_event(change, routes.get(change.source_id), run) if type(change) is Event else None
    frontier = progress.get(change.source_id)
    if _behind_frontier(previous, frontier) or _behind_frontier(current, frontier):
        raise ValueError("event change violates a guaranteed frontier")
    if current is None:
        del active[key]
    else:
        active[key] = current
    revisions[key] = change.revision


def _advance_frontier(item: Frontier, run: FusionRun, routes: dict[str, SourceRoute],
                      progress: dict[str, Frontier]) -> None:
    if type(item) is not Frontier or item.source_id not in routes:
        raise ValueError("frontier requires a declared source in this run")
    before = progress.get(item.source_id)
    point = item.position_sample
    if before is not None and (
        before.position_sample is None or (point is not None and point < before.position_sample)
    ):
        raise ValueError("frontiers cannot retreat or advance after source finalization")
    if point is not None:
        if routes[item.source_id].mapping is None:
            raise ValueError("a finite frontier requires a source mapping")
        _coordinate(point, "frontier position", run.master.origin_sample)
    if item.ready_sample_exclusive is not None:
        _coordinate(item.ready_sample_exclusive, "frontier readiness", run.master.origin_sample)
    progress[item.source_id] = item


def replay_fusion(run: FusionRun, steps: Sequence[ReplayStep]) -> tuple[ReplayFrame, ...]:
    """Apply arrival batches and report each decision on the supplied trace."""
    if type(run) is not FusionRun or type(steps) not in (list, tuple) or len(steps) > MAX_STEPS:
        raise ValueError("supply a fusion run and a bounded replay")
    for step in steps:
        if (type(step) is not ReplayStep or type(step.changes) is not tuple
                or type(step.frontiers) is not tuple or len(step.frontiers) > MAX_SOURCES
                or (step.dispatch is not None and type(step.dispatch) is not DispatchStamp)):
            raise ValueError("each replay step needs bounded change and frontier tuples")
    if sum(len(step.changes) for step in steps) > MAX_RECORDS:
        raise ValueError("replay exceeds the event or revision bound")

    routes = {source.source_id: source for source in run.sources}
    active: dict[Key, EventEvidence] = {}
    revisions: dict[Key, int] = {}
    progress: dict[str, Frontier] = {}
    committed: list[CommittedGroup] = []
    history = []
    for step in steps:
        for change in step.changes:
            _update_event(change, run, routes, progress, active, revisions)
        for item in step.frontiers:
            _advance_frontier(item, run, routes, progress)

        result = _summarize(run, active.values())
        previous_count = len(committed)
        if tuple(item.group for item in committed) != result.groups[:previous_count]:
            raise RuntimeError("guaranteed frontiers must preserve committed groups")
        frontiers = tuple(progress[key] for key in sorted(progress))
        for group in result.groups[previous_count:]:
            if len(frontiers) < len(routes) or any(
                f.position_sample is not None and f.position_sample <= group.gate_end_sample
                for f in frontiers
            ):
                break
            required = [f.ready_sample_exclusive for f in frontiers]
            required.extend(row.ready_sample_exclusive for row in group.members + group.competitors)
            if committed:
                required.append(committed[-1].decision_ready_sample_exclusive)
            committed.append(CommittedGroup(group, frontiers, _latest_known(required), step.dispatch))

        history.append(ReplayFrame(
            step, tuple(committed[previous_count:]), result.groups[len(committed):], result.excluded,
        ))
    return tuple(history)
