"""Offline Welch fractional-octave band power for normalized real PCM."""
from __future__ import annotations

from bisect import bisect_left, bisect_right
from collections import deque
import cmath
from dataclasses import dataclass
import math
from pathlib import Path
import sys
from typing import Literal, Sequence

_TIMEBASE_SCRIPTS = Path(__file__).resolve().parents[2] / "audio-timebase-sync/scripts"
if str(_TIMEBASE_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_TIMEBASE_SCRIPTS))

from reference_timebase import DiscontinuityError, SampleRate, SampleTimeline


FRACTIONS = (1, 3, 6, 12, 24)
MAX_SAMPLE_RATE_HZ = 384_000
MAX_NFFT = 262_144
MAX_WELCH_SEGMENTS = 64
MAX_PUSH_FRAMES = MAX_NFFT
MAX_SEGMENTS_PER_PUSH = 128
MIN_NONZERO_PCM = 2.0 ** -128
MAX_ABS_PCM = 2.0 ** 128

Window = Literal["rectangular", "hann_periodic"]
UnsupportedBand = Literal["truncated_nyquist", "unavailable", "unresolved_dc"]
BandStatus = Literal["ok", "zero_power", "truncated_nyquist", "unavailable", "unresolved_dc"]


def _integer(value: int, low: int, high: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in [{low}, {high}]")


def _fraction(value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value not in FRACTIONS:
        raise ValueError("fraction must be 1, 3, 6, 12 or 24")


@dataclass(frozen=True)
class RTAConfig:
    sample_rate_hz: int
    channel_labels: tuple[str, ...]
    source_tap: str
    fraction: int
    segment_samples: int
    hop_samples: int
    nfft: int
    welch_segments: int = 1
    window: Window = "hann_periodic"
    detrend_mean: bool = False
    min_center_hz: float = 20.0
    max_center_hz: float = 20_000.0

    def __post_init__(self) -> None:
        _integer(self.sample_rate_hz, 2, MAX_SAMPLE_RATE_HZ, "sample_rate_hz")
        _integer(self.nfft, 4, MAX_NFFT, "nfft")
        if self.nfft & (self.nfft - 1):
            raise ValueError("nfft must be a power of two")
        _integer(self.segment_samples, 4, self.nfft, "segment_samples")
        _integer(self.hop_samples, 1, self.segment_samples, "hop_samples")
        _integer(self.welch_segments, 1, MAX_WELCH_SEGMENTS, "welch_segments")
        _fraction(self.fraction)
        labels = self.channel_labels
        if (not isinstance(labels, tuple) or not 1 <= len(labels) <= 8
                or any(not isinstance(label, str) or not label.strip() for label in labels)
                or len(set(labels)) != len(labels)):
            raise ValueError("channel_labels must contain 1..8 distinct nonblank names")
        if not isinstance(self.source_tap, str) or not self.source_tap.strip():
            raise ValueError("source_tap must name the measured input")
        if self.window not in ("rectangular", "hann_periodic"):
            raise ValueError("unknown analysis window")
        if not isinstance(self.detrend_mean, bool):
            raise ValueError("detrend_mean must be Boolean")
        for value in (self.min_center_hz, self.max_center_hz):
            if (isinstance(value, bool) or not isinstance(value, (int, float))
                    or not 1 <= value <= MAX_SAMPLE_RATE_HZ):
                raise ValueError("center limits must be finite numbers in [1, 384000] Hz")
        if self.min_center_hz > self.max_center_hz:
            raise ValueError("center limits must be ordered")

    @property
    def bin_spacing_hz(self) -> float:
        return self.sample_rate_hz / self.nfft

    @property
    def segment_spacing_hz(self) -> float:
        """Native frequency spacing before any zero padding."""
        return self.sample_rate_hz / self.segment_samples


@dataclass(frozen=True)
class FractionalOctaveBand:
    index: int
    center_hz: float
    lower_hz: float
    upper_hz: float


def _frequency(fraction: int, twice_index: int) -> float:
    # Compute the same exponent for both sides of each shared edge.
    return 10.0 ** ((60 * fraction + 3 * twice_index) / (20 * fraction))


def fractional_octave_band(fraction: int, index: int) -> FractionalOctaveBand:
    """Return IEC base-10 frequencies rounded to binary64 for one band."""
    _fraction(fraction)
    _integer(index, -256, 256, "band index")
    twice_center = 2 * index + (1 if fraction % 2 == 0 else 0)
    return FractionalOctaveBand(
        index,
        _frequency(fraction, twice_center),
        _frequency(fraction, twice_center - 1),
        _frequency(fraction, twice_center + 1),
    )


@dataclass(frozen=True)
class RTABandReading:
    band: FractionalOctaveBand
    status: BandStatus
    power: float | None = None

    @property
    def rms(self) -> float | None:
        return None if self.power is None else math.sqrt(self.power)

    @property
    def level_dbfs(self) -> float | None:
        if self.power is None:
            return None
        return 10.0 * math.log10(self.power) if self.power else -math.inf


@dataclass(frozen=True)
class RTAChannelReading:
    channel_label: str
    total_power: float
    bands: tuple[RTABandReading, ...]


@dataclass(frozen=True)
class RTAFrame:
    epoch_id: str
    start_sample: int
    end_sample_exclusive: int
    config: RTAConfig
    channels: tuple[RTAChannelReading, ...]


def _bin_overlaps(
    lower_hz: float, upper_hz: float, edges: tuple[float, ...],
) -> tuple[int, tuple[float, ...]]:
    """Project [lower, upper] within the positive-bin cells (DC excluded)."""
    first = bisect_right(edges, lower_hz)
    last = bisect_left(edges, upper_hz)
    weights = []
    for k in range(first, last + 1):
        left, right = edges[k - 1], edges[k]
        covered = min(upper_hz, right) - max(lower_hz, left)
        weights.append(covered / (right - left))
    return first, tuple(weights)


@dataclass(frozen=True)
class _BandProjection:
    band: FractionalOctaveBand
    unsupported: UnsupportedBand | None = None
    first_bin: int = 0
    weights: tuple[float, ...] = ()

    def power(self, bin_powers: tuple[float, ...]) -> float:
        values = bin_powers[self.first_bin:self.first_bin + len(self.weights)]
        total = math.fsum(value * weight for value, weight in zip(values, self.weights))
        if total == 0.0 and any(values):
            raise ArithmeticError("positive band power rounded to zero")
        return total


def _make_projections(config: RTAConfig) -> tuple[_BandProjection, ...]:
    step = config.bin_spacing_hz
    nyquist = config.sample_rate_hz / 2
    edges = tuple((k + 0.5) * step for k in range(config.nfft // 2)) + (nyquist,)
    # Both configured center limits are inside this fixed index range for every fraction.
    projections = []
    for index in range(-256, 257):
        band = fractional_octave_band(config.fraction, index)
        if not config.min_center_hz <= band.center_hz <= config.max_center_hz:
            continue
        if band.lower_hz >= nyquist:
            projections.append(_BandProjection(band, "unavailable"))
        elif band.upper_hz > nyquist:
            projections.append(_BandProjection(band, "truncated_nyquist"))
        elif band.lower_hz < edges[0]:
            projections.append(_BandProjection(band, "unresolved_dc"))
        else:
            first, weights = _bin_overlaps(band.lower_hz, band.upper_hz, edges)
            projections.append(_BandProjection(band, first_bin=first, weights=weights))
    if not projections:
        raise ValueError("center limits do not select a band")
    return tuple(projections)


@dataclass(frozen=True)
class _SegmentPower:
    total: float
    bands: tuple[float, ...]


def _mean_power(values: Sequence[float]) -> float:
    mean = math.fsum(values) / len(values)
    if mean == 0.0 and any(values):
        raise ArithmeticError("positive Welch power rounded to zero")
    return mean


class _AnalysisPlan:
    def __init__(self, config: RTAConfig):
        self.config = config
        self.projections = _make_projections(config)
        m, nfft = config.segment_samples, config.nfft
        self.window = ((1.0,) * m if config.window == "rectangular"
                       else tuple(math.sin(math.pi * n / m) ** 2 for n in range(m)))
        # Density times df cancels fs. This is bin power under the PSD skill's
        # normalization, using an unnormalized DFT and one-sided power factors.
        self.bin_scale = 1.0 / (nfft * math.fsum(w * w for w in self.window))
        roots = [cmath.exp(-1j * math.tau * k / nfft) for k in range(nfft // 2)]
        roots[nfft // 4] = -1j
        self.roots = tuple(roots)
        indices = [0]
        for bit in reversed(range(nfft.bit_length() - 1)):
            indices.extend([index + (1 << bit) for index in indices])
        self.bit_reversed = tuple(indices)

    def _bin_powers(self, samples: tuple[float, ...]) -> tuple[float, ...]:
        mean = 0.0
        if self.config.detrend_mean:
            # An exact constant must disappear even if M times that value rounds.
            mean = (samples[0] if all(x == samples[0] for x in samples)
                    else math.fsum(samples) / len(samples))
        data = [(x - mean) * w for x, w in zip(samples, self.window)]
        m, nfft = len(data), self.config.nfft
        values = [complex(data[i]) if i < m else 0j for i in self.bit_reversed]
        # Radix-2 decimation in time. The existing direct DFT is a small-vector oracle.
        for stage in range(1, nfft.bit_length()):
            width = 1 << stage
            half = width // 2
            stride = nfft // width
            for start in range(0, nfft, width):
                for k in range(half):
                    left, right = start + k, start + k + half
                    even = values[left]
                    odd = values[right] * self.roots[k * stride]
                    values[left], values[right] = even + odd, even - odd

        powers = []
        for k, value in enumerate(values[:nfft // 2 + 1]):
            scale = self.bin_scale if k in (0, nfft // 2) else 2.0 * self.bin_scale
            power = abs(value) ** 2 * scale
            if power == 0.0 and value:
                raise ArithmeticError("positive spectral bin power rounded to zero")
            powers.append(power)
        return tuple(powers)

    def segment(self, samples: tuple[float, ...]) -> _SegmentPower:
        bin_powers = self._bin_powers(samples)
        return _SegmentPower(
            math.fsum(bin_powers),
            tuple(band.power(bin_powers) for band in self.projections),
        )

    def average(self, channel_label: str, history: Sequence[_SegmentPower]) -> RTAChannelReading:
        bands = []
        for i, projection in enumerate(self.projections):
            if projection.unsupported is not None:
                bands.append(RTABandReading(projection.band, projection.unsupported))
            else:
                power = _mean_power([segment.bands[i] for segment in history])
                status = "ok" if power else "zero_power"
                bands.append(RTABandReading(projection.band, status, power))
        total = _mean_power([segment.total for segment in history])
        return RTAChannelReading(channel_label, total, tuple(bands))


def _pcm_sample(value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("PCM samples must be real numbers")
    magnitude = abs(value)
    if magnitude != 0 and not MIN_NONZERO_PCM <= magnitude <= MAX_ABS_PCM:
        raise ValueError("nonzero PCM magnitude must be finite and in [2**-128, 2**128]")
    return float(value)


class FractionalOctaveRTA:
    """Per-channel Welch band readings on an exact, caller-supplied sample clock."""

    def __init__(self, config: RTAConfig, *, epoch_id: str, start_sample: int):
        if not isinstance(config, RTAConfig):
            raise ValueError("config must be an RTAConfig")
        self._timeline = SampleTimeline(
            epoch_id, start_sample, SampleRate(config.sample_rate_hz), len(config.channel_labels),
        )
        self._plan = _AnalysisPlan(config)
        self._pending: tuple[tuple[float, ...], ...] = ((),) * len(config.channel_labels)
        self._history: deque[tuple[_SegmentPower, ...]] = deque(maxlen=config.welch_segments)

    @property
    def config(self) -> RTAConfig:
        return self._plan.config

    @property
    def epoch_id(self) -> str:
        return self._timeline.epoch_id

    @property
    def next_sample(self) -> int:
        return self._timeline.next_sample

    def reset_epoch(
        self, epoch_id: str, start_sample: int, config: RTAConfig | None = None,
    ) -> None:
        """Clear pending samples and averaging history on a fresh epoch."""
        plan = self._plan
        if config is not None:
            if not isinstance(config, RTAConfig):
                raise ValueError("config must be an RTAConfig")
            plan = _AnalysisPlan(config)
        settings = plan.config
        pending = ((),) * len(settings.channel_labels)
        history = deque(maxlen=settings.welch_segments)
        self._timeline.reset_epoch(
            epoch_id, start_sample, SampleRate(settings.sample_rate_hz), len(settings.channel_labels),
        )
        self._plan, self._pending, self._history = plan, pending, history

    def push(
        self, start_sample: int, planes: Sequence[Sequence[float]], *, epoch_id: str,
    ) -> tuple[RTAFrame, ...]:
        """Consume one contiguous planar block, or leave the stream state intact."""
        if isinstance(start_sample, bool) or not isinstance(start_sample, int) or start_sample < 0:
            raise ValueError("start_sample must be a nonnegative integer")
        if epoch_id != self.epoch_id:
            raise ValueError("epoch mismatch")
        if start_sample != self.next_sample:
            kind = "gap" if start_sample > self.next_sample else "overlap"
            raise DiscontinuityError(kind, self.next_sample, start_sample)
        settings = self.config
        channel_count = len(settings.channel_labels)
        if (not isinstance(planes, (tuple, list)) or len(planes) != channel_count
                or any(not isinstance(plane, (tuple, list)) for plane in planes)):
            raise ValueError("provide one planar tuple/list for every declared channel")
        frame_count = len(planes[0])
        _integer(frame_count, 0, MAX_PUSH_FRAMES, "block frame count")
        if any(len(plane) != frame_count for plane in planes):
            raise ValueError("all planes must contain the same sample count")
        if not frame_count:
            return ()

        pending_count = len(self._pending[0])
        m, hop = settings.segment_samples, settings.hop_samples
        offsets = range(0, pending_count + frame_count - m + 1, hop)
        if len(offsets) > MAX_SEGMENTS_PER_PUSH:
            raise ValueError("block completes more than 128 segments; use smaller blocks")
        samples = tuple(old + tuple(_pcm_sample(x) for x in plane)
                        for old, plane in zip(self._pending, planes))
        history = self._history.copy()
        origin = start_sample - pending_count
        span_back = (settings.welch_segments - 1) * hop
        frames = []
        next_offset = 0
        for offset in offsets:
            history.append(tuple(self._plan.segment(plane[offset:offset + m])
                                 for plane in samples))
            if len(history) == settings.welch_segments:
                channels = tuple(
                    self._plan.average(label, [segment[ch] for segment in history])
                    for ch, label in enumerate(settings.channel_labels)
                )
                frames.append(RTAFrame(
                    epoch_id, origin + offset - span_back, origin + offset + m, settings, channels,
                ))
            next_offset = offset + hop
        new_pending = tuple(plane[next_offset:] for plane in samples)
        result = tuple(frames)
        # Commit only after every new sample and measurement has succeeded.
        self._timeline.ingest(start_sample, frame_count, channel_count)
        self._pending, self._history = new_pending, history
        return result
