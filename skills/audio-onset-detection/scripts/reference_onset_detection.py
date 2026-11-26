"""Bounded offline onset detection from calibrated frames or short PCM runs."""

from __future__ import annotations

from bisect import bisect_left
from collections import deque
from dataclasses import dataclass
from fractions import Fraction
from math import isfinite, log, log1p
from statistics import median
from typing import Literal, Optional, Sequence, Union

from reference_oscilloscope import MAX_SAMPLE_INDEX, ScopeEpoch
from reference_stereo_correlation import _sqrt_binary64
from reference_stft import MAX_REFERENCE_FRAMES, MAX_REFERENCE_NFFT, stft_chunked


MAX_FEATURE_NFFT = 4096
MAX_HISTORY_FRAMES = 128
Scalar = Union[float, int]
ScoreSource = Literal["flux", "rms_rise"]
Contribution = tuple[int, Fraction]
_ZERO = Fraction()


def _check_integer(value: int, name: str, lower: int, upper: int) -> None:
    if type(value) is not int or not lower <= value <= upper:
        raise ValueError(f"{name} must be an integer in [{lower}, {upper}]")


def _binary64(value: Scalar, name: str, *, nonnegative: bool = False) -> float:
    if type(value) not in (float, int):
        raise ValueError(f"{name} must be a finite binary64 value")
    try:
        number = float(value)
    except OverflowError as error:
        raise ValueError(f"{name} exceeds binary64 range") from error
    if not isfinite(number) or number != value or (nonnegative and number < 0):
        raise ValueError(f"invalid {name}")
    return number


@dataclass(frozen=True)
class OnsetGrid:
    """Exact clock and window for one selected channel or declared mix."""

    epoch: ScopeEpoch
    window: tuple[float, ...]
    fft_length: int
    hop: int
    first_start_sample: Optional[int] = None

    def __post_init__(self) -> None:
        if type(self.epoch) is not ScopeEpoch or len(self.epoch.channel_ids) != 1:
            raise ValueError("supply an epoch for one selected channel or mix")
        if type(self.window) not in (tuple, list):
            raise ValueError("supply the actual window coefficients")
        _check_integer(self.fft_length, "FFT length", 2, MAX_FEATURE_NFFT)
        _check_integer(len(self.window), "window length", 2, self.fft_length)
        _check_integer(self.hop, "hop", 1, len(self.window))
        window = tuple(_binary64(w, "window coefficient") for w in self.window)
        if sum(map(Fraction, window)) <= 0:
            raise ValueError("amplitude calibration requires a positive coherent sum")
        start = self.first_start_sample
        if start is None:
            start = self.epoch.origin_sample
        _check_integer(start, "first frame start", self.epoch.origin_sample, MAX_SAMPLE_INDEX)
        object.__setattr__(self, "first_start_sample", start)
        object.__setattr__(self, "window", window)

    @property
    def window_length(self) -> int:
        return len(self.window)

    @property
    def bin_count(self) -> int:
        return self.fft_length // 2 + 1


