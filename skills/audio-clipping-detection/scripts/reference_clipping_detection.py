"""Bounded streaming evidence at integer rails and floating-point references."""

from __future__ import annotations

from dataclasses import dataclass, replace
from math import isfinite
from typing import Literal, Sequence

from reference_oscilloscope import (
    MAX_BLOCK_FRAMES, MAX_SAMPLE_INDEX, PCMSample, ScopeEpoch, _check_integer, _freeze_planes,
)
from reference_pcm import PCMFormat, decode_pcm
from reference_timebase import SampleRate, SampleTimeline


Polarity = Literal["negative", "positive"]
RunKind = Literal["rail_contact", "reference_exceedance"]
CloseReason = Literal["observed_break", "gap", "epoch_change", "end_of_input"]


@dataclass(frozen=True)
class SignedPcmProfile:
    valid_bits: int
    minimum_plateau_samples: int = 2

    def __post_init__(self) -> None:
        _check_integer(self.valid_bits, "valid bits", 2, 32)
        _check_integer(self.minimum_plateau_samples, "minimum plateau samples", 2, MAX_SAMPLE_INDEX)

    @property
    def lower(self) -> int:
        return -(1 << (self.valid_bits - 1))

    @property
    def upper(self) -> int:
        return (1 << (self.valid_bits - 1)) - 1


@dataclass(frozen=True)
class FloatReferenceProfile:
    lower: float = -1.0
    upper: float = 1.0

    def __post_init__(self) -> None:
        for value in (self.lower, self.upper):
            if type(value) not in (int, float):
                raise ValueError("reference endpoints must be finite real values")
            try:
                finite = isfinite(value)
            except OverflowError:
                finite = False
            if not finite:
                raise ValueError("reference endpoints must be finite real values")
        if not self.lower < 0 < self.upper:
            raise ValueError("reference endpoints must have opposite signs around zero")


Profile = SignedPcmProfile | FloatReferenceProfile


@dataclass(frozen=True)
class ChannelCounts:
    channel_id: str
    negative_contacts: int
    positive_contacts: int
    negative_exceedances: int
    positive_exceedances: int


@dataclass(frozen=True)
class BoundaryRun:
    epoch_id: str
    channel_id: str
    kind: RunKind
    polarity: Polarity
    boundary: PCMSample
    start_sample: int
    end_sample_exclusive: int
    extreme: PCMSample
    starts_at_epoch_origin: bool
    plateau_ready_sample_exclusive: int | None
    close_reason: CloseReason | None
    end_confirmed_sample_exclusive: int | None

    @property
    def length(self) -> int:
        return self.end_sample_exclusive - self.start_sample


@dataclass(frozen=True)
class ClippingUpdate:
    epoch: ScopeEpoch
    profile: Profile
    observed_end_sample_exclusive: int
    counts: tuple[ChannelCounts, ...]
    open_runs: tuple[BoundaryRun, ...]
    completed_runs: tuple[BoundaryRun, ...]
    finalized: bool
    pcm_format: PCMFormat | None = None


@dataclass
class _OpenRun:
    polarity: Polarity
    start_sample: int
    end_sample_exclusive: int
    extreme: PCMSample


@dataclass
class _ChannelState:
    channel_id: str
    negative_contacts: int = 0
    positive_contacts: int = 0
    negative_exceedances: int = 0
    positive_exceedances: int = 0
    run: _OpenRun | None = None

    def counts(self) -> ChannelCounts:
        return ChannelCounts(
            self.channel_id, self.negative_contacts, self.positive_contacts,
            self.negative_exceedances, self.positive_exceedances,
        )


def _setup(epoch: ScopeEpoch, profile: Profile) -> SampleRate:
    if type(epoch) is not ScopeEpoch or type(profile) not in (SignedPcmProfile, FloatReferenceProfile):
        raise ValueError("provide a ScopeEpoch and a signed code or float reference profile")
    return SampleRate(epoch.rate_hz.numerator, epoch.rate_hz.denominator)


