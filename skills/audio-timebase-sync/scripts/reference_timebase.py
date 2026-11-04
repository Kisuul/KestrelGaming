"""Exact sample-clock and epoch reference; no real device or scheduling logic.

A clock correlation from one anchor is a nominal mapping, NOT evidence of
hardware clock accuracy, drift correction, or calibrated end-to-end latency.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction


def _integer(value: int, label: str, minimum: int = 0) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise ValueError(f"{label} must be an integer >= {minimum}")


def _epoch_id(value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("epoch_id must be a nonempty string")


@dataclass(frozen=True)
class SampleRate:
    numerator: int
    denominator: int = 1

    def __post_init__(self) -> None:
        _integer(self.numerator, "rate numerator", 1)
        _integer(self.denominator, "rate denominator", 1)

    @property
    def hz(self) -> Fraction:
        return Fraction(self.numerator, self.denominator)


def sample_count_to_seconds(count: int, rate: SampleRate) -> Fraction:
    _integer(count, "sample count")
    if not isinstance(rate, SampleRate):
        raise ValueError("rate must be a SampleRate")
    return Fraction(count, 1) / rate.hz


def convert_rate_offset(source_offset: int, source_rate: SampleRate,
                        destination_rate: SampleRate) -> Fraction:
    """A *position*, not integer output-sample count or a resampler algorithm."""
    _integer(source_offset, "source offset")
    if not isinstance(source_rate, SampleRate) or not isinstance(destination_rate, SampleRate):
        raise ValueError("source and destination rates must be SampleRate values")
    return Fraction(source_offset, 1) * destination_rate.hz / source_rate.hz


@dataclass(frozen=True)
class FrameSpan:
    epoch_id: str
    start_sample: int
    end_sample_exclusive: int
    center_sample_twice: int
    start_seconds: Fraction
    end_seconds_exclusive: Fraction
    center_seconds: Fraction
    duration_seconds: Fraction
    channel_count: int


class DiscontinuityError(ValueError):
    def __init__(self, kind: str, expected_start: int, observed_start: int):
        self.kind = kind
        self.expected_start = expected_start
        self.observed_start = observed_start
        self.delta_samples = observed_start - expected_start
        super().__init__(
            f"{kind}: expected start={expected_start}, observed={observed_start}; "
            f"delta={self.delta_samples} samples; explicit new epoch required"
        )


class SampleTimeline:
    """Atomic acceptance of contiguous PCM block metadata in one epoch."""

    def __init__(self, epoch_id: str, origin_sample: int,
                 sample_rate: SampleRate, channel_count: int):
        _epoch_id(epoch_id)
        _integer(origin_sample, "origin_sample")
        if not isinstance(sample_rate, SampleRate):
            raise ValueError("sample_rate must be a SampleRate")
        _integer(channel_count, "channel_count", 1)
        self.epoch_id = epoch_id
        self.origin_sample = origin_sample
        self.sample_rate = sample_rate
        self.channel_count = channel_count
        self.next_sample = origin_sample
        self.accepted_blocks = 0

    def ingest(self, start_sample: int, frame_count: int, channel_count: int) -> FrameSpan:
        """Reject invalid, gapped or overlapping blocks without mutating state."""
        _integer(start_sample, "start_sample")
        _integer(frame_count, "frame_count", 1)
        _integer(channel_count, "channel_count", 1)
        if channel_count != self.channel_count:
            raise ValueError("channel layout changed: start a new epoch")
        if start_sample != self.next_sample:
            kind = "gap" if start_sample > self.next_sample else "overlap"
            raise DiscontinuityError(kind, self.next_sample, start_sample)

        end = start_sample + frame_count
        center_twice = 2 * start_sample + frame_count - 1
        fs = self.sample_rate.hz
        span = FrameSpan(
            epoch_id=self.epoch_id,
            start_sample=start_sample,
            end_sample_exclusive=end,
            center_sample_twice=center_twice,
            start_seconds=Fraction(start_sample - self.origin_sample, 1) / fs,
            end_seconds_exclusive=Fraction(end - self.origin_sample, 1) / fs,
            center_seconds=Fraction(center_twice - 2 * self.origin_sample, 2) / fs,
            duration_seconds=Fraction(frame_count, 1) / fs,
            channel_count=channel_count,
        )
        self.next_sample = end
        self.accepted_blocks += 1
        return span

    def reset_epoch(self, new_epoch_id: str, origin_sample: int,
                    sample_rate: SampleRate | None = None,
                    channel_count: int | None = None) -> None:
        """Declare a discontinuity, seek, restart or reconfiguration explicitly."""
        _epoch_id(new_epoch_id)
        if new_epoch_id == self.epoch_id:
            raise ValueError("new epoch must have a distinct identifier")
        _integer(origin_sample, "origin_sample")
        rate = self.sample_rate if sample_rate is None else sample_rate
        channels = self.channel_count if channel_count is None else channel_count
        if not isinstance(rate, SampleRate):
            raise ValueError("sample_rate must be a SampleRate")
        _integer(channels, "channel_count", 1)
        self.epoch_id = new_epoch_id
        self.origin_sample = origin_sample
        self.sample_rate = rate
        self.channel_count = channels
        self.next_sample = origin_sample
        self.accepted_blocks = 0


@dataclass(frozen=True)
class ExternalClockAnchor:
    epoch_id: str
    sample_index: int
    clock_domain: str
    clock_kind: str
    time_seconds: Fraction

    def __post_init__(self) -> None:
        _epoch_id(self.epoch_id)
        _integer(self.sample_index, "anchor sample")
        if not isinstance(self.clock_domain, str) or not self.clock_domain.strip():
            raise ValueError("clock_domain must be named")
        if self.clock_kind not in ("capture", "playback", "callback"):
            raise ValueError("clock_kind must be capture, playback or callback")
        if not isinstance(self.time_seconds, Fraction):
            raise ValueError("anchor time must be an explicit Fraction in seconds")


def estimate_external_time(sample_index: int, epoch_id: str,
                           rate: SampleRate, anchor: ExternalClockAnchor,
                           expected_domain: str) -> Fraction:
    """Nominal mapping, not hardware synchronization or clock drift correction."""
    _integer(sample_index, "sample_index")
    _epoch_id(epoch_id)
    if not isinstance(rate, SampleRate):
        raise ValueError("rate must be a SampleRate")
    if not isinstance(anchor, ExternalClockAnchor):
        raise ValueError("anchor must be an ExternalClockAnchor")
    if epoch_id != anchor.epoch_id:
        raise ValueError("anchor belongs to another sample epoch")
    if not isinstance(expected_domain, str) or not expected_domain.strip():
        raise ValueError("expected_domain must be a nonempty string")
    if anchor.clock_domain != expected_domain:
        raise ValueError("external clock domain mismatch")
    return anchor.time_seconds + Fraction(sample_index - anchor.sample_index, 1) / rate.hz
