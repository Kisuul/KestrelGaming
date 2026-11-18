"""Bounded offline parallel STFT/PSD reference; no realtime guarantees.

Only public timebase types are shared. The local radix-2 FFT is independently
checked with the pre-existing direct DFT in the repository tests.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import math
from pathlib import Path
import sys

_TIMEBASE = Path(__file__).resolve().parents[2] / "audio-timebase-sync/scripts"
if str(_TIMEBASE) not in sys.path:
    sys.path.insert(0, str(_TIMEBASE))
from reference_timebase import DiscontinuityError, SampleRate, SampleTimeline

MAX_NFFT = 32768
MAX_PUSH_SAMPLES = 65536
MAX_PROFILE_FRAMES = 256
MAX_WORK_UNITS = 2**24
MAX_OUTPUT_VALUES = 2**20
MAX_EPOCHS = 1024
MIN_NONZERO_PCM = 2.0**-128
MAX_ABS_PCM = 2.0**128


def _integer(value: int, lower: int, upper: int, name: str) -> None:
    if type(value) is not int or not lower <= value <= upper:
        raise ValueError(f"{name} must be an integer in [{lower}, {upper}]")


def _sample_index(value: int) -> None:
    _integer(value, 0, 2**256-1, "sample index")


def _name(value: str) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > 128:
        raise ValueError("names must contain 1..128 characters and be nonblank")


def _frequency(value: float) -> None:
    if (type(value) not in (int, float) or not 0 <= value <= 384000):
        raise ValueError("frequency must be finite in [0,384000] Hz")


@dataclass(frozen=True)
class ProfileConfig:
    name: str
    window_samples: int
    hop_samples: int
    nfft: int
    window: str = "hann_periodic"

    def __post_init__(self) -> None:
        _name(self.name)
        _integer(self.nfft, 4, MAX_NFFT, "nfft")
        if self.nfft & (self.nfft-1):
            raise ValueError("nfft must be a power of two")
        _integer(self.window_samples, 4, self.nfft, "window_samples")
        _integer(self.hop_samples, 1, self.window_samples, "hop_samples")
        if self.window not in ("rectangular", "hann_periodic"):
            raise ValueError("unsupported window")


@dataclass(frozen=True)
class SpectrumConfig:
    sample_rate_hz: int
    channel_labels: tuple[str, ...]
    source_tap: str
    profiles: tuple[ProfileConfig, ...]
    frequency_edges_hz: tuple[float, ...] = (20.0, 200.0, 2000.0, 20000.0)

    def __post_init__(self) -> None:
        _integer(self.sample_rate_hz, 2, 384000, "sample_rate_hz")
        _name(self.source_tap)
        labels = self.channel_labels
        if not isinstance(labels, tuple) or not 1 <= len(labels) <= 8:
            raise ValueError("provide 1..8 ordered channel labels")
        for label in labels:
            _name(label)
        if len(set(labels)) != len(labels):
            raise ValueError("channel labels must be unique")
        profiles = self.profiles
        if (not isinstance(profiles, tuple) or len(profiles) != 3
                or any(not isinstance(p, ProfileConfig) for p in profiles)):
            raise ValueError("provide exactly three ProfileConfig values")
        if len({p.name for p in profiles}) != 3:
            raise ValueError("profile names must be unique")
        sizes = tuple(p.window_samples for p in profiles)
        if sizes != tuple(sorted(sizes, reverse=True)):
            raise ValueError("window lengths must be ordered low >= mid >= high")
        if any((self.first_composite_samples-p.window_samples) % p.hop_samples
               for p in profiles):
            raise ValueError("profiles do not align at the first common endpoint")
        if self.composite_hop_samples > 65536:
            raise ValueError("common-end hop exceeds 65536 samples")
        edges = self.frequency_edges_hz
        if not isinstance(edges, tuple) or len(edges) != 4:
            raise ValueError("provide four frequency edges")
        for edge in edges:
            _frequency(edge)
        if edges[0] <= 0 or any(a >= b for a, b in zip(edges, edges[1:])):
            raise ValueError("frequency edges must be positive and strictly increasing")

    @property
    def first_composite_samples(self) -> int:
        return max(p.window_samples for p in self.profiles)

    @property
    def composite_hop_samples(self) -> int:
        # gcd formulation keeps the reference compatible with Python 3.9+.
        result = 1
        for p in self.profiles:
            result = result*p.hop_samples // math.gcd(result, p.hop_samples)
        return result


def reference_config(sample_rate_hz: int = 48000,
                     channel_labels: tuple[str, ...] = ("L",),
                     source_tap: str = "decoded PCM") -> SpectrumConfig:
    if type(sample_rate_hz) is not int or sample_rate_hz not in (48000, 96000):
        raise ValueError("tabulated defaults support only 48000 and 96000 Hz")
    factor = sample_rate_hz // 48000
    profiles = tuple(ProfileConfig(name, m*factor, h*factor, m*factor)
                     for name, m, h in (("low", 8192, 2048), ("mid", 2048, 512),
                                       ("high", 512, 128)))
    return SpectrumConfig(sample_rate_hz, channel_labels, source_tap, profiles)


def owner_index(config: SpectrumConfig, frequency_hz: float) -> int | None:
    """Frequency ownership only; this does not invent a supporting bin."""
    _frequency(frequency_hz)
    edges = config.frequency_edges_hz
    for i in range(3):
        if edges[i] <= frequency_hz < edges[i+1] or (
                i == 2 and frequency_hz == edges[3]):
            return i
    return None


@dataclass(frozen=True)
class WindowProperties:
    coefficients: tuple[float, ...]
    sum_w: float
    sum_w_squared: float
    coherent_gain: float
    mean_square_gain: float
    enbw_native_bins: float
    enbw_hz: float
    approximate_main_lobe_width_hz: float


@dataclass(frozen=True)
class ChannelPSD:
    channel_label: str
    psd: tuple[float, ...]


@dataclass(frozen=True)
class ProfileObservation:
    epoch_id: str
    start_sample: int
    end_sample_exclusive: int
    center_sample_twice: int
    config: SpectrumConfig
    profile: ProfileConfig
    window_properties: WindowProperties
    frequencies_hz: tuple[float, ...]
    channels: tuple[ChannelPSD, ...]

    @property
    def bin_spacing_hz(self) -> float:
        return self.config.sample_rate_hz / self.profile.nfft


@dataclass(frozen=True)
class FrequencySelection:
    profile_name: str
    status: str
    bin_indices: tuple[int, ...]


@dataclass(frozen=True)
class FrequencyReading:
    status: str
    profile_name: str | None = None
    bin_index: int | None = None
    density: float | None = None


@dataclass(frozen=True)
class CompositeObservation:
    epoch_id: str
    end_sample_exclusive: int
    contributors: tuple[ProfileObservation, ...]
    selections: tuple[FrequencySelection, ...]

    def at_frequency(self, frequency_hz: float, channel_label: str) -> FrequencyReading:
        config = self.contributors[0].config
        if channel_label not in config.channel_labels:
            raise ValueError("unknown channel label")
        i = owner_index(config, frequency_hz)
        if i is None:
            return FrequencyReading("unavailable")
        frame = self.contributors[i]
        for k in self.selections[i].bin_indices:
            if frame.frequencies_hz[k] == frequency_hz:
                channel = config.channel_labels.index(channel_label)
                return FrequencyReading("ok", frame.profile.name, k,
                                        frame.channels[channel].psd[k])
        return FrequencyReading("unavailable", frame.profile.name)


@dataclass(frozen=True)
class PushResult:
    profile_observations: tuple[ProfileObservation, ...] = ()
    composites: tuple[CompositeObservation, ...] = ()


def _fft(samples: tuple[float, ...], nfft: int) -> list[complex]:
    """Unnormalized forward radix-2 FFT, with explicit zero padding."""
    values = [complex(x) for x in samples] + [0j]*(nfft-len(samples))
    j = 0
    for i in range(1, nfft):
        bit = nfft >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j ^= bit
        if i < j:
            values[i], values[j] = values[j], values[i]
    width = 2
    while width <= nfft:
        half = width//2
        for j in range(half):
            angle = -math.tau*j/width
            twiddle = complex(math.cos(angle), math.sin(angle))
            for first in range(j, nfft, width):
                a, b = values[first], twiddle*values[first+half]
                values[first], values[first+half] = a+b, a-b
        width *= 2
    return values


class _Plan:
    def __init__(self, config: SpectrumConfig, index: int):
        self.profile = p = config.profiles[index]
        self.fs = config.sample_rate_hz
        m = p.window_samples
        w = ((1.0,)*m if p.window == "rectangular" else
             tuple(0.5-0.5*math.cos(math.tau*n/m) for n in range(m)))
        s1, s2 = math.fsum(w), math.fsum(x*x for x in w)
        self.window = WindowProperties(w, s1, s2, s1/m, s2/m, m*s2/(s1*s1),
                                       self.fs*s2/(s1*s1),
                                       (2 if p.window == "rectangular" else 4)*self.fs/m)
        self.frequencies = tuple(k*self.fs/p.nfft for k in range(p.nfft//2+1))
        self.bins = tuple(k for k, f in enumerate(self.frequencies)
                          if k and owner_index(config, f) == index)

    def density(self, samples: tuple[float, ...]) -> tuple[float, ...]:
        weighted = tuple(x*w for x, w in zip(samples, self.window.coefficients))
        if any(x and w and not y for x, w, y in
               zip(samples, self.window.coefficients, weighted)):
            raise ArithmeticError("window multiplication rounded to zero")
        transformed = _fft(weighted, self.profile.nfft)
        denominator = self.fs*self.window.sum_w_squared
        result = []
        for k in range(self.profile.nfft//2+1):
            magnitude = abs(transformed[k])
            squared = magnitude*magnitude
            paired = 1 if k in (0, self.profile.nfft//2) else 2
            density = paired*squared/denominator
            if not math.isfinite(density) or not math.isfinite(magnitude):
                raise ArithmeticError("nonfinite FFT or PSD result")
            if magnitude and (not squared or not density):
                raise ArithmeticError("positive spectral power rounded to zero")
            result.append(density)
        if any(weighted) and not any(result):
            raise ArithmeticError("nonzero frame collapsed to silence")
        return tuple(result)


def _pcm(value: float) -> float:
    if type(value) not in (int, float):
        raise ValueError("PCM samples must be real int/float values, excluding bool")
    # Compare before float conversion, including arbitrarily large integers.
    if not -MAX_ABS_PCM <= value <= MAX_ABS_PCM or (value and abs(value) < MIN_NONZERO_PCM):
        raise ValueError("PCM sample outside supported finite amplitude domain")
    return float(value)


class MultiresolutionSpectrum:
    """Single-caller analyzer; stage every result before changing live state."""

    def __init__(self, config: SpectrumConfig, *, epoch_id: str, start_sample: int):
        self._validate_reset_metadata(epoch_id, start_sample)
        if not isinstance(config, SpectrumConfig):
            raise ValueError("config must be SpectrumConfig")
        self._config = config
        self._plans = tuple(_Plan(config, i) for i in range(3))
        self._timeline = SampleTimeline(epoch_id, start_sample,
                                        SampleRate(config.sample_rate_hz), len(config.channel_labels))
        self._pending = self._empty_pending(config)
        self._epoch_count = 1

    @staticmethod
    def _validate_reset_metadata(epoch_id: str, start_sample: int) -> None:
        _name(epoch_id)
        _sample_index(start_sample)

    @staticmethod
    def _empty_pending(config: SpectrumConfig) -> tuple:
        return tuple(((),)*len(config.channel_labels) for _ in range(3))

    @property
    def config(self) -> SpectrumConfig:
        return self._config

    @property
    def epoch_id(self) -> str:
        return self._timeline.epoch_id

    @property
    def next_sample(self) -> int:
        return self._timeline.next_sample

    def reset_epoch(self, epoch_id: str, start_sample: int,
                    config: SpectrumConfig | None = None) -> None:
        self._validate_reset_metadata(epoch_id, start_sample)
        if self._epoch_count >= MAX_EPOCHS:
            raise ValueError("epoch limit reached; create another analyzer")
        config = self.config if config is None else config
        if not isinstance(config, SpectrumConfig):
            raise ValueError("config must be SpectrumConfig")
        plans = tuple(_Plan(config, i) for i in range(3))
        pending = self._empty_pending(config)
        timeline = deepcopy(self._timeline)
        timeline.reset_epoch(epoch_id, start_sample, SampleRate(config.sample_rate_hz),
                             len(config.channel_labels))
        self._config, self._plans, self._pending = config, plans, pending
        self._timeline, self._epoch_count = timeline, self._epoch_count+1

    def push(self, start_sample: int, planes: tuple, *, epoch_id: str) -> PushResult:
        _sample_index(start_sample)
        _name(epoch_id)
        if epoch_id != self.epoch_id:
            raise ValueError("epoch mismatch; explicit reset required")
        if start_sample != self.next_sample:
            raise DiscontinuityError("gap" if start_sample > self.next_sample else "overlap",
                                     self.next_sample, start_sample)
        config = self.config
        channels = len(config.channel_labels)
        if (not isinstance(planes, (tuple, list)) or len(planes) != channels
                or any(not isinstance(plane, (tuple, list)) for plane in planes)):
            raise ValueError("provide one tuple/list plane per channel")
        count = len(planes[0])
        _integer(count, 0, MAX_PUSH_SAMPLES, "block sample count")
        if any(len(plane) != count for plane in planes):
            raise ValueError("channel planes must have identical lengths")
        _sample_index(start_sample+count)
        offsets = tuple(range(0, len(old[0])+count-p.window_samples+1, p.hop_samples)
                        for old, p in zip(self._pending, config.profiles))
        frame_count = sum(len(r) for r in offsets)
        work = channels*sum(len(r)*p.nfft*(p.nfft.bit_length()-1)
                            for r, p in zip(offsets, config.profiles))
        output_count = channels*sum(len(r)*(p.nfft//2+1)
                                    for r, p in zip(offsets, config.profiles))
        if frame_count > MAX_PROFILE_FRAMES:
            raise ValueError("callback exceeds completed profile frame limit")
        if work > MAX_WORK_UNITS or output_count > MAX_OUTPUT_VALUES:
            raise ValueError("callback exceeds work/output limit")
        if not count:
            return PushResult()
        samples = tuple(tuple(_pcm(x) for x in plane) for plane in planes)
        pending = []
        frames = []
        for i, (plan, old, starts) in enumerate(zip(self._plans, self._pending, offsets)):
            p = plan.profile
            staged = tuple(history+plane for history, plane in zip(old, samples))
            origin = start_sample-len(old[0])
            for offset in starts:
                start = origin+offset
                readings = tuple(ChannelPSD(label, plan.density(plane[offset:offset+p.window_samples]))
                                 for label, plane in zip(config.channel_labels, staged))
                frames.append((i, ProfileObservation(
                    epoch_id, start, start+p.window_samples, 2*start+p.window_samples-1,
                    config, p, plan.window, plan.frequencies, readings)))
            consumed = starts[-1]+p.hop_samples if starts else 0
            pending.append(tuple(plane[consumed:] for plane in staged))
        frames.sort(key=lambda item: (item[1].end_sample_exclusive, item[0]))
        common = {}
        first = self._timeline.origin_sample+config.first_composite_samples
        hop = config.composite_hop_samples
        for i, frame in frames:
            end = frame.end_sample_exclusive
            if end >= first and (end-first) % hop == 0:
                common.setdefault(end, {})[i] = frame
        composites = []
        for end, group in sorted(common.items()):
            if set(group) != {0, 1, 2}:
                raise ArithmeticError("common-end schedule lost a contributor")
            contributors = tuple(group[i] for i in range(3))
            selections = tuple(FrequencySelection(plan.profile.name,
                               "ok" if plan.bins else "unavailable", plan.bins)
                               for plan in self._plans)
            composites.append(CompositeObservation(epoch_id, end, contributors, selections))
        result = PushResult(tuple(frame for _, frame in frames), tuple(composites))
        new_pending = tuple(pending)
        timeline = deepcopy(self._timeline)
        timeline.ingest(start_sample, count, channels)
        # Nothing above changed live state; the assignments below cannot run user code.
        self._timeline, self._pending = timeline, new_pending
        return result
