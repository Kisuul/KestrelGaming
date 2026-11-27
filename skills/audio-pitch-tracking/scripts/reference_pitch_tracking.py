"""Bounded, sample-clocked monophonic pitch candidate reference."""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from math import ceil, floor, isfinite
from typing import Literal, Optional, Sequence, Union

from reference_oscilloscope import MAX_SAMPLE_INDEX, PCMSample, ScopeEpoch
from reference_oscilloscope import _check_integer, _freeze_planes


MAX_COMPARISON_SAMPLES = 4096
MAX_EVALUATED_LAG = 4096
MAX_BLOCK_SAMPLES = MAX_COMPARISON_SAMPLES + MAX_EVALUATED_LAG
MAX_FRAMES_PER_BLOCK = 128

Scalar = Union[int, float, Fraction]
Refinement = Literal["integer", "raw", "cmnd"]
FitMethod = Literal["integer", "raw", "cmnd", "integer_fallback"]
CandidateStatus = Literal["eligible", "threshold_rejected", "out_of_band"]
PitchStatus = Literal["unavailable", "silence", "dc_only", "below_floor", "unvoiced", "voiced"]
_ZERO = Fraction()
_ONE = Fraction(1)
_HALF = Fraction(1, 2)


def _scalar(value: Scalar, name: str) -> Fraction:
    if type(value) not in (int, float, Fraction) or (type(value) is float and not isfinite(value)):
        raise ValueError(f"{name} must be a finite real number")
    return Fraction(value)


@dataclass(frozen=True)
class PitchProfile:
    comparison_samples: int
    minimum_hz: Scalar
    maximum_hz: Scalar
    threshold: Scalar = Fraction(1, 10)
    ac_rms_floor: Scalar = 0
    refinement: Refinement = "raw"

    def __post_init__(self) -> None:
        _check_integer(self.comparison_samples, "comparison samples", 1, MAX_COMPARISON_SAMPLES)
        minimum = _scalar(self.minimum_hz, "minimum frequency")
        maximum = _scalar(self.maximum_hz, "maximum frequency")
        threshold = _scalar(self.threshold, "CMND threshold")
        rms_floor = _scalar(self.ac_rms_floor, "AC RMS floor")
        if not 0 < minimum <= maximum:
            raise ValueError("supply a positive ordered frequency band")
        if not 0 < threshold <= 1 or rms_floor < 0:
            raise ValueError("use a CMND threshold in (0, 1] and a nonnegative AC RMS floor")
        if self.refinement not in ("integer", "raw", "cmnd"):
            raise ValueError("select integer, raw, or cmnd refinement")
        object.__setattr__(self, "minimum_hz", minimum)
        object.__setattr__(self, "maximum_hz", maximum)
        object.__setattr__(self, "threshold", threshold)
        object.__setattr__(self, "ac_rms_floor", rms_floor)


@dataclass(frozen=True)
class PitchGrid:
    epoch: ScopeEpoch
    profile: PitchProfile
    hop_samples: int
    first_start_sample: Optional[int] = None
    period_min: Fraction = field(init=False)
    period_max: Fraction = field(init=False)
    first_seed_lag: int = field(init=False)
    last_seed_lag: int = field(init=False)
    maximum_lag: int = field(init=False)

    def __post_init__(self) -> None:
        if type(self.epoch) is not ScopeEpoch or len(self.epoch.channel_ids) != 1:
            raise ValueError("supply an epoch for one channel or declared mix")
        if type(self.profile) is not PitchProfile:
            raise ValueError("supply a PitchProfile")
        band = self.profile
        rate = self.epoch.rate_hz
        if band.maximum_hz > rate / 2:
            raise ValueError("the frequency band must lie at or below Nyquist")
        lo, hi = rate / band.maximum_hz, rate / band.minimum_hz
        if band.refinement == "integer":
            first, last = ceil(lo), floor(hi)
        else:
            first, last = floor(lo), ceil(hi)
        maximum = last + 1
        _check_integer(maximum, "last evaluated lag", 3, MAX_EVALUATED_LAG)
        length = band.comparison_samples + maximum
        _check_integer(self.hop_samples, "hop", 1, length)
        start = self.epoch.origin_sample if self.first_start_sample is None else self.first_start_sample
        _check_integer(start, "first frame start", self.epoch.origin_sample, MAX_SAMPLE_INDEX - length)
        object.__setattr__(self, "first_start_sample", start)
        object.__setattr__(self, "period_min", lo)
        object.__setattr__(self, "period_max", hi)
        object.__setattr__(self, "first_seed_lag", first)
        object.__setattr__(self, "last_seed_lag", last)
        object.__setattr__(self, "maximum_lag", maximum)

    @property
    def frame_length(self) -> int:
        return self.profile.comparison_samples + self.maximum_lag


