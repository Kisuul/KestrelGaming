"""Bounded educational rational-rate FIR resampling reference.

Centered, finite Kaiser-windowed sinc with explicit zero extension. No device,
clock recovery, drift handling, realtime guarantee, or file/codec parser.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
import math

MAX_INPUT_FRAMES = 256
MAX_OUTPUT_FRAMES = 4096
MAX_RATIO_FACTOR = 320
TAPS_PER_FACTOR_SIDE = 10
KAISER_BETA = 5.0


def _integer(value: int, label: str, minimum: int = 0) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise ValueError(f"{label} must be an integer >= {minimum}")


def _rate(value: Fraction, label: str) -> Fraction:
    if not isinstance(value, Fraction) or value <= 0:
        raise ValueError(f"{label} must be a positive exact Fraction in Hz")
    return value


def _i0(value: float) -> float:
    """Modified Bessel I0 via positive convergent series; bounded beta <= 5."""
    term = 1.0
    total = 1.0
    for k in range(1, 65):
        term *= (value / (2.0 * k)) ** 2
        total += term
        if term < total * 1e-17:
            return total
    raise ArithmeticError("I0 series failed to converge")


def _sinc(value: float) -> float:
    return 1.0 if value == 0.0 else math.sin(math.pi * value) / (math.pi * value)


@lru_cache(maxsize=32)
def _fir(up: int, down: int) -> tuple[float, ...]:
    """Unit DC, odd linear-phase lowpass at min(original,target) Nyquist.

    Taps are indexed on the *upsampled* time grid and multiplied by up,
    matching upsample-filter-decimate conventions.
    """
    if up == down == 1:
        return (1.0,)
    high_rate = max(up, down)
    half = TAPS_PER_FACTOR_SIDE * high_rate
    normalizer = _i0(KAISER_BETA)
    coefficients = []
    for offset in range(-half, half + 1):
        window = _i0(KAISER_BETA * math.sqrt(max(0.0, 1.0 - (offset / half) ** 2))) / normalizer
        coefficients.append(_sinc(offset / high_rate) / high_rate * window)
    total = math.fsum(coefficients)
    if not total > 0.0:
        raise ValueError("invalid lowpass coefficient normalization")
    return tuple((tap / total) * up for tap in coefficients)


@dataclass(frozen=True)
class RatePlan:
    source_hz: Fraction
    destination_hz: Fraction

    def __post_init__(self) -> None:
        _rate(self.source_hz, "source_hz")
        _rate(self.destination_hz, "destination_hz")
        ratio = self.destination_hz / self.source_hz
        if max(ratio.numerator, ratio.denominator) > MAX_RATIO_FACTOR:
            raise ValueError("reduced rate ratio exceeds bounded oracle limit")

    @property
    def up(self) -> int:
        return (self.destination_hz / self.source_hz).numerator

    @property
    def down(self) -> int:
        return (self.destination_hz / self.source_hz).denominator

    @property
    def intermediate_hz(self) -> Fraction:
        return self.source_hz * self.up

    @property
    def filter_half_length(self) -> int:
        return 0 if self.up == self.down == 1 else TAPS_PER_FACTOR_SIDE * max(self.up, self.down)

    @property
    def compensated_group_delay_source_samples(self) -> Fraction:
        return Fraction(self.filter_half_length, self.up)

    @property
    def nominal_delay_seconds(self) -> Fraction:
        return self.compensated_group_delay_source_samples / self.source_hz

    def output_frames(self, input_frames: int) -> int:
        _integer(input_frames, "input_frames")
        return (input_frames * self.up + self.down - 1) // self.down

    def input_offset_at_output(self, output_offset: int) -> Fraction:
        _integer(output_offset, "output_offset")
        return Fraction(output_offset * self.down, self.up)

    def output_time_from_origin(self, output_offset: int) -> Fraction:
        _integer(output_offset, "output_offset")
        return Fraction(output_offset, 1) / self.destination_hz


def _validate_planes(planes: list[list[float]], channels: int) -> tuple[list[list[float]], int]:
    if (not isinstance(planes, (list, tuple)) or len(planes) != channels
            or any(not isinstance(channel, (list, tuple)) for channel in planes)):
        raise ValueError("planar sample buffer must have the declared channel count")
    n = len(planes[0])
    if not n or any(len(p) != n for p in planes):
        raise ValueError("all channels must contain equal, nonempty sample counts")
    normalized = []
    for p in planes:
        channel = []
        for value in p:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError("audio samples must be finite real numbers")
            try:
                scalar = float(value)
            except (OverflowError, ValueError) as exc:
                raise ValueError("sample cannot be represented in float") from exc
            if not math.isfinite(scalar):
                raise ValueError("audio samples must be finite")
            channel.append(scalar)
        normalized.append(channel)
    return normalized, n


def _convolve_at(plane: list[float], output_offset: int, plan: RatePlan,
                 kernel: tuple[float, ...]) -> float:
    if plan.up == plan.down == 1:
        return plane[output_offset]
    up, down, half = plan.up, plan.down, plan.filter_half_length
    t = output_offset * down
    left = max(0, -((half - t) // up))  # ceil((t-half)/up)
    right = min(len(plane) - 1, (t + half) // up)
    try:
        value = math.fsum(plane[j] * kernel[half + t - j * up]
                          for j in range(left, right + 1))
    except OverflowError as exc:
        raise ValueError("resampled sum exceeds finite representation") from exc
    if not math.isfinite(value):
        raise ValueError("resampled value exceeds finite representation")
    return value


class StreamResampler:
    """Bounded offline-like stateful oracle, with delayed stable output only.

    This retains the *entire* bounded epoch for reproducibility. Do not use
    this model as an RT callback or unbounded capture processor.
    """
    def __init__(self, epoch_id: str, input_origin_sample: int,
                 source_hz: Fraction, destination_hz: Fraction,
                 channels: int, output_origin_sample: int = 0):
        if not isinstance(epoch_id, str) or not epoch_id.strip():
            raise ValueError("epoch_id must be a nonempty string")
        _integer(input_origin_sample, "input_origin_sample")
        _integer(output_origin_sample, "output_origin_sample")
        _integer(channels, "channels", 1)
        if channels > 8:
            raise ValueError("bounded oracle supports at most 8 channels")
        plan = RatePlan(source_hz, destination_hz)
        self._used_epoch_ids = {epoch_id}
        self._set_epoch(epoch_id, input_origin_sample, output_origin_sample, plan, channels)

    def _set_epoch(self, epoch_id: str, input_origin: int, output_origin: int,
                   plan: RatePlan, channels: int) -> None:
        self.epoch_id = epoch_id
        self.input_origin_sample = input_origin
        self.output_origin_sample = output_origin
        self.channels = channels
        self.plan = plan
        self._kernel = _fir(plan.up, plan.down)
        self._planes = [[] for _ in range(channels)]
        self.next_input_sample = input_origin
        self.next_output_offset = 0
        self.finalized = False

    def _render(self, planes: list[list[float]], limit: int,
                completed: bool) -> tuple[list[list[float]], list[bool], int]:
        up, down, half = self.plan.up, self.plan.down, self.plan.filter_half_length
        available = len(planes[0])
        generated = [[] for _ in range(self.channels)]
        flags = []
        m = self.next_output_offset
        while m < limit:
            # Noncausal centered kernel: do not publish output while an
            # actual sample inside future support could still change it.
            j_max = (m * down + half) // up
            if not completed and j_max >= available:
                break
            edge = (((m * down - half + up - 1) // up) < 0
                    or ((m * down + half) // up) >= available)
            values = [_convolve_at(plane, m, self.plan, self._kernel) for plane in planes]
            for c, x in enumerate(values):
                generated[c].append(x)
            flags.append(edge)
            m += 1
        return generated, flags, m

    def _output(self, data: list[list[float]], boundary: list[bool],
                start_offset: int, finalized_tail: bool) -> dict:
        return {
            "epoch_id": self.epoch_id,
            "output_start_sample": self.output_origin_sample + start_offset,
            "output_frames": len(boundary),
            "planar_samples": data,
            "boundary_affected": boundary,
            "first_source_offset": self.plan.input_offset_at_output(start_offset),
            "source_origin_sample": self.input_origin_sample,
            "source_hz": self.plan.source_hz,
            "destination_hz": self.plan.destination_hz,
            "up": self.plan.up,
            "down": self.plan.down,
            "filter_half_length_upsampled": self.plan.filter_half_length,
            "required_lookahead_source_samples": self.plan.compensated_group_delay_source_samples,
            "finalized_tail": finalized_tail,
        }

    def push(self, start_sample: int, planar_samples: list[list[float]]) -> dict:
        if self.finalized:
            raise ValueError("stream epoch finalized; reset to a new epoch")
        _integer(start_sample, "start_sample")
        if start_sample != self.next_input_sample:
            raise ValueError(
                f"noncontiguous source samples: expected {self.next_input_sample}, "
                f"observed {start_sample}; new epoch required"
            )
        added, frame_count = _validate_planes(planar_samples, self.channels)
        available = len(self._planes[0]) + frame_count
        if available > MAX_INPUT_FRAMES or self.plan.output_frames(available) > MAX_OUTPUT_FRAMES:
            raise ValueError("bounded reference input/output limit exceeded")
        proposed = [self._planes[i] + added[i] for i in range(self.channels)]
        output, boundary, next_offset = self._render(
            proposed, self.plan.output_frames(available), completed=False)
        # Publish state only after all validation and numerical work succeeds.
        old_offset = self.next_output_offset
        self._planes = proposed
        self.next_input_sample += frame_count
        self.next_output_offset = next_offset
        return self._output(output, boundary, old_offset, finalized_tail=False)

    def finalize(self) -> dict:
        if self.finalized:
            raise ValueError("stream epoch already finalized")
        if not self._planes[0]:
            raise ValueError("cannot finalize a stream without input")
        output, boundary, next_offset = self._render(
            self._planes, self.plan.output_frames(len(self._planes[0])), completed=True)
        old_offset = self.next_output_offset
        self.next_output_offset = next_offset
        self.finalized = True
        return self._output(output, boundary, old_offset, finalized_tail=True)

    def reset_epoch(self, new_epoch_id: str, input_origin_sample: int,
                    source_hz: Fraction | None = None,
                    destination_hz: Fraction | None = None,
                    channels: int | None = None,
                    output_origin_sample: int = 0) -> None:
        if not isinstance(new_epoch_id, str) or not new_epoch_id.strip():
            raise ValueError("new epoch ID must be a nonempty string")
        if new_epoch_id in self._used_epoch_ids:
            raise ValueError("epoch ID must never be reused")
        _integer(input_origin_sample, "input_origin_sample")
        _integer(output_origin_sample, "output_origin_sample")
        c = self.channels if channels is None else channels
        _integer(c, "channels", 1)
        if c > 8:
            raise ValueError("bounded oracle supports at most 8 channels")
        source = self.plan.source_hz if source_hz is None else source_hz
        dest = self.plan.destination_hz if destination_hz is None else destination_hz
        plan = RatePlan(source, dest)
        self._set_epoch(new_epoch_id, input_origin_sample, output_origin_sample, plan, c)
        self._used_epoch_ids.add(new_epoch_id)


def resample_offline(planar_samples: list[list[float]], source_hz: Fraction,
                     destination_hz: Fraction, input_origin_sample: int = 0,
                     epoch_id: str = "offline", output_origin_sample: int = 0) -> dict:
    """Complete finite record: concatenate buffered and zero-extended tail."""
    if not isinstance(planar_samples, (list, tuple)):
        raise ValueError("planar input must be a sequence")
    stream = StreamResampler(epoch_id, input_origin_sample, source_hz,
                             destination_hz, len(planar_samples), output_origin_sample)
    stable = stream.push(input_origin_sample, planar_samples)
    tail = stream.finalize()
    merged = [stable["planar_samples"][ch] + tail["planar_samples"][ch]
              for ch in range(stream.channels)]
    flags = stable["boundary_affected"] + tail["boundary_affected"]
    return {
        "epoch_id": epoch_id,
        "source_origin_sample": input_origin_sample,
        "output_origin_sample": output_origin_sample,
        "source_hz": source_hz,
        "destination_hz": destination_hz,
        "up": stream.plan.up,
        "down": stream.plan.down,
        "input_frames": len(planar_samples[0]),
        "output_frames": len(flags),
        "planar_samples": merged,
        "boundary_affected": flags,
        "filter_half_length_upsampled": stream.plan.filter_half_length,
        "compensated_group_delay_source_samples": stream.plan.compensated_group_delay_source_samples,
        "output_first_source_offset": Fraction(0),
        "output_last_source_offset": stream.plan.input_offset_at_output(len(flags) - 1),
        "extension": "zero_outside_finite_epoch",
        "quality": "educational_kaiser_beta5_10taps_per_factor_side",
    }
