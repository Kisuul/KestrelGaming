"""Exact sample-clock edge triggering and capture for prepared PCM."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from fractions import Fraction
from math import isfinite
from typing import Literal, Sequence

from reference_oscilloscope import (
    CaptureWindow,
    MAX_BLOCK_FRAMES,
    MAX_HISTORY_FRAMES,
    MAX_SAMPLE_INDEX,
    PCMSample,
    ScopeEpoch,
)


@dataclass(frozen=True)
class TriggerSettings:
    """Level and hysteresis use the units of the selected channel."""

    channel_id: str
    direction: Literal["rising", "falling"] = "rising"
    level: PCMSample = 0
    hysteresis: PCMSample = 0
    pre_frames: int = 0
    post_frames: int = 0
    holdoff_frames: int = 0
    mode: Literal["normal", "single"] = "normal"

    def __post_init__(self) -> None:
        if type(self.channel_id) is not str or not self.channel_id.strip():
            raise ValueError("channel_id must be a nonempty label")
        if self.direction not in ("rising", "falling"):
            raise ValueError("direction must be rising or falling")
        if self.mode not in ("normal", "single"):
            raise ValueError("mode must be normal or single")
        for name, value in (("level", self.level), ("hysteresis", self.hysteresis)):
            if type(value) is not int and (type(value) is not float or not isfinite(value)):
                raise ValueError(f"{name} must be a finite float or integer")
        if self.hysteresis < 0:
            raise ValueError("hysteresis must be nonnegative")
        counts = (self.pre_frames, self.post_frames, self.holdoff_frames)
        if any(type(count) is not int or not 0 <= count <= MAX_SAMPLE_INDEX for count in counts):
            raise ValueError("pre, post, and holdoff counts must be nonnegative sample integers")
        if self.pre_frames + self.post_frames + 1 > MAX_HISTORY_FRAMES:
            raise ValueError(f"capture length must be at most {MAX_HISTORY_FRAMES} frames")


@dataclass(frozen=True)
class CrossingDecision:
    epoch: ScopeEpoch
    settings: TriggerSettings
    detection_sample: int
    left_value: PCMSample
    right_value: PCMSample
    fraction: Fraction
    disposition: Literal[
        "unarmed", "single_disarmed", "holdoff", "busy",
        "missing_prehistory", "span_out_of_range", "accepted",
    ]
    requested_start_sample: int
    requested_end_sample_exclusive: int
    holdoff_release_sample: int | None

    @property
    def left_sample(self) -> int:
        return self.detection_sample - 1


@dataclass(frozen=True)
class CaptureComplete:
    trigger: CrossingDecision
    window: CaptureWindow


@dataclass(frozen=True)
class CaptureAborted:
    trigger: CrossingDecision
    replacement_epoch_id: str


class ScopeTrigger:
    """One sequential trigger and one pending capture slot."""

    def __init__(self, epoch: ScopeEpoch, settings: TriggerSettings) -> None:
        if type(settings) is not TriggerSettings:
            raise ValueError("trigger requires TriggerSettings")
        self._settings = settings
        # Reflect falling edges so both directions use the same inequalities.
        self._polarity = 1 if settings.direction == "rising" else -1
        self._level = self._polarity * Fraction(settings.level)
        self._hysteresis = Fraction(settings.hysteresis)
        self._arm_level = self._level - self._hysteresis
        self._capture_length = settings.pre_frames + settings.post_frames + 1
        self._used_epoch_ids: set[str] = set()
        self._pending: CrossingDecision | None = None
        self.reset_epoch(epoch)

    @property
    def epoch(self) -> ScopeEpoch:
        return self._epoch

    @property
    def next_sample(self) -> int:
        return self._next_sample

    @property
    def pending(self) -> CrossingDecision | None:
        return self._pending

    def reset_epoch(self, epoch: ScopeEpoch) -> CaptureAborted | None:
        """Start a new sample timeline and report any abandoned span."""
        if type(epoch) is not ScopeEpoch:
            raise ValueError("reset requires a ScopeEpoch")
        if epoch.epoch_id in self._used_epoch_ids:
            raise ValueError("epoch identifier has already been used")
        if self._settings.channel_id not in epoch.channel_ids:
            raise ValueError("trigger channel is absent from the epoch")
        channel = epoch.channel_ids.index(self._settings.channel_id)
        aborted = None
        if self._pending is not None:
            aborted = CaptureAborted(self._pending, epoch.epoch_id)

        self._history: deque[tuple[PCMSample, ...]] = deque(maxlen=self._capture_length)
        self._epoch = epoch
        self._channel = channel
        self._next_sample = epoch.origin_sample
        self._previous: tuple[PCMSample, Fraction] | None = None
        self._armed = False
        self._single_permitted = False
        self._holdoff_release: int | None = None
        self._pending = None
        self._used_epoch_ids.add(epoch.epoch_id)
        return aborted

    def arm_single(self) -> None:
        """Permit one acceptance and search for a fresh arming sample."""
        if self._settings.mode != "single":
            raise ValueError("arm_single requires single-shot mode")
        if self._pending is not None:
            raise ValueError("capture is pending")
        if not self._single_permitted:
            self._armed = False
            self._single_permitted = True

    def _decide(
        self, index: int, left: PCMSample, right: PCMSample, fraction: Fraction
    ) -> CrossingDecision:
        settings = self._settings
        start = index - settings.pre_frames
        end = index + settings.post_frames + 1
        if not self._armed:
            disposition = "unarmed"
        elif settings.mode == "single" and not self._single_permitted:
            disposition = "single_disarmed"
        elif self._holdoff_release is not None and index < self._holdoff_release:
            disposition = "holdoff"
        elif self._pending is not None:
            disposition = "busy"
        elif start < index + 1 - len(self._history):
            disposition = "missing_prehistory"
        elif end > MAX_SAMPLE_INDEX:
            disposition = "span_out_of_range"
        else:
            disposition = "accepted"
            self._holdoff_release = index + settings.holdoff_frames
            self._single_permitted = False

        decision = CrossingDecision(
            epoch=self._epoch,
            settings=settings,
            detection_sample=index,
            left_value=left,
            right_value=right,
            fraction=fraction,
            disposition=disposition,
            requested_start_sample=start,
            requested_end_sample_exclusive=end,
            holdoff_release_sample=self._holdoff_release,
        )
        self._armed = False
        if disposition == "accepted":
            self._pending = decision
        return decision

    def ingest(
        self, *, epoch: ScopeEpoch, start_sample: int, planes: Sequence[Sequence[PCMSample]]
    ) -> tuple[CrossingDecision | CaptureComplete, ...]:
        """Validate a whole input block and return its events in sample order."""
        if type(epoch) is not ScopeEpoch or epoch != self._epoch:
            raise ValueError("block metadata must match the active epoch")
        if type(start_sample) is not int or not 0 <= start_sample <= MAX_SAMPLE_INDEX:
            raise ValueError("block start must be an integer in the sample index range")
        if start_sample != self._next_sample:
            kind = "gap" if start_sample > self._next_sample else "overlap"
            raise ValueError(f"{kind}: expected start={self._next_sample}, observed={start_sample}")

        # Use the capture type to validate and freeze all channel planes before ingest.
        block = CaptureWindow(self._epoch, start_sample, planes)
        if block.frame_count > MAX_BLOCK_FRAMES:
            raise ValueError(f"input block must contain at most {MAX_BLOCK_FRAMES} frames")

        events: list[CrossingDecision | CaptureComplete] = []
        for index, row in enumerate(zip(*block.planes), start_sample):
            self._history.append(row)
            raw = row[self._channel]
            value = self._polarity * Fraction(raw)
            previous = self._previous
            if previous is not None and previous[1] < self._level <= value:
                left_raw, left = previous
                fraction = (self._level - left) / (value - left)
                events.append(self._decide(index, left_raw, raw, fraction))
            if self._hysteresis:
                self._armed = self._armed or value <= self._arm_level
            else:
                self._armed = self._armed or value < self._level
            self._previous = (raw, value)

            # An earlier capture is still busy during its last sample's decision.
            pending = self._pending
            if pending is not None and index + 1 == pending.requested_end_sample_exclusive:
                window = CaptureWindow(
                    pending.epoch, pending.requested_start_sample, tuple(zip(*self._history))
                )
                events.append(CaptureComplete(pending, window))
                self._pending = None

        self._next_sample = block.end_sample_exclusive
        return tuple(events)
