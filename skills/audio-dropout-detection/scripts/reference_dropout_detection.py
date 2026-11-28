"""Bounded source coverage, playout provenance, and quiet-window evidence."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from fractions import Fraction
from math import isfinite
from typing import Literal, Sequence

from reference_levels import sample_levels
from reference_oscilloscope import (
    MAX_BLOCK_FRAMES,
    MAX_SAMPLE_INDEX,
    PCMSample,
    ScopeEpoch,
    _check_integer,
    _freeze_planes,
)
from reference_timebase import DiscontinuityError, SampleRate, SampleTimeline


@dataclass(frozen=True)
class FrameInterval:
    start_sample: int
    end_sample_exclusive: int

    def __post_init__(self) -> None:
        _check_integer(self.start_sample, "interval start", 0, MAX_SAMPLE_INDEX)
        _check_integer(self.end_sample_exclusive, "interval end", self.start_sample + 1, MAX_SAMPLE_INDEX)

    @property
    def frames(self) -> int:
        return self.end_sample_exclusive - self.start_sample


def _block_interval(start_sample: int, frames: int) -> FrameInterval:
    _check_integer(frames, "block frames", 1, MAX_BLOCK_FRAMES)
    _check_integer(start_sample, "block start", 0, MAX_SAMPLE_INDEX - frames)
    return FrameInterval(start_sample, start_sample + frames)


def _rate(epoch: ScopeEpoch) -> SampleRate:
    if type(epoch) is not ScopeEpoch:
        raise ValueError("provide a ScopeEpoch")
    return SampleRate(epoch.rate_hz.numerator, epoch.rate_hz.denominator)


def _timeline(epoch: ScopeEpoch) -> SampleTimeline:
    rate = _rate(epoch)
    return SampleTimeline(epoch.epoch_id, epoch.origin_sample, rate, len(epoch.channel_ids))


def _reset(clock: SampleTimeline, epoch: ScopeEpoch) -> None:
    rate = _rate(epoch)
    clock.reset_epoch(epoch.epoch_id, epoch.origin_sample, rate, len(epoch.channel_ids))


def _check_epoch(epoch: ScopeEpoch, current: ScopeEpoch) -> None:
    if type(epoch) is not ScopeEpoch or epoch != current:
        raise ValueError("block must use the current epoch")


def _declared_gap(current: ScopeEpoch, frontier: int, next_epoch: ScopeEpoch) -> FrameInterval:
    _rate(next_epoch)
    if (
        current.clock_domain != next_epoch.clock_domain
        or current.rate_hz != next_epoch.rate_hz
        or current.tap_id != next_epoch.tap_id
        or current.units != next_epoch.units
        or current.channel_ids != next_epoch.channel_ids
        or next_epoch.origin_sample <= frontier
    ):
        raise ValueError("declare a nonempty gap on the same source clock, tap, and channel layout")
    return FrameInterval(frontier, next_epoch.origin_sample)


@dataclass(frozen=True)
class CoverageUpdate:
    epoch: ScopeEpoch
    offered: FrameInterval
    expected_start_sample: int
    status: Literal["accepted", "forward_gap", "early_start"]
    provisional_gap: FrameInterval | None = None
    overlap: FrameInterval | None = None

    @property
    def start_delta_frames(self) -> int:
        return self.offered.start_sample - self.expected_start_sample


@dataclass(frozen=True)
class ConfirmedGap:
    before: ScopeEpoch
    after: ScopeEpoch
    missing: FrameInterval

    @property
    def duration_seconds(self) -> Fraction:
        return Fraction(self.missing.frames) / self.before.rate_hz


class SourceCoverage:
    """Audit trusted source positions without accepting discontinuous blocks."""

    def __init__(self, epoch: ScopeEpoch) -> None:
        self._clock = _timeline(epoch)
        self._epoch = epoch

    @property
    def next_sample(self) -> int:
        return self._clock.next_sample

    def ingest(self, *, epoch: ScopeEpoch, start_sample: int, frame_count: int) -> CoverageUpdate:
        _check_epoch(epoch, self._epoch)
        offered = _block_interval(start_sample, frame_count)
        expected = self.next_sample
        try:
            self._clock.ingest(start_sample, frame_count, len(epoch.channel_ids))
        except DiscontinuityError as exc:
            if exc.kind == "gap":
                gap = FrameInterval(expected, start_sample)
                return CoverageUpdate(epoch, offered, expected, "forward_gap", provisional_gap=gap)
            start = max(epoch.origin_sample, start_sample)
            stop = min(expected, offered.end_sample_exclusive)
            overlap = FrameInterval(start, stop) if start < stop else None
            return CoverageUpdate(epoch, offered, expected, "early_start", overlap=overlap)
        return CoverageUpdate(epoch, offered, expected, "accepted")

    def reset_epoch(self, epoch: ScopeEpoch, *, confirm_gap: bool = False) -> ConfirmedGap | None:
        """Start a fresh epoch and report a gap only when the caller confirms it."""
        if type(confirm_gap) is not bool:
            raise ValueError("confirm_gap must be a bool")
        gap = _declared_gap(self._epoch, self.next_sample, epoch) if confirm_gap else None
        previous = self._epoch
        _reset(self._clock, epoch)
        self._epoch = epoch
        return ConfirmedGap(previous, epoch, gap) if gap is not None else None


PlayoutKind = Literal["original", "zero_fill", "repeat", "other_concealment", "unrendered", "unknown"]
_REPLACEMENT_KINDS = ("zero_fill", "repeat", "other_concealment")


@dataclass(frozen=True)
class PlayoutSegment:
    interval: FrameInterval
    kind: PlayoutKind

    def __post_init__(self) -> None:
        kinds = ("original", *_REPLACEMENT_KINDS, "unrendered", "unknown")
        if type(self.interval) is not FrameInterval or type(self.kind) is not str or self.kind not in kinds:
            raise ValueError("provide an interval and a recognized playout provenance kind")


@dataclass(frozen=True)
class PlayoutReport:
    epoch: ScopeEpoch
    requested: FrameInterval
    segments: tuple[PlayoutSegment, ...]
    original_frames: int
    replacement_frames: int
    unrendered_frames: int
    unknown_frames: int


def summarize_playout(
    *, epoch: ScopeEpoch, start_sample: int, frame_count: int, segments: Sequence[PlayoutSegment],
) -> PlayoutReport:
    """Validate explicit provenance over a complete, nonoverlapping output request."""
    _rate(epoch)
    requested = _block_interval(start_sample, frame_count)
    if start_sample < epoch.origin_sample:
        raise ValueError("playout request begins before the epoch")
    if type(segments) not in (list, tuple) or not 1 <= len(segments) <= frame_count:
        raise ValueError("provide a partition of the requested playout frames")
    frozen = tuple(segments)
    counts: Counter[str] = Counter()
    cursor = start_sample
    for segment in frozen:
        if type(segment) is not PlayoutSegment or segment.interval.start_sample != cursor:
            raise ValueError("playout segments must be ordered and contiguous")
        cursor = segment.interval.end_sample_exclusive
        counts[segment.kind] += segment.interval.frames
    if cursor != requested.end_sample_exclusive:
        raise ValueError("playout segments must exactly cover the requested interval")
    return PlayoutReport(
        epoch, requested, frozen, counts["original"],
        sum(counts[kind] for kind in _REPLACEMENT_KINDS), counts["unrendered"], counts["unknown"],
    )


@dataclass(frozen=True)
class QuietProfile:
    window_frames: int
    minimum_quiet_frames: int
    quiet_rms_max: float
    active_rms_min: float
    relative_quiet_max: float

    def __post_init__(self) -> None:
        _check_integer(self.window_frames, "window frames", 1, MAX_BLOCK_FRAMES)
        _check_integer(self.minimum_quiet_frames, "minimum quiet frames", 1, MAX_SAMPLE_INDEX)
        for value in (self.quiet_rms_max, self.active_rms_min, self.relative_quiet_max):
            try:
                valid = type(value) in (float, int) and isfinite(value)
            except OverflowError:
                valid = False
            if not valid:
                raise ValueError("quiet profile levels must be finite real values")
        if not 0 <= self.quiet_rms_max < self.active_rms_min:
            raise ValueError("require 0 <= quiet RMS limit < active RMS floor")
        if not 0 <= self.relative_quiet_max <= 1:
            raise ValueError("relative quiet limit must be in [0, 1]")


@dataclass(frozen=True)
class QuietCandidate:
    channel_id: str
    quiet: FrameInterval
    support: FrameInterval
    quiet_rms_max: float
    before_rms: float
    after_rms: float
    ratio: Fraction

    @property
    def ready_sample_exclusive(self) -> int:
        return self.support.end_sample_exclusive


BoundaryReason = Literal["gap", "epoch_change", "end_of_input", "unusable_window"]


@dataclass(frozen=True)
class IncompleteQuiet:
    channel_id: str
    quiet: FrameInterval
    before_rms: float | None
    quiet_rms_max: float
    reason: BoundaryReason


@dataclass(frozen=True)
class QuietUpdate:
    epoch: ScopeEpoch
    profile: QuietProfile
    observed_end_sample_exclusive: int
    candidates: tuple[QuietCandidate, ...]
    incomplete: tuple[IncompleteQuiet, ...]
    finalized: bool


@dataclass
class _QuietRun:
    start_sample: int
    end_sample_exclusive: int
    before_rms: float | None
    maximum_rms: float

    @property
    def interval(self) -> FrameInterval:
        return FrameInterval(self.start_sample, self.end_sample_exclusive)


@dataclass
class _Channel:
    channel_id: str
    previous_active_rms: float | None = None
    run: _QuietRun | None = None


def _window_rms(values: list[PCMSample]) -> float | None:
    # Scale before using the RMS oracle so its mean-square calculation stays finite.
    peak = max(map(abs, values))
    if peak == 0:
        return 0.0
    normalized = [value / peak for value in values]
    rms = peak * sample_levels(normalized)["rms"]
    return rms if rms > 0 else None


class QuietDetector:
    """Measure channel-specific quiet candidates on the epoch's fixed window grid."""

    def __init__(self, epoch: ScopeEpoch, profile: QuietProfile) -> None:
        if type(profile) is not QuietProfile:
            raise ValueError("provide a QuietProfile")
        self._clock = _timeline(epoch)
        self._profile = profile
        self._relative_limit = Fraction(profile.relative_quiet_max)
        self._start_epoch(epoch)

    def _start_epoch(self, epoch: ScopeEpoch) -> None:
        self._epoch = epoch
        self._channels = [_Channel(channel) for channel in epoch.channel_ids]
        self._buffers: list[list[PCMSample]] = [[] for _ in epoch.channel_ids]
        self._window_usable = True
        self._finalized = False

    @property
    def next_sample(self) -> int:
        return self._clock.next_sample

    @staticmethod
    def _end_incomplete(channel: _Channel, reason: BoundaryReason, result: list[IncompleteQuiet]) -> None:
        if channel.run is not None:
            run = channel.run
            result.append(IncompleteQuiet(channel.channel_id, run.interval, run.before_rms, run.maximum_rms, reason))
            channel.run = None

    def _measure_window(
        self, end: int, candidates: list[QuietCandidate], incomplete: list[IncompleteQuiet],
    ) -> None:
        width = self._profile.window_frames
        for channel, buffer in zip(self._channels, self._buffers):
            rms = _window_rms(buffer) if self._window_usable else None
            buffer.clear()
            if rms is None:
                self._end_incomplete(channel, "unusable_window", incomplete)
                channel.previous_active_rms = None
                continue
            run = channel.run
            if rms <= self._profile.quiet_rms_max:
                if run is None:
                    channel.run = _QuietRun(end - width, end, channel.previous_active_rms, rms)
                else:
                    run.end_sample_exclusive = end
                    run.maximum_rms = max(run.maximum_rms, rms)
                channel.previous_active_rms = None
                continue
            active = rms >= self._profile.active_rms_min
            if (
                active and run is not None and run.before_rms is not None
                and run.end_sample_exclusive - run.start_sample >= self._profile.minimum_quiet_frames
            ):
                ratio = Fraction(run.maximum_rms) / Fraction(min(run.before_rms, rms))
                if ratio <= self._relative_limit:
                    support = FrameInterval(run.start_sample - width, end)
                    candidates.append(
                        QuietCandidate(channel.channel_id, run.interval, support, run.maximum_rms,
                                       run.before_rms, rms, ratio)
                    )
            channel.run = None
            channel.previous_active_rms = rms if active else None
        self._window_usable = True

    def ingest(
        self, *, epoch: ScopeEpoch, start_sample: int, planes: Sequence[Sequence[PCMSample]],
        usable: Sequence[bool] | None = None,
    ) -> QuietUpdate:
        """Accept one validated block, with optional per-frame evidence eligibility."""
        _check_epoch(epoch, self._epoch)
        if self._finalized:
            raise ValueError("start a new epoch after finalizing")
        frozen = _freeze_planes(planes, len(self._channels), MAX_BLOCK_FRAMES)
        size = len(frozen[0])
        interval = _block_interval(start_sample, size)
        if usable is not None:
            if type(usable) not in (tuple, list) or len(usable) != size or any(type(x) is not bool for x in usable):
                raise ValueError("provide one bool per frame when declaring eligibility")
            usable = tuple(usable)
        self._clock.ingest(start_sample, size, len(self._channels))

        candidates: list[QuietCandidate] = []
        incomplete: list[IncompleteQuiet] = []
        offset = 0
        width = self._profile.window_frames
        while offset < size:
            stop = min(size, offset + width - len(self._buffers[0]))
            for buffer, plane in zip(self._buffers, frozen):
                buffer.extend(plane[offset:stop])
            if usable is not None:
                self._window_usable = self._window_usable and all(usable[offset:stop])
            offset = stop
            if len(self._buffers[0]) == width:
                self._measure_window(start_sample + offset, candidates, incomplete)
        return QuietUpdate(
            epoch, self._profile, interval.end_sample_exclusive, tuple(candidates), tuple(incomplete), False,
        )

    def _close(self, reason: BoundaryReason, end: int) -> QuietUpdate:
        incomplete: list[IncompleteQuiet] = []
        for channel in self._channels:
            self._end_incomplete(channel, reason, incomplete)
        for buffer in self._buffers:
            buffer.clear()
        self._finalized = True
        return QuietUpdate(self._epoch, self._profile, end, (), tuple(incomplete), True)

    def finish(self) -> QuietUpdate:
        return self._close("end_of_input", self.next_sample)

    def reset_epoch(
        self, epoch: ScopeEpoch, *, reason: Literal["gap", "epoch_change"] = "epoch_change",
    ) -> QuietUpdate:
        if type(reason) is not str or reason not in ("gap", "epoch_change"):
            raise ValueError("declare a gap or an epoch change")
        old_end = self.next_sample
        if reason == "gap":
            _declared_gap(self._epoch, old_end, epoch)
        _reset(self._clock, epoch)
        previous = self._close(reason, old_end)
        self._start_epoch(epoch)
        return previous