class ClippingDetector:
    """Track one tap and one open run per channel over validated sample spans."""

    def __init__(self, epoch: ScopeEpoch, profile: Profile) -> None:
        rate = _setup(epoch, profile)
        self._timeline = SampleTimeline(epoch.epoch_id, epoch.origin_sample, rate, len(epoch.channel_ids))
        self._start_epoch(epoch, profile)

    @property
    def next_sample(self) -> int:
        return self._timeline.next_sample

    def _start_epoch(self, epoch: ScopeEpoch, profile: Profile) -> None:
        self._epoch = epoch
        self._profile = profile
        self._integer = type(profile) is SignedPcmProfile
        self._states = [_ChannelState(channel) for channel in epoch.channel_ids]
        self._finalized = False

    def _sample_polarity(self, state: _ChannelState, value: PCMSample) -> Polarity | None:
        if value == self._profile.lower:
            state.negative_contacts += 1
            return "negative" if self._integer else None
        if value == self._profile.upper:
            state.positive_contacts += 1
            return "positive" if self._integer else None
        if value < self._profile.lower:
            state.negative_exceedances += 1
            return "negative"
        if value > self._profile.upper:
            state.positive_exceedances += 1
            return "positive"
        return None

    def _run_snapshot(
        self, channel: str, run: _OpenRun, reason: CloseReason | None = None,
    ) -> BoundaryRun:
        plateau = None
        if type(self._profile) is SignedPcmProfile:
            threshold = run.start_sample + self._profile.minimum_plateau_samples
            if run.end_sample_exclusive >= threshold:
                plateau = threshold
        boundary = self._profile.lower if run.polarity == "negative" else self._profile.upper
        return BoundaryRun(
            epoch_id=self._epoch.epoch_id, channel_id=channel,
            kind="rail_contact" if self._integer else "reference_exceedance",
            polarity=run.polarity, boundary=boundary, start_sample=run.start_sample,
            end_sample_exclusive=run.end_sample_exclusive, extreme=run.extreme,
            starts_at_epoch_origin=run.start_sample == self._epoch.origin_sample,
            plateau_ready_sample_exclusive=plateau, close_reason=reason,
            end_confirmed_sample_exclusive=run.end_sample_exclusive + 1 if reason == "observed_break" else None,
        )

    def _update(self, end: int, completed: list[BoundaryRun]) -> ClippingUpdate:
        # Stable ordering preserves channel order for simultaneous ends.
        completed.sort(key=lambda run: run.end_sample_exclusive)
        return ClippingUpdate(
            epoch=self._epoch, profile=self._profile, observed_end_sample_exclusive=end,
            counts=tuple(state.counts() for state in self._states),
            open_runs=tuple(self._run_snapshot(state.channel_id, state.run)
                            for state in self._states if state.run is not None),
            completed_runs=tuple(completed), finalized=self._finalized,
        )

    def ingest(
        self, *, epoch: ScopeEpoch, start_sample: int, planes: Sequence[Sequence[PCMSample]],
    ) -> ClippingUpdate:
        """Validate the entire block and then scan it in the current epoch."""
        if type(epoch) is not ScopeEpoch or epoch != self._epoch:
            raise ValueError("block must use the detector's current epoch")
        if self._finalized:
            raise ValueError("start a new epoch after finalizing")
        frozen = _freeze_planes(planes, len(self._states), MAX_BLOCK_FRAMES)
        size = len(frozen[0])
        _check_integer(start_sample, "block start", 0, MAX_SAMPLE_INDEX - size)
        if self._integer and any(
            type(value) is not int or not self._profile.lower <= value <= self._profile.upper
            for plane in frozen for value in plane
        ):
            raise ValueError("provide unpacked signed codes within the declared valid bits")
        span = self._timeline.ingest(start_sample, size, len(self._states))

        completed = []
        for state, plane in zip(self._states, frozen):
            for index, value in enumerate(plane, span.start_sample):
                polarity = self._sample_polarity(state, value)
                run = state.run
                if run is not None and run.polarity != polarity:
                    completed.append(self._run_snapshot(state.channel_id, run, "observed_break"))
                    state.run = run = None
                if polarity is None:
                    continue
                if run is None:
                    state.run = _OpenRun(polarity, index, index + 1, value)
                else:
                    run.end_sample_exclusive = index + 1
                    run.extreme = min(run.extreme, value) if polarity == "negative" else max(run.extreme, value)
        return self._update(span.end_sample_exclusive, completed)

    def ingest_pcm(
        self, *, epoch: ScopeEpoch, start_sample: int, payload: bytes | list[bytes], fmt: PCMFormat,
    ) -> ClippingUpdate:
        """Decode integer PCM and recover its exact centered valid codes."""
        if type(fmt) is not PCMFormat or fmt.kind.startswith("f") or not self._integer:
            raise ValueError("integer PCM format and signed code profile required")
        if fmt.precision_bits != self._profile.valid_bits or fmt.channels != len(self._states):
            raise ValueError("PCM format must match the declared valid bits and channel count")
        if fmt.channel_labels is not None and fmt.channel_labels != self._epoch.channel_ids:
            raise ValueError("PCM labels must match the declared channel order")
        decoded = decode_pcm(payload, fmt)
        scale = 1 << (fmt.precision_bits - 1)
        codes = tuple(tuple(int(value * scale) for value in plane) for plane in decoded["planar_samples"])
        return replace(self.ingest(epoch=epoch, start_sample=start_sample, planes=codes), pcm_format=fmt)

    def _close_boundary(self, end: int, reason: CloseReason) -> ClippingUpdate:
        completed = []
        for state in self._states:
            if state.run is not None:
                completed.append(self._run_snapshot(state.channel_id, state.run, reason))
                state.run = None
        self._finalized = True
        return self._update(end, completed)

    def finish(self) -> ClippingUpdate:
        """Finalize the observed support and emit any remaining runs once."""
        return self._close_boundary(self.next_sample, "end_of_input")

    def reset_epoch(
        self, epoch: ScopeEpoch, *, profile: Profile | None = None,
        reason: Literal["gap", "epoch_change"] = "epoch_change",
    ) -> ClippingUpdate:
        """Close the prior observation and start a declared discontinuity."""
        if type(reason) is not str or reason not in ("gap", "epoch_change"):
            raise ValueError("declare a gap or epoch change")
        selected = self._profile if profile is None else profile
        rate = _setup(epoch, selected)
        old_end = self.next_sample
        self._timeline.reset_epoch(epoch.epoch_id, epoch.origin_sample, rate, len(epoch.channel_ids))
        previous = self._close_boundary(old_end, reason)
        self._start_epoch(epoch, selected)
        return previous