@dataclass(frozen=True)
class PitchDifference:
    raw: tuple[Fraction, ...]
    cmnd: tuple[Optional[Fraction], ...]


@dataclass(frozen=True)
class PitchCandidate:
    seed_lag: int
    depth: Fraction
    period_samples: Fraction
    frequency_hz: Fraction
    method: FitMethod
    status: CandidateStatus


@dataclass(frozen=True)
class PitchFrame:
    grid: PitchGrid
    start_sample: int
    available_end_sample_exclusive: int
    observed_release_sample_exclusive: Optional[int]
    status: PitchStatus
    mean_pcm: Optional[Fraction] = None
    ac_mean_square: Optional[Fraction] = None
    difference: Optional[PitchDifference] = None
    candidates: tuple[PitchCandidate, ...] = ()
    selected: Optional[PitchCandidate] = None

    @property
    def end_sample_exclusive(self) -> int:
        return self.start_sample + self.grid.frame_length

    @property
    def center_sample_twice(self) -> int:
        return self.start_sample + self.end_sample_exclusive - 1

    @property
    def ready_sample_exclusive(self) -> Optional[int]:
        return None if self.status == "unavailable" else self.end_sample_exclusive


def _pcm(samples: Sequence[PCMSample], limit: int) -> tuple[PCMSample, ...]:
    if type(samples) not in (list, tuple):
        raise ValueError("supply a list or tuple of mono PCM samples")
    return _freeze_planes((samples,), 1, limit)[0] if samples else ()


