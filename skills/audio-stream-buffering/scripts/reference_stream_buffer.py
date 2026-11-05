"""Bounded frame-indexed audio FIFO oracle; intentionally NOT a real-time/SPSC queue.

One logical stream clock, explicitly acknowledged overflow/underflow policies,
no implicit sample-clock resets. Designed for engineering fixtures, not audio I/O.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math

MAX_CHANNELS = 8
MAX_CAPACITY = 256
MAX_CALLBACK = 256
MIN_RATE = 2000
MAX_RATE = 384000


def integer(value: int, name: str, minimum: int = 0, maximum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    if maximum is not None and value > maximum:
        raise ValueError(f"{name} must be <= {maximum}")
    return value


def sample_rate(value: Fraction) -> Fraction:
    if not isinstance(value, Fraction) or not MIN_RATE <= value <= MAX_RATE:
        raise ValueError("rate_hz must be Fraction within 2000..384000 Hz")
    return value


def identifier(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("epoch_id must be a nonempty string")
    return value


def _validate_block(planes, channels: int, capacity: int) -> tuple[list[list[float]], int]:
    if not isinstance(planes, (tuple, list)) or len(planes) != channels:
        raise ValueError("expected one planar buffer per channel")
    if any(not isinstance(row, (tuple, list)) for row in planes):
        raise ValueError("each channel must contain a list or tuple of samples")
    n = len(planes[0])
    if not 1 <= n <= min(MAX_CALLBACK, capacity):
        raise ValueError("input block size exceeds reference capacity or is empty")
    if any(len(row) != n for row in planes):
        raise ValueError("all channel planes must contain identical frame counts")
    result = []
    for row in planes:
        data = []
        for x in row:
            if isinstance(x, bool) or not isinstance(x, (int, float)):
                raise ValueError("samples must be finite real scalars, not bool/complex")
            try:
                value = float(x)
            except (ValueError, OverflowError) as exc:
                raise ValueError("sample cannot be represented as finite binary64") from exc
            if not math.isfinite(value):
                raise ValueError("input samples must be finite")
            data.append(value)
        result.append(data)
    return result, n


@dataclass(frozen=True)
class TraceSpan:
    """Half-open sample-coordinate span and its provenance."""
    kind: str  # input | overrun_gap | underrun_silence
    start_sample: int
    frames: int

    def __post_init__(self) -> None:
        if self.kind not in ("input", "overrun_gap", "underrun_silence"):
            raise ValueError("unknown span kind")
        integer(self.start_sample, "span start")
        integer(self.frames, "span count", 1)


class FrameRing:
    """Deterministic planar buffer model, single logical producer and consumer.

    Preallocated sample slots are pedagogical only. Calls allocate results and
    statistics; no thread safety or real-time callback guarantees are provided.
    """

    def __init__(
        self, *, capacity_frames: int, channels: int, rate_hz: Fraction,
        epoch_id: str, origin_sample: int = 0,
        overflow_policy: str = "reject", underflow_policy: str = "reject",
    ) -> None:
        integer(capacity_frames, "capacity_frames", 1, MAX_CAPACITY)
        integer(channels, "channels", 1, MAX_CHANNELS)
        sample_rate(rate_hz)
        identifier(epoch_id)
        integer(origin_sample, "origin_sample")
        if overflow_policy not in ("reject", "drop_oldest"):
            raise ValueError("overflow_policy must be reject or drop_oldest")
        if underflow_policy not in ("reject", "silence"):
            raise ValueError("underflow_policy must be reject or silence")
        self.capacity_frames = capacity_frames
        self.channels = channels
        self.rate_hz = rate_hz
        self.epoch_id = epoch_id
        self.origin_sample = origin_sample
        self.overflow_policy = overflow_policy
        self.underflow_policy = underflow_policy
        self._used_epochs = {epoch_id}
        self._slots = [[0.0] * capacity_frames for _ in range(channels)]
        self.read_cursor = origin_sample  # next output/presentation sample position
        self.stored_start = origin_sample  # oldest actually retained input
        self.write_cursor = origin_sample  # next expected producer sample index
        self.total_dropped = 0
        self.total_overrun_gap_silence = 0
        self.total_underrun_silence = 0
        self.accepted_pushes = 0
        self.accepted_pulls = 0

    @property
    def buffered_frames(self) -> int:
        return self.write_cursor - self.stored_start

    @property
    def free_frames(self) -> int:
        return self.capacity_frames - self.buffered_frames

    @property
    def pending_overrun_gap(self) -> int:
        return self.stored_start - self.read_cursor

    @property
    def playable_frames(self) -> int:
        if self.pending_overrun_gap:
            return 0
        return self.buffered_frames

    @property
    def storage_latency_seconds(self) -> Fraction:
        """Buffer occupancy / nominal Hz, NOT actual device/output latency."""
        return Fraction(self.buffered_frames, 1) / self.rate_hz

    def snapshot(self) -> dict:
        return {
            "epoch_id": self.epoch_id,
            "read_cursor": self.read_cursor,
            "stored_start": self.stored_start,
            "write_cursor": self.write_cursor,
            "buffered_frames": self.buffered_frames,
            "free_frames": self.free_frames,
            "pending_overrun_gap": self.pending_overrun_gap,
            "playable_frames": self.playable_frames,
            "storage_latency_seconds": self.storage_latency_seconds,
            "total_dropped": self.total_dropped,
            "total_overrun_gap_silence": self.total_overrun_gap_silence,
            "total_underrun_silence": self.total_underrun_silence,
            "accepted_pushes": self.accepted_pushes,
            "accepted_pulls": self.accepted_pulls,
        }

    def push(self, start_sample: int, planar_samples) -> dict:
        """All-or-nothing producer block. Only explicit drop_oldest may discard."""
        integer(start_sample, "start_sample")
        if start_sample != self.write_cursor:
            raise ValueError(f"noncontiguous producer epoch: expected {self.write_cursor}, got {start_sample}")
        samples, count = _validate_block(planar_samples, self.channels, self.capacity_frames)
        overflow = max(0, self.buffered_frames + count - self.capacity_frames)
        if overflow and self.overflow_policy == "reject":
            raise ValueError("ring capacity exceeded; producer block not accepted")
        # Commit only after all checks have succeeded.
        self.stored_start += overflow
        for c in range(self.channels):
            for i in range(count):
                self._slots[c][(self.write_cursor + i) % self.capacity_frames] = samples[c][i]
        self.write_cursor += count
        self.total_dropped += overflow
        self.accepted_pushes += 1
        return {
            "epoch_id": self.epoch_id,
            "input_start_sample": start_sample,
            "input_end_sample_exclusive": self.write_cursor,
            "accepted_frames": count,
            "dropped_oldest_frames": overflow,
            "dropped_span": (self.stored_start - overflow, self.stored_start) if overflow else None,
            "buffered_frames_after": self.buffered_frames,
            "pending_overrun_gap_after": self.pending_overrun_gap,
            "capacity_frames": self.capacity_frames,
        }

    def pull(self, start_sample: int, frames: int) -> dict:
        """Consume requested presentation coordinates with explicit provenance.

        Missing *past* frames are overflow gaps; missing *future* frames are
        underruns. Filling future silence advances producer expectancy so late
        packets cannot be mislabelled as if they arrived on time.
        """
        integer(start_sample, "start_sample")
        integer(frames, "frames", 1, MAX_CALLBACK)
        if start_sample != self.read_cursor:
            raise ValueError(f"noncontiguous consumer epoch: expected {self.read_cursor}, got {start_sample}")
        end = start_sample + frames
        missing_overrun = max(0, min(end, self.stored_start) - start_sample)
        available_start = max(start_sample, self.stored_start)
        available_end = min(end, self.write_cursor)
        received = max(0, available_end - available_start)
        missing_under = max(0, end - max(start_sample, self.write_cursor))
        if missing_overrun + received + missing_under != frames:
            raise AssertionError("internal span partition invariant failed")
        if (missing_overrun or missing_under) and self.underflow_policy == "reject":
            raise ValueError("input span unavailable: explicit recovery policy required")
        result = [[0.0] * frames for _ in range(self.channels)]
        for j in range(received):
            at = available_start + j
            k = at - start_sample
            for ch in range(self.channels):
                result[ch][k] = self._slots[ch][at % self.capacity_frames]
        spans = []
        if missing_overrun:
            spans.append(TraceSpan("overrun_gap", start_sample, missing_overrun))
        if received:
            spans.append(TraceSpan("input", available_start, received))
        if missing_under:
            spans.append(TraceSpan("underrun_silence", max(start_sample, self.write_cursor), missing_under))
        # Commit after validation/construction. A synthetic future segment moves
        # the required producer cursor forward, rejecting any stale arrivals.
        self.read_cursor = end
        self.write_cursor = max(self.write_cursor, end)
        self.stored_start = max(self.stored_start, end)
        self.total_overrun_gap_silence += missing_overrun
        self.total_underrun_silence += missing_under
        self.accepted_pulls += 1
        return {
            "epoch_id": self.epoch_id,
            "start_sample": start_sample,
            "end_sample_exclusive": end,
            "start_seconds_from_epoch": Fraction(start_sample - self.origin_sample, 1) / self.rate_hz,
            "frames": frames,
            "planar_samples": result,
            "spans": tuple(spans),
            "source_frames": received,
            "overrun_gap_frames": missing_overrun,
            "underrun_silence_frames": missing_under,
            "synthetic_frames": missing_overrun + missing_under,
            "synthetic_audio": bool(missing_overrun + missing_under),
            "buffered_frames_after": self.buffered_frames,
            "next_required_input_sample": self.write_cursor,
        }

    def reset_epoch(
        self, new_epoch_id: str, origin_sample: int, *,
        capacity_frames: int | None = None, channels: int | None = None,
        rate_hz: Fraction | None = None,
        overflow_policy: str | None = None,
        underflow_policy: str | None = None,
    ) -> None:
        identifier(new_epoch_id)
        if new_epoch_id in self._used_epochs:
            raise ValueError("epoch IDs must be never-reused")
        integer(origin_sample, "origin_sample")
        cap = self.capacity_frames if capacity_frames is None else capacity_frames
        ch = self.channels if channels is None else channels
        rate = self.rate_hz if rate_hz is None else rate_hz
        overflow = self.overflow_policy if overflow_policy is None else overflow_policy
        underflow = self.underflow_policy if underflow_policy is None else underflow_policy
        # Construct a fully validated candidate, then atomically swap fields.
        next_epoch = FrameRing(capacity_frames=cap, channels=ch, rate_hz=rate,
                               epoch_id=new_epoch_id, origin_sample=origin_sample,
                               overflow_policy=overflow, underflow_policy=underflow)
        historical_ids = self._used_epochs | {new_epoch_id}
        self.__dict__.update(next_epoch.__dict__)
        self._used_epochs = historical_ids