@dataclass(frozen=True)
class OnsetProfile:
    lag: int = 1
    neighbor_radius: int = 0
    amplitude_reference: Optional[float] = None
    weights: Optional[tuple[float, ...]] = None
    source: ScoreSource = "flux"
    left: int = 1
    right: int = 1
    background: int = 4
    margin: float = 0.0
    refractory_samples: int = 0

    def __post_init__(self) -> None:
        for name in ("lag", "left", "right", "background"):
            _check_integer(getattr(self, name), name, 1, MAX_HISTORY_FRAMES)
        _check_integer(self.neighbor_radius, "neighbor radius", 0, MAX_FEATURE_NFFT // 2)
        _check_integer(self.refractory_samples, "refractory samples", 0, MAX_SAMPLE_INDEX)
        if type(self.source) is not str or self.source not in ("flux", "rms_rise"):
            raise ValueError("select flux or rms_rise")
        object.__setattr__(self, "margin", _binary64(self.margin, "margin", nonnegative=True))
        if self.amplitude_reference is not None:
            reference = _binary64(self.amplitude_reference, "amplitude reference", nonnegative=True)
            if reference == 0:
                raise ValueError("amplitude reference must be positive")
            object.__setattr__(self, "amplitude_reference", reference)
        if self.weights is not None:
            if type(self.weights) not in (tuple, list):
                raise ValueError("supply one weight per nonnegative bin")
            _check_integer(len(self.weights), "weight count", 2, MAX_FEATURE_NFFT // 2 + 1)
            weights = tuple(_binary64(w, "bin weight", nonnegative=True) for w in self.weights)
            object.__setattr__(self, "weights", weights)


@dataclass(frozen=True)
class OnsetFrame:
    """A complete real frame with one-sided peak amplitudes and weighted RMS."""

    grid: OnsetGrid
    start_sample: int
    end_sample_exclusive: int
    amplitudes: tuple[float, ...]
    weighted_rms: float

    def __post_init__(self) -> None:
        if type(self.grid) is not OnsetGrid:
            raise ValueError("supply an onset grid")
        _check_integer(self.start_sample, "frame start", self.grid.first_start_sample, MAX_SAMPLE_INDEX)
        _check_integer(self.end_sample_exclusive, "frame end", self.start_sample, MAX_SAMPLE_INDEX)
        if self.end_sample_exclusive - self.start_sample != self.grid.window_length:
            raise ValueError("frame must have complete window support")
        if type(self.amplitudes) not in (tuple, list) or len(self.amplitudes) != self.grid.bin_count:
            raise ValueError("supply one calibrated amplitude per nonnegative bin")
        values = tuple(_binary64(v, "bin amplitude", nonnegative=True) for v in self.amplitudes)
        rms = _binary64(self.weighted_rms, "weighted RMS", nonnegative=True)
        object.__setattr__(self, "amplitudes", values)
        object.__setattr__(self, "weighted_rms", rms)


@dataclass(frozen=True)
class NoveltyPoint:
    frame: OnsetFrame
    profile: OnsetProfile
    reference_start_sample: Optional[int]
    flux: Optional[Fraction]
    rms_rise: Optional[Fraction]
    contributions: tuple[Contribution, ...]

    @property
    def center_sample_twice(self) -> int:
        return self.frame.start_sample + self.frame.end_sample_exclusive - 1


@dataclass(frozen=True)
class OnsetEvent:
    peak: NoveltyPoint
    score_source: ScoreSource
    score: Fraction
    ready_sample_exclusive: int
    observed_release_sample_exclusive: Optional[int]

    @property
    def estimated_sample_twice(self) -> int:
        return self.peak.center_sample_twice


def _maximum_neighbors(values: tuple[Fraction, ...], radius: int) -> tuple[Fraction, ...]:
    if radius == 0:
        return values

    # Keep the largest candidate at the front of the clipped moving window.
    maxima = []
    indices = deque()
    right = 0
    for k in range(len(values)):
        while indices and indices[0] < k - radius:
            indices.popleft()
        while right < min(len(values), k + radius + 1):
            while indices and values[indices[-1]] <= values[right]:
                indices.pop()
            indices.append(right)
            right += 1
        maxima.append(values[indices[0]])
    return tuple(maxima)


def _log_change(increase: Fraction, reference_level: Fraction) -> Fraction:
    ratio = increase / reference_level
    try:
        result = log1p(float(ratio))
    except OverflowError:
        # log(1 + q) = log(q) + log(1 + 1/q) for q beyond binary64 range.
        result = log(ratio.numerator) - log(ratio.denominator) + log1p(float(1 / ratio))
    if result == 0:
        raise ValueError("positive log change underflows binary64")
    return Fraction(result)


class OnsetDetector:
    """Consume one complete frame at a time and retain bounded history."""

    def __init__(self, grid: OnsetGrid, profile: OnsetProfile = OnsetProfile()) -> None:
        self._begin(grid, profile)

    def _begin(self, grid: OnsetGrid, profile: OnsetProfile) -> None:
        if type(grid) is not OnsetGrid or type(profile) is not OnsetProfile:
            raise ValueError("supply a grid and detection profile")
        if profile.neighbor_radius >= grid.bin_count:
            raise ValueError("neighbor radius exceeds the bin grid")
        if profile.weights is not None and len(profile.weights) != grid.bin_count:
            raise ValueError("weight count must match the bin grid")
        weights = profile.weights if profile.weights is not None else (1.0,) * grid.bin_count
        reference = profile.amplitude_reference
        self._grid = grid
        self._profile = profile
        self._weights = tuple(map(Fraction, weights))
        self._amplitude_reference = None if reference is None else Fraction(reference)
        self._next_start = grid.first_start_sample
        self._lagged = deque(maxlen=profile.lag)
        self._scores = deque(maxlen=max(profile.left, profile.background) + profile.right)
        self._last_peak_twice = None
        self._last_observed_boundary = None

    def reset(self, grid: OnsetGrid, profile: Optional[OnsetProfile] = None) -> None:
        """Start at the first frame of a new epoch with empty histories."""
        if type(grid) is not OnsetGrid or grid.epoch.epoch_id == self._grid.epoch.epoch_id:
            raise ValueError("reset requires a new epoch")
        self._begin(grid, self._profile if profile is None else profile)

    def _novelty(self, frame: OnsetFrame, levels: tuple[Fraction, ...]) -> NoveltyPoint:
        if len(self._lagged) < self._profile.lag:
            return NoveltyPoint(frame, self._profile, None, None, None, ())
        previous, previous_levels = self._lagged[0]
        nearby = _maximum_neighbors(previous_levels, self._profile.neighbor_radius)
        reference = self._amplitude_reference
        contributions = []
        for k, (now, before, weight) in enumerate(zip(levels, nearby, self._weights)):
            if weight and now > before:
                increase = now - before
                if reference is not None:
                    increase = _log_change(increase, reference + before)
                contributions.append((k, weight * increase))
        flux = sum((value for _, value in contributions), _ZERO)
        rms_rise = max(_ZERO, Fraction(frame.weighted_rms) - Fraction(previous.weighted_rms))
        return NoveltyPoint(frame, self._profile, previous.start_sample, flux, rms_rise, tuple(contributions))

    def _pick(
        self, point: NoveltyPoint, score: Fraction, observed_boundary: Optional[int]
    ) -> Optional[OnsetEvent]:
        if len(self._scores) < self._scores.maxlen:
            return None
        profile = self._profile
        context = [*self._scores, (point, score)]
        index = len(context) - 1 - profile.right
        peak, value = context[index]
        if value <= max(s for _, s in context[index - profile.left:index]):
            return None
        if value < max(s for _, s in context[index + 1:]):
            return None
        baseline = median(s for _, s in context[index - profile.background:index])
        if value <= baseline + Fraction(profile.margin):
            return None
        if self._last_peak_twice is not None:
            if peak.center_sample_twice - self._last_peak_twice < 2 * profile.refractory_samples:
                return None
        return OnsetEvent(peak, profile.source, value, point.frame.end_sample_exclusive, observed_boundary)

    def push(
        self, frame: OnsetFrame, *, observed_release_sample_exclusive: Optional[int] = None
    ) -> tuple[NoveltyPoint, Optional[OnsetEvent]]:
        """Return the new score and any earlier peak confirmed by this frame."""
        if type(frame) is not OnsetFrame or frame.grid != self._grid:
            raise ValueError("frame grid or epoch changed")
        if frame.start_sample != self._next_start:
            raise ValueError("unexpected frame start, check for a gap or overlap")
        observed = observed_release_sample_exclusive
        if observed is not None:
            lower = frame.end_sample_exclusive
            if self._last_observed_boundary is not None:
                lower = max(lower, self._last_observed_boundary)
            _check_integer(observed, "observed release boundary", lower, MAX_SAMPLE_INDEX)

        levels = tuple(map(Fraction, frame.amplitudes))
        point = self._novelty(frame, levels)
        score = point.flux if self._profile.source == "flux" else point.rms_rise
        event = None if score is None else self._pick(point, score, observed)

        self._lagged.append((frame, levels))
        self._next_start += self._grid.hop
        if score is not None:
            self._scores.append((point, score))
        if event is not None:
            self._last_peak_twice = event.peak.center_sample_twice
        if observed is not None:
            self._last_observed_boundary = observed
        return point, event


@dataclass(frozen=True)
class OnsetRun:
    novelty: tuple[NoveltyPoint, ...]
    events: tuple[OnsetEvent, ...]


def analyze_pcm_chunks(
    chunks: Sequence[tuple[int, Sequence[Scalar]]],
    grid: OnsetGrid,
    profile: OnsetProfile = OnsetProfile(),
) -> OnsetRun:
    """Use the shared STFT for one contiguous, bounded offline PCM run."""
    detector = OnsetDetector(grid, profile)
    if grid.fft_length > MAX_REFERENCE_NFFT:
        raise ValueError("PCM exceeds shared STFT limit; supply calibrated frames")
    if type(chunks) not in (list, tuple):
        raise ValueError("supply a list or tuple of PCM blocks")
    samples = []
    blocks = []
    boundaries = []
    origin = grid.first_start_sample
    end = origin
    limit = grid.window_length + MAX_REFERENCE_FRAMES * grid.hop - 1
    for chunk in chunks:
        if type(chunk) is not tuple or len(chunk) != 2:
            raise ValueError("supply each PCM block as a (start, samples) pair")
        start, values = chunk
        if type(start) is not int or start != end:
            raise ValueError("PCM blocks must be contiguous and begin at the grid start")
        if type(values) not in (list, tuple) or not values:
            raise ValueError("PCM blocks must contain a nonempty list or tuple of samples")
        end += len(values)
        if end > MAX_SAMPLE_INDEX or end - origin > limit:
            raise ValueError("PCM exceeds sample or shared STFT frame limit")
        block = [_binary64(v, "PCM sample") for v in values]
        samples.extend(block)
        blocks.append(block)
        boundaries.append(end)

    try:
        rate = float(grid.epoch.rate_hz)
        stft = stft_chunked(blocks, list(grid.window), rate, grid.hop, grid.fft_length, "amplitude", origin)
    except OverflowError as error:
        raise ValueError("PCM STFT or rate exceeds binary64 range") from error

    squares = tuple(Fraction(w)**2 for w in grid.window)
    window_energy = sum(squares)
    novelty = []
    events = []
    for row in stft["frames"]:
        start = row["start_sample"] - origin
        power = sum(w2 * Fraction(samples[start + j])**2 for j, w2 in enumerate(squares))
        rms = _sqrt_binary64(power / window_energy)
        if power and (rms == 0 or not any(row["values"])):
            raise ValueError("nonzero weighted PCM frame underflows binary64")
        frame = OnsetFrame(
            grid, row["start_sample"], row["end_sample_exclusive"], row["values"], rms
        )
        release = boundaries[bisect_left(boundaries, frame.end_sample_exclusive)]
        point, event = detector.push(frame, observed_release_sample_exclusive=release)
        novelty.append(point)
        if event is not None:
            events.append(event)
    return OnsetRun(tuple(novelty), tuple(events))


@dataclass(frozen=True)
class OnsetMatch:
    reference_index: int
    estimate_index: int
    error_sample_twice: int


@dataclass(frozen=True)
class OnsetEvaluation:
    eligible_interval_twice: tuple[int, int]
    tolerance_sample_twice: int
    matches: tuple[OnsetMatch, ...]
    unmatched_references: tuple[int, ...]
    unmatched_estimates: tuple[int, ...]

    @property
    def true_positives(self) -> int:
        return len(self.matches)

    @property
    def false_positives(self) -> int:
        return len(self.unmatched_estimates)

    @property
    def false_negatives(self) -> int:
        return len(self.unmatched_references)

    @property
    def precision(self) -> Optional[Fraction]:
        tp = self.true_positives
        denominator = tp + self.false_positives
        return Fraction(tp, denominator) if denominator else None

    @property
    def recall(self) -> Optional[Fraction]:
        tp = self.true_positives
        denominator = tp + self.false_negatives
        return Fraction(tp, denominator) if denominator else None

    @property
    def f1(self) -> Optional[Fraction]:
        numerator = 2 * self.true_positives
        denominator = numerator + self.false_positives + self.false_negatives
        return Fraction(numerator, denominator) if denominator else None


def _ordered_times(
    times: Sequence[int], eligible_interval: tuple[int, int]
) -> list[tuple[int, int]]:
    if type(times) not in (list, tuple):
        raise ValueError("supply a list or tuple of doubled sample times")
    for value in times:
        _check_integer(value, "event time", eligible_interval[0], eligible_interval[1] - 1)
    return sorted(enumerate(times), key=lambda entry: entry[1])


def match_onsets(
    reference_times_twice: Sequence[int], estimate_times_twice: Sequence[int], *,
    tolerance_sample_twice: int, eligible_interval_twice: tuple[int, int],
) -> OnsetEvaluation:
    """Match events on one clock within one eligible interval and tolerance."""
    _check_integer(tolerance_sample_twice, "tolerance", 0, 2 * MAX_SAMPLE_INDEX)
    if type(eligible_interval_twice) is not tuple or len(eligible_interval_twice) != 2:
        raise ValueError("supply one half-open eligible interval in doubled samples")
    start, end = eligible_interval_twice
    _check_integer(start, "eligible start", 0, 2 * MAX_SAMPLE_INDEX)
    _check_integer(end, "eligible end", start + 1, 2 * MAX_SAMPLE_INDEX + 1)
    references = _ordered_times(reference_times_twice, eligible_interval_twice)
    estimates = _ordered_times(estimate_times_twice, eligible_interval_twice)
    i = j = 0
    matches = []
    while i < len(references) and j < len(estimates):
        ref_index, ref_time = references[i]
        est_index, est_time = estimates[j]
        error = est_time - ref_time
        if error < -tolerance_sample_twice:
            j += 1
        elif error > tolerance_sample_twice:
            i += 1
        else:
            matches.append(OnsetMatch(ref_index, est_index, error))
            i += 1
            j += 1
    used_refs = {m.reference_index for m in matches}
    used_ests = {m.estimate_index for m in matches}
    return OnsetEvaluation(
        eligible_interval_twice, tolerance_sample_twice, tuple(matches),
        tuple(i for i in range(len(references)) if i not in used_refs),
        tuple(j for j in range(len(estimates)) if j not in used_ests),
    )
