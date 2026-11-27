"""Bounded offline stimuli on a declared sample clock."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math
import sys
from typing import Callable, ClassVar, Optional, Union

from reference_oscilloscope import MAX_SAMPLE_INDEX, ScopeEpoch, _check_integer


MAX_SIGNAL_FRAMES = 65536
MAX_COMPONENTS = 16
_MAX_PEAK = Fraction(sys.float_info.max)
Exact = Union[int, Fraction]
Coefficient = Union[int, float]


def _rational(value: Exact, name: str) -> Fraction:
    if type(value) not in (int, Fraction):
        raise ValueError(f"{name} must be an integer or exact rational")
    return Fraction(value)


def _level(value: Coefficient, name: str) -> float:
    if type(value) not in (int, float):
        raise ValueError(f"{name} must use a finite binary64 value")
    try:
        number = float(value)
    except OverflowError as exc:
        raise ValueError(f"{name} exceeds the binary64 range") from exc
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


@dataclass(frozen=True)
class Tone:
    frequency_hz: Exact
    amplitude: Coefficient
    phase_turns: Exact = 0

    def __post_init__(self) -> None:
        frequency = _rational(self.frequency_hz, "tone frequency")
        if frequency < 0:
            raise ValueError("tone frequency cannot be negative")
        object.__setattr__(self, "frequency_hz", frequency)
        object.__setattr__(self, "amplitude", _level(self.amplitude, "tone amplitude"))
        object.__setattr__(self, "phase_turns", _rational(self.phase_turns, "tone phase"))


@dataclass(frozen=True)
class Impulse:
    sample_offset: int
    amplitude: Coefficient

    def __post_init__(self) -> None:
        _check_integer(self.sample_offset, "impulse offset", 0, MAX_SIGNAL_FRAMES - 1)
        object.__setattr__(self, "amplitude", _level(self.amplitude, "impulse amplitude"))


@dataclass(frozen=True)
class LogSweep:
    start_hz: Exact
    end_hz: Exact
    amplitude: Coefficient
    phase_turns: Exact = 0

    def __post_init__(self) -> None:
        start = _rational(self.start_hz, "sweep start frequency")
        end = _rational(self.end_hz, "sweep end frequency")
        if min(start, end) <= 0:
            raise ValueError("sweep endpoints must be positive")
        object.__setattr__(self, "start_hz", start)
        object.__setattr__(self, "end_hz", end)
        object.__setattr__(self, "amplitude", _level(self.amplitude, "sweep amplitude"))
        object.__setattr__(self, "phase_turns", _rational(self.phase_turns, "sweep phase"))


Component = Union[Tone, Impulse, LogSweep]


@dataclass(frozen=True)
class ChannelSignal:
    components: tuple[Component, ...] = ()
    dc: Coefficient = 0

    def __post_init__(self) -> None:
        if (type(self.components) is not tuple or len(self.components) > MAX_COMPONENTS
                or any(type(component) not in (Tone, Impulse, LogSweep)
                       for component in self.components)):
            raise ValueError("supply a bounded tuple of tones, impulses, and sweeps")
        object.__setattr__(self, "dc", _level(self.dc, "DC offset"))
        if self.peak_bound > _MAX_PEAK:
            raise ValueError("channel peak bound exceeds the binary64 range")

    @property
    def peak_bound(self) -> Fraction:
        """Conservative sum of absolute, represented coefficients."""
        return abs(Fraction(self.dc)) + sum(
            abs(Fraction(component.amplitude)) for component in self.components
        )


def _check_component(component: Component, rate: Fraction, frames: int) -> None:
    if type(component) is Tone:
        if 2 * component.frequency_hz > rate:
            raise ValueError("tone frequency exceeds Nyquist")
    elif type(component) is Impulse:
        if component.sample_offset >= frames:
            raise ValueError("impulse must lie inside the active span")
    else:
        if 2 * max(component.start_hz, component.end_hz) >= rate:
            raise ValueError("sweep endpoints must be below Nyquist")
        if float(min(component.start_hz, component.end_hz) / rate) == 0:
            raise ValueError("normalized sweep endpoints must remain positive in binary64")


@dataclass(frozen=True)
class SignalPlan:
    epoch: ScopeEpoch
    active_start_sample: int
    active_frame_count: int
    channels: tuple[ChannelSignal, ...]
    leading_guard_frames: int = 0
    tail_guard_frames: int = 0
    peak_limit: Optional[Coefficient] = None

    def __post_init__(self) -> None:
        if type(self.epoch) is not ScopeEpoch:
            raise ValueError("supply a sample epoch with units and channel order")
        _check_integer(self.active_frame_count, "active frame count", 1, MAX_SIGNAL_FRAMES)
        _check_integer(self.leading_guard_frames, "leading guard", 0, MAX_SIGNAL_FRAMES)
        _check_integer(self.tail_guard_frames, "tail guard", 0, MAX_SIGNAL_FRAMES)
        if self.active_frame_count + self.leading_guard_frames + self.tail_guard_frames > MAX_SIGNAL_FRAMES:
            raise ValueError("total record including guards exceeds the frame bound")
        _check_integer(self.active_start_sample, "active start",
                       self.epoch.origin_sample + self.leading_guard_frames,
                       MAX_SAMPLE_INDEX - self.active_frame_count - self.tail_guard_frames)
        if (type(self.channels) is not tuple or len(self.channels) != len(self.epoch.channel_ids)
                or any(type(channel) is not ChannelSignal for channel in self.channels)):
            raise ValueError("supply one channel recipe per declared channel")
        if self.peak_limit is not None:
            limit = _level(self.peak_limit, "peak limit")
            if limit < 0 or any(channel.peak_bound > Fraction(limit) for channel in self.channels):
                raise ValueError("channel peak bound exceeds the requested peak limit")
            object.__setattr__(self, "peak_limit", limit)
        for channel in self.channels:
            for component in channel.components:
                _check_component(component, self.epoch.rate_hz, self.active_frame_count)

    @property
    def active_end_sample_exclusive(self) -> int:
        return self.active_start_sample + self.active_frame_count

    @property
    def record_start_sample(self) -> int:
        return self.active_start_sample - self.leading_guard_frames

    @property
    def record_end_sample_exclusive(self) -> int:
        return self.active_end_sample_exclusive + self.tail_guard_frames


@dataclass(frozen=True)
class SignalBlock:
    plan: SignalPlan
    start_sample: int
    planes: tuple[tuple[float, ...], ...]
    generator_id: ClassVar[str] = "audio-test-signals-v1"

    @property
    def end_sample_exclusive(self) -> int:
        return self.start_sample + len(self.planes[0])

    @property
    def sample_peaks(self) -> tuple[float, ...]:
        return tuple(max(map(abs, plane)) for plane in self.planes)


def _sine(numerator: int, denominator: int) -> float:
    # Fold exact turns to the first quadrant before converting to radians.
    half_turns, phase = divmod(2 * numerator, denominator)
    folded = min(phase, denominator - phase)
    magnitude = math.sin(math.tau * (folded / (2 * denominator)))
    return -magnitude if half_turns % 2 else magnitude


def _tone_at(tone: Tone, rate: Fraction) -> Callable[[int], float]:
    step = tone.frequency_hz / rate
    phase = tone.phase_turns
    ticks = math.lcm(step.denominator, phase.denominator)
    start = phase.numerator * (ticks // phase.denominator)
    stride = step.numerator * (ticks // step.denominator)
    return lambda offset: tone.amplitude * _sine(start + stride * offset, ticks)


def _log_ratio(ratio: Fraction) -> float:
    relative_change = ratio - 1
    if abs(relative_change) <= Fraction(1, 2):
        return math.log1p(float(relative_change))
    # Keep the mantissa in [1/2, 2) before converting it to binary64.
    exponent = ratio.numerator.bit_length() - ratio.denominator.bit_length()
    mantissa = ratio / Fraction(2) ** exponent
    return math.log(float(mantissa)) + exponent * math.log(2)


def _sweep_at(sweep: LogSweep, rate: Fraction, frame_count: int) -> Callable[[int], float]:
    if sweep.start_hz == sweep.end_hz:
        return _tone_at(Tone(sweep.start_hz, sweep.amplitude, sweep.phase_turns), rate)
    growth = _log_ratio(sweep.end_hz / sweep.start_hz)
    anchor = float(max(sweep.start_hz, sweep.end_hz) / rate)

    def sample(offset: int) -> float:
        z = growth * (offset / frame_count)
        if z > 0:
            # Factor out exp(z) and use the end frequency to keep the exponential bounded.
            cycles = anchor * offset * math.exp(growth * ((offset - frame_count) / frame_count))
            cycles *= -math.expm1(-z) / z
        elif z < 0:
            cycles = anchor * offset * (math.expm1(z) / z)
        else:
            cycles = anchor * offset
        phase = sweep.phase_turns + Fraction(cycles)
        return sweep.amplitude * _sine(phase.numerator, phase.denominator)

    return sample


def _component_at(component: Component, rate: Fraction, frame_count: int) -> Callable[[int], float]:
    if type(component) is Tone:
        return _tone_at(component, rate)
    if type(component) is Impulse:
        return lambda offset: component.amplitude if offset == component.sample_offset else 0.0
    return _sweep_at(component, rate, frame_count)


def render_signal(
    plan: SignalPlan, *, start_sample: Optional[int] = None, frame_count: Optional[int] = None,
) -> SignalBlock:
    """Render a nonempty subspan of the declared record in planar channel order."""
    if type(plan) is not SignalPlan:
        raise ValueError("supply a validated signal plan")
    start = plan.record_start_sample if start_sample is None else start_sample
    _check_integer(start, "render start", plan.record_start_sample, plan.record_end_sample_exclusive - 1)
    count = plan.record_end_sample_exclusive - start if frame_count is None else frame_count
    _check_integer(count, "render count", 1, plan.record_end_sample_exclusive - start)

    offset = start - plan.active_start_sample
    stop = offset + count
    first_active = max(offset, 0)
    end_active = min(stop, plan.active_frame_count)
    leading = (0.0,) * min(count, max(0, -offset))
    tail = (0.0,) * min(count, max(0, stop - plan.active_frame_count))
    planes = []
    for channel in plan.channels:
        evaluate = tuple(
            _component_at(component, plan.epoch.rate_hz, plan.active_frame_count)
            for component in channel.components
        )
        active = tuple(math.fsum((channel.dc, *(component(i) for component in evaluate)))
                       for i in range(first_active, end_active))
        planes.append(leading + active + tail)
    return SignalBlock(plan, start, tuple(planes))
