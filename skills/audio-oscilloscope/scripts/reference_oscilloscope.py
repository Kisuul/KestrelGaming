"""Bounded offline reference for sample-clocked captures and display projection."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from fractions import Fraction
from itertools import islice
from math import isfinite
from typing import Literal, Sequence, Union


MAX_CHANNELS = 8
MAX_HISTORY_FRAMES = 1024
MAX_BLOCK_FRAMES = 256
MAX_SAMPLE_INDEX = 2**256 - 1

PCMSample = Union[int, float]
Planes = tuple[tuple[PCMSample, ...], ...]


def _check_integer(value: int, name: str, minimum: int, maximum: int) -> None:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an integer in [{minimum}, {maximum}]")


def _is_label(value: str) -> bool:
    return type(value) is str and bool(value.strip())


def _freeze_planes(
    planes: Sequence[Sequence[PCMSample]], channels: int, max_frames: int
) -> Planes:
    if type(planes) not in (list, tuple) or len(planes) != channels:
        raise ValueError("provide one plane per declared channel")
    if any(type(plane) not in (list, tuple) for plane in planes):
        raise ValueError("each channel plane must be a list or tuple")

    size = len(planes[0])
    _check_integer(size, "frame count", 1, max_frames)
    if any(len(plane) != size for plane in planes):
        raise ValueError("channel planes must have equal frame counts")

    frozen = tuple(tuple(plane) for plane in planes)
    for plane in frozen:
        for sample in plane:
            if type(sample) is int and -(2**31) <= sample < 2**31:
                continue
            if type(sample) is float and isfinite(sample):
                continue
            raise ValueError("PCM must use finite floats or signed 32-bit integers")
    return frozen


@dataclass(frozen=True)
class ScopeEpoch:
    epoch_id: str
    origin_sample: int
    rate_hz: Fraction
    clock_domain: str
    tap_id: str
    units: str
    channel_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _check_integer(self.origin_sample, "epoch origin", 0, MAX_SAMPLE_INDEX)
        if type(self.rate_hz) is not Fraction or self.rate_hz <= 0:
            raise ValueError("rate_hz must be a positive Fraction")
        if not all(map(_is_label, (self.epoch_id, self.clock_domain, self.tap_id, self.units))):
            raise ValueError("epoch, clock, tap, and units must have nonempty labels")
        labels = self.channel_ids
        if type(labels) is not tuple or not 1 <= len(labels) <= MAX_CHANNELS:
            raise ValueError(f"channel_ids must be a tuple of 1 to {MAX_CHANNELS} labels")
        if not all(map(_is_label, labels)) or len(set(labels)) != len(labels):
            raise ValueError("channel labels must be nonempty and unique")


@dataclass(frozen=True)
class CaptureWindow:
    """One complete interval with samples in declared channel order."""

    epoch: ScopeEpoch
    start_sample: int
    planes: Planes

    def __post_init__(self) -> None:
        if type(self.epoch) is not ScopeEpoch:
            raise ValueError("capture requires a ScopeEpoch")
        _check_integer(self.start_sample, "capture start", self.epoch.origin_sample, MAX_SAMPLE_INDEX)
        planes = _freeze_planes(self.planes, len(self.epoch.channel_ids), MAX_HISTORY_FRAMES)
        if self.start_sample + len(planes[0]) > MAX_SAMPLE_INDEX:
            raise ValueError("capture exclusive end exceeds the sample index range")
        object.__setattr__(self, "planes", planes)

    @property
    def frame_count(self) -> int:
        return len(self.planes[0])

    @property
    def end_sample_exclusive(self) -> int:
        return self.start_sample + self.frame_count

    @property
    def center_sample_twice(self) -> int:
        return self.start_sample + self.end_sample_exclusive - 1


class ScopeAcquisition:
    """One contiguous producer per epoch. The caller owns presentation timing."""

    def __init__(
        self, epoch: ScopeEpoch, *, window_frames: int, hop_frames: int, history_frames: int
    ) -> None:
        _check_integer(history_frames, "history_frames", 1, MAX_HISTORY_FRAMES)
        _check_integer(window_frames, "window_frames", 1, history_frames)
        _check_integer(hop_frames, "hop_frames", 1, MAX_SAMPLE_INDEX)
        self._window_frames = window_frames
        self._hop_frames = hop_frames
        self._history_frames = history_frames
        self._used_epoch_ids: set[str] = set()
        self.reset_epoch(epoch)

    @property
    def epoch(self) -> ScopeEpoch:
        return self._epoch

    @property
    def next_sample(self) -> int:
        return self._next_sample

    @property
    def next_capture_end(self) -> int:
        return self._next_capture_end

    def reset_epoch(self, epoch: ScopeEpoch) -> None:
        """Clear history and restart the capture grid at a fresh origin."""
        if type(epoch) is not ScopeEpoch:
            raise ValueError("reset requires a ScopeEpoch")
        if epoch.epoch_id in self._used_epoch_ids:
            raise ValueError("epoch identifier has already been used")
        first_end = epoch.origin_sample + self._window_frames
        if first_end > MAX_SAMPLE_INDEX:
            raise ValueError("first capture exclusive end exceeds the sample index range")
        history = tuple(deque(maxlen=self._history_frames) for _ in epoch.channel_ids)

        self._used_epoch_ids.add(epoch.epoch_id)
        self._history = history
        self._epoch = epoch
        self._next_sample = epoch.origin_sample
        self._next_capture_end = first_end

    def ingest(
        self, *, epoch: ScopeEpoch, start_sample: int, planes: Sequence[Sequence[PCMSample]]
    ) -> tuple[CaptureWindow, ...]:
        """Validate the full block, then return every newly complete window."""
        if type(epoch) is not ScopeEpoch or epoch != self._epoch:
            raise ValueError("block metadata must match the active epoch")
        _check_integer(start_sample, "block start", 0, MAX_SAMPLE_INDEX)
        if start_sample != self._next_sample:
            kind = "gap" if start_sample > self._next_sample else "overlap"
            raise ValueError(f"{kind}: expected start={self._next_sample}, observed={start_sample}")

        samples = _freeze_planes(planes, len(epoch.channel_ids), MAX_BLOCK_FRAMES)
        block_end = start_sample + len(samples[0])
        if block_end > MAX_SAMPLE_INDEX:
            raise ValueError("block exclusive end exceeds the sample index range")

        captures = []
        while self._next_sample < block_end:
            end = min(block_end, self._next_capture_end)
            left = self._next_sample - start_sample
            right = end - start_sample
            for retained, plane in zip(self._history, samples):
                retained.extend(plane[left:right])
            self._next_sample = end

            if end == self._next_capture_end:
                # Take the newest window from each channel in chronological order.
                snapshot = tuple(
                    tuple(islice(reversed(retained), self._window_frames))[::-1]
                    for retained in self._history
                )
                captures.append(CaptureWindow(self._epoch, end - self._window_frames, snapshot))
                self._next_capture_end += self._hop_frames
        return tuple(captures)


@dataclass(frozen=True)
class ChannelExtrema:
    minimum: PCMSample
    maximum: PCMSample
    minimum_sample: int
    maximum_sample: int


@dataclass(frozen=True)
class ScopeBucket:
    start_sample: int
    end_sample_exclusive: int
    extrema: tuple[ChannelExtrema, ...]


@dataclass(frozen=True)
class ScopePoint:
    sample_index: int
    values: tuple[PCMSample, ...]


@dataclass(frozen=True)
class ScopeProjection:
    mode: Literal["min_max", "points"]
    epoch: ScopeEpoch
    start_sample: int
    end_sample_exclusive: int
    width: int
    buckets: tuple[ScopeBucket, ...] = ()
    points: tuple[ScopePoint, ...] = ()


def _extrema(plane: tuple[PCMSample, ...], left: int, right: int, start: int) -> ChannelExtrema:
    low = high = left
    for offset in range(left + 1, right):
        if plane[offset] < plane[low]:
            low = offset
        if plane[offset] > plane[high]:
            high = offset
    return ChannelExtrema(plane[low], plane[high], start + low, start + high)


def project_waveform(capture: CaptureWindow, *, width: int) -> ScopeProjection:
    """Project one immutable capture at the requested display width."""
    if type(capture) is not CaptureWindow:
        raise ValueError("projection requires a CaptureWindow")
    if type(width) is not int or width < 1:
        raise ValueError("width must be a positive integer")

    start = capture.start_sample
    end = capture.end_sample_exclusive
    length = capture.frame_count
    if width > length:
        points = tuple(
            ScopePoint(index, values) for index, values in enumerate(zip(*capture.planes), start)
        )
        return ScopeProjection("points", capture.epoch, start, end, width, points=points)

    buckets = []
    left = 0
    for column in range(width):
        right = (column + 1) * length // width
        extrema = tuple(_extrema(plane, left, right, start) for plane in capture.planes)
        buckets.append(ScopeBucket(start + left, start + right, extrema))
        left = right
    return ScopeProjection("min_max", capture.epoch, start, end, width, buckets=tuple(buckets))