def _shared_denominator(samples: tuple[PCMSample, ...]) -> tuple[tuple[int, ...], int]:
    # Finite binary64 samples are dyadic. Convert once, then compare integers
    # so a small difference survives beside a large DC level or dynamic range.
    ratios = [sample.as_integer_ratio() for sample in samples]
    scale = max(denominator for _, denominator in ratios)
    return tuple(numerator * (scale // denominator) for numerator, denominator in ratios), scale


def _difference(
    grid: PitchGrid, data: tuple[int, ...], scale: int, constant: bool,
) -> PitchDifference:
    maximum = grid.maximum_lag
    if constant:
        return PitchDifference((_ZERO,) * (maximum + 1), (_ONE,) + (None,) * maximum)
    width = grid.profile.comparison_samples
    first = data[:width]
    scale_squared = scale**2
    raw = [_ZERO]
    normalized = [_ONE]
    cumulative = 0
    for lag in range(1, maximum + 1):
        squares = sum((a - b)**2 for a, b in zip(first, data[lag:lag + width]))
        cumulative += squares
        raw.append(Fraction(squares, scale_squared))
        normalized.append(Fraction(lag * squares, cumulative) if cumulative else None)
    return PitchDifference(tuple(raw), tuple(normalized))


def _refine(values: Sequence[Optional[Fraction]], lag: int) -> Optional[Fraction]:
    left, center, right = values[lag - 1:lag + 2]
    if left is None or center is None or right is None or center > min(left, right):
        return None
    curvature = left - 2 * center + right
    if curvature <= 0:
        return None
    delta = (left - right) / (2 * curvature)
    if abs(delta) > _HALF:
        return None
    return lag + delta


def _candidates(grid: PitchGrid, curve: PitchDifference) -> tuple[PitchCandidate, ...]:
    band = grid.profile
    candidates = []
    for lag in range(grid.first_seed_lag, grid.last_seed_lag + 1):
        left, depth, right = curve.cmnd[lag - 1:lag + 2]
        if left is None or depth is None or right is None or depth >= left or depth > right:
            continue
        method = band.refinement
        period = Fraction(lag)
        if method != "integer":
            fitted = _refine(curve.raw if method == "raw" else curve.cmnd, lag)
            if fitted is None:
                method = "integer_fallback"
            else:
                period = fitted
        status = "eligible"
        if not grid.period_min <= period <= grid.period_max:
            status = "out_of_band"
        elif depth >= band.threshold:
            status = "threshold_rejected"
        candidates.append(PitchCandidate(lag, depth, period, grid.epoch.rate_hz / period, method, status))
    return tuple(candidates)


def _complete(
    samples: tuple[PCMSample, ...], grid: PitchGrid, start: int, observed: Optional[int],
) -> PitchFrame:
    data, scale = _shared_denominator(samples)
    total = sum(data)
    size = len(data)
    mean = Fraction(total, size * scale)
    energy = sum(sample**2 for sample in data)
    ac_power = Fraction(size * energy - total**2, (size * scale)**2)
    curve = _difference(grid, data, scale, constant=ac_power == 0)
    candidates = _candidates(grid, curve)
    selected = None
    if ac_power == 0:
        status = "dc_only" if mean else "silence"
    elif ac_power < grid.profile.ac_rms_floor**2:
        status = "below_floor"
    else:
        selected = next((candidate for candidate in candidates if candidate.status == "eligible"), None)
        status = "voiced" if selected is not None else "unvoiced"
    return PitchFrame(
        grid, start, start + size, observed, status, mean, ac_power, curve, candidates, selected,
    )


def measure_pitch(
    samples: Sequence[PCMSample], grid: PitchGrid, *, start_sample: Optional[int] = None,
    observed_release_sample_exclusive: Optional[int] = None,
) -> PitchFrame:
    """Analyze one grid position. A short input stays unavailable."""
    if type(grid) is not PitchGrid:
        raise ValueError("supply a PitchGrid")
    start = grid.first_start_sample if start_sample is None else start_sample
    _check_integer(start, "frame start", grid.first_start_sample, MAX_SAMPLE_INDEX - grid.frame_length)
    if (start - grid.first_start_sample) % grid.hop_samples:
        raise ValueError("frame start must align to the declared hop")
    pcm = _pcm(samples, grid.frame_length)
    end = start + len(pcm)
    observed = observed_release_sample_exclusive
    if observed is not None:
        _check_integer(observed, "observed release boundary", end, MAX_SAMPLE_INDEX)
    if len(pcm) < grid.frame_length:
        return PitchFrame(grid, start, end, observed, "unavailable")
    return _complete(pcm, grid, start, observed)


class PitchTracker:
    """Assemble complete frames from contiguous blocks on one sample clock."""

    def __init__(self, grid: PitchGrid) -> None:
        self._begin(grid)

    def _begin(self, grid: PitchGrid) -> None:
        if type(grid) is not PitchGrid:
            raise ValueError("supply a PitchGrid")
        self._grid = grid
        self._next_input = grid.first_start_sample
        self._frame_start = grid.first_start_sample
        self._pending = ()

    def reset(self, grid: PitchGrid) -> None:
        """Begin a new epoch with empty frame history."""
        if type(grid) is not PitchGrid or grid.epoch.epoch_id == self._grid.epoch.epoch_id:
            raise ValueError("reset requires a new epoch")
        self._begin(grid)

    def push(self, start_sample: int, samples: Sequence[PCMSample]) -> tuple[PitchFrame, ...]:
        """Return complete frames and the delivery boundary that supplied them."""
        if type(start_sample) is not int or start_sample != self._next_input:
            raise ValueError("PCM blocks must follow one another on the sample clock")
        block = _pcm(samples, MAX_BLOCK_SAMPLES)
        end = start_sample + len(block)
        _check_integer(end, "block end", start_sample, MAX_SAMPLE_INDEX)
        pcm = self._pending + block
        grid = self._grid
        length, hop = grid.frame_length, grid.hop_samples
        starts = range(0, len(pcm) - length + 1, hop)
        if len(starts) > MAX_FRAMES_PER_BLOCK:
            raise ValueError("too many complete frames in one delivery block")
        frames = tuple(_complete(pcm[i:i + length], grid, self._frame_start + i, end) for i in starts)
        consumed = len(starts) * hop
        self._pending = pcm[consumed:]
        self._frame_start += consumed
        self._next_input = end
        return frames
