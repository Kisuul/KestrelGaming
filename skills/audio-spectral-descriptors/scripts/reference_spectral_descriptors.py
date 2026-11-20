"""Offline descriptors of a single calibrated one-sided PSD and adjacent-frame flux."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math

MAX_NFFT = 32768
MAX_SAMPLE_RATE = 384000
MAX_SAMPLE_INDEX = (1 << 256) - 1
MIN_POSITIVE_PSD = 2.0**-800
MAX_PSD = 2.0**800


def _integer(value: int, low: int, high: int, name: str) -> None:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in [{low}, {high}]")


@dataclass(frozen=True)
class PSDContext:
    """Identity, amplitude unit, and transform settings of one PSD stream."""

    clock_id: str
    epoch_id: str
    source_tap: str
    channel: str
    amplitude_unit: str
    calibration_id: str
    profile_id: str
    window_id: str
    sample_rate_hz: int
    window_samples: int
    nfft: int
    hop_samples: int
    detrend: str = "none"

    def __post_init__(self) -> None:
        for name in ("clock_id", "epoch_id", "source_tap", "channel", "amplitude_unit",
                     "calibration_id", "profile_id", "window_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip() or len(value) > 128:
                raise ValueError(f"{name} must be a nonblank string of at most 128 characters")
        _integer(self.sample_rate_hz, 2, MAX_SAMPLE_RATE, "sample_rate_hz")
        _integer(self.nfft, 2, MAX_NFFT, "nfft")
        _integer(self.window_samples, 2, self.nfft, "window_samples")
        _integer(self.hop_samples, 1, MAX_NFFT, "hop_samples")
        if self.detrend not in ("none", "mean"):
            raise ValueError("detrend must be 'none' or 'mean'")


@dataclass(frozen=True)
class PSDFrame:
    """A complete immutable one-sided PSD in squared amplitude units per Hz."""

    context: PSDContext
    start_sample: int
    psd: tuple[float, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.context, PSDContext):
            raise ValueError("frame requires a PSDContext")
        _integer(self.start_sample, 0, MAX_SAMPLE_INDEX-self.context.window_samples, "start_sample")
        if not isinstance(self.psd, tuple) or len(self.psd) != self.context.nfft//2+1:
            raise ValueError("PSD must be a tuple with nfft//2+1 ordinates")
        for value in self.psd:
            if (type(value) not in (float, int)
                    or not (value == 0 or MIN_POSITIVE_PSD <= value <= MAX_PSD)):
                raise ValueError("PSD ordinates must be zero or finite values in [2**-800, 2**800]")
        object.__setattr__(self, "psd", tuple(float(value) for value in self.psd))

    @property
    def end_sample_exclusive(self) -> int:
        return self.start_sample + self.context.window_samples

    @property
    def center_sample_twice(self) -> int:
        return 2*self.start_sample + self.context.window_samples - 1


@dataclass(frozen=True)
class DescriptorOptions:
    """Select a half-open band and a rational cumulative power fraction."""

    low_hz: float = 0.0
    high_hz: float | None = None
    include_dc: bool = False
    include_nyquist: bool = True
    rolloff_fraction: Fraction = Fraction(17, 20)

    def __post_init__(self) -> None:
        edges = (self.low_hz,) if self.high_hz is None else (self.low_hz, self.high_hz)
        for edge in edges:
            if type(edge) not in (float, int) or not 0 <= edge <= MAX_SAMPLE_RATE/2:
                raise ValueError("band edges must be finite, nonnegative frequencies")
        if self.high_hz is not None and self.low_hz >= self.high_hz:
            raise ValueError("band must have positive width")
        if type(self.include_dc) is not bool or type(self.include_nyquist) is not bool:
            raise ValueError("DC and Nyquist options must be Boolean")
        if not isinstance(self.rolloff_fraction, Fraction) or not 0 < self.rolloff_fraction < 1:
            raise ValueError("rolloff_fraction must be a Fraction strictly between zero and one")


@dataclass(frozen=True)
class DescriptorResult:
    frame: PSDFrame
    options: DescriptorOptions
    bin_indices: tuple[int, ...]
    status: str
    total_power: float | None
    centroid_hz: float | None = None
    spread_hz: float | None = None
    rolloff_bin: int | None = None
    rolloff_hz: float | None = None
    flatness: float | None = None
    crest: float | None = None
    entropy_nats: float | None = None
    normalized_entropy: float | None = None
    underflowed: tuple[str, ...] = ()


@dataclass(frozen=True)
class FluxResult:
    status: str
    previous_start_sample: int | None = None
    power_flux: float | None = None
    shape_flux: float | None = None


@dataclass(frozen=True)
class Observation:
    descriptors: DescriptorResult
    flux: FluxResult


@dataclass(frozen=True)
class _Measurement:
    descriptors: DescriptorResult
    weights: tuple[int, ...] = ()
    total: int = 0


def _options(value: DescriptorOptions) -> None:
    if not isinstance(value, DescriptorOptions):
        raise ValueError("expected DescriptorOptions")


def _frame(value: PSDFrame) -> None:
    if not isinstance(value, PSDFrame):
        raise ValueError("expected one PSDFrame from one profile")


def _select(frame: PSDFrame, options: DescriptorOptions) -> tuple[int, ...]:
    fs, nfft = frame.context.sample_rate_hz, frame.context.nfft
    nyquist = fs/2
    high = nyquist if options.high_hz is None else options.high_hz
    if not options.low_hz < high <= nyquist:
        raise ValueError("band must have positive width and end at or below Nyquist")
    first = 0 if options.include_dc else 1
    bins = [k for k in range(first, len(frame.psd))
            if options.low_hz <= k*fs/nfft < high]
    if nfft % 2 == 0 and high == nyquist and options.include_nyquist:
        bins.append(nfft//2)
    return tuple(bins)


def _integer_weights(values: tuple[float, ...]) -> tuple[tuple[int, ...], int]:
    # Every binary64 ordinate is a rational with a power-of-two denominator.
    ratios = [value.as_integer_ratio() for value in values]
    denominator = max(bottom for _, bottom in ratios)
    return tuple(top*(denominator//bottom) for top, bottom in ratios), denominator


def _sqrt_ratio(numerator: int, denominator: int) -> float:
    if numerator == 0:
        return 0.0
    shift = numerator.bit_length()-denominator.bit_length()
    shift -= shift % 2
    if shift < 0:
        scaled = (numerator << -shift)/denominator
    else:
        scaled = numerator/(denominator << shift)
    # Take the square root before applying the scale to preserve small results.
    return math.ldexp(math.sqrt(scaled), shift//2)


def _rolloff(bins: tuple[int, ...], weights: tuple[int, ...],
             total: int, fraction: Fraction) -> int:
    threshold = total*fraction.numerator
    cumulative = 0
    for index, weight in zip(bins, weights):
        cumulative += weight
        if cumulative*fraction.denominator >= threshold:
            return index
    raise ArithmeticError("positive selected power did not reach the rolloff threshold")


def _log_entropy(weights: tuple[int, ...], total: int) -> float:
    """Sum positive entropy contributions before converting to binary64 magnitude."""
    log_total = math.log(total)
    log_terms = []
    for weight in weights:
        if weight == 0 or weight == total:
            continue
        rest = total-weight
        if rest << 52 <= weight:
            # With p this close to 1, the relative correction to rest/weight
            # is of the order of binary64 precision.
            log_terms.append(math.log(rest)-math.log(weight))
        else:
            surprise = (math.log1p(rest/weight) if weight > rest
                        else log_total-math.log(weight))
            log_terms.append(math.log(surprise)-surprise)
    if not log_terms:
        return -math.inf
    largest = max(log_terms)
    return largest+math.log(math.fsum(math.exp(term-largest) for term in log_terms))


def _available(value: float, positive: bool, field: str, underflowed: list[str]) -> float | None:
    if positive and value == 0:
        underflowed.append(field)
        return None
    return value


def _measure(frame: PSDFrame, options: DescriptorOptions) -> _Measurement:
    bins = _select(frame, options)
    if not bins:
        return _Measurement(DescriptorResult(frame, options, bins, "empty_selection", None))
    values = tuple(frame.psd[k] for k in bins)
    weights, scale = _integer_weights(values)
    total = sum(weights)
    if total == 0:
        return _Measurement(DescriptorResult(frame, options, bins, "silent", 0.0), weights)

    fs, nfft = frame.context.sample_rate_hz, frame.context.nfft
    first_moment = sum(k*w for k, w in zip(bins, weights))
    second_moment = sum(k*k*w for k, w in zip(bins, weights))
    # The subtraction is exact in integer arithmetic.
    variance_numerator = second_moment*total-first_moment*first_moment
    underflowed: list[str] = []
    centroid = _available(first_moment*fs/(total*nfft), first_moment > 0,
                          "centroid_hz", underflowed)
    spread = _sqrt_ratio(variance_numerator*fs*fs, (total*nfft)**2)
    crossing = _rolloff(bins, weights, total, options.rolloff_fraction)
    crest = max(weights)*len(bins)/total
    flatness = 0.0
    all_positive = all(values)
    if all_positive:
        log_peak = math.log(max(values))
        log_mean = math.fsum(math.log(value)-log_peak for value in values)/len(values)
        flatness = math.exp(min(0.0, log_mean+math.log(crest)))
    flatness = _available(flatness, all_positive, "flatness", underflowed)

    log_entropy = _log_entropy(weights, total)
    max_entropy = math.log(len(bins))
    positive_entropy = log_entropy != -math.inf
    entropy = _available(min(math.exp(log_entropy), max_entropy), positive_entropy,
                         "entropy_nats", underflowed)
    normalized = None
    if max_entropy > 0:
        normalized = _available(min(1.0, math.exp(log_entropy-math.log(max_entropy))),
                                positive_entropy, "normalized_entropy", underflowed)
    return _Measurement(DescriptorResult(
        frame=frame, options=options, bin_indices=bins, status="ok",
        total_power=total*fs/(scale*nfft), centroid_hz=centroid, spread_hz=spread,
        rolloff_bin=crossing, rolloff_hz=crossing*fs/nfft, flatness=flatness,
        crest=crest, entropy_nats=entropy, normalized_entropy=normalized,
        underflowed=tuple(underflowed),
    ), weights, total)


def measure(frame: PSDFrame, options: DescriptorOptions = DescriptorOptions()) -> DescriptorResult:
    """Calculate one observation without changing any comparison state."""
    _frame(frame)
    _options(options)
    return _measure(frame, options).descriptors


def _flux(current: _Measurement, previous: _Measurement) -> FluxResult:
    a, b = current.descriptors.frame, previous.descriptors.frame
    bins = current.descriptors.bin_indices
    if not bins:
        return FluxResult("empty_selection", b.start_sample)
    density_distance = math.hypot(*(a.psd[k]-b.psd[k] for k in bins))
    power = density_distance*(a.context.sample_rate_hz/a.context.nfft)
    if current.total == 0 or previous.total == 0:
        return FluxResult("silence", b.start_sample, power)
    # Subtract normalized masses before rounding. Uniform represented gain cancels exactly.
    delta_squared = sum((x*previous.total-y*current.total)**2
                        for x, y in zip(current.weights, previous.weights))
    shape = _sqrt_ratio(delta_squared, (current.total*previous.total)**2)
    if delta_squared and shape == 0:
        return FluxResult("shape_underflow", b.start_sample, power)
    return FluxResult("ok", b.start_sample, power, shape)


class DescriptorStream:
    """Compare adjacent frames with the same context and fixed selection."""

    def __init__(self, options: DescriptorOptions = DescriptorOptions()) -> None:
        _options(options)
        self._options = options
        self._previous: _Measurement | None = None

    def reset(self) -> None:
        self._previous = None

    def push(self, frame: PSDFrame) -> Observation:
        _frame(frame)
        previous = self._previous
        if previous is not None:
            prior = previous.descriptors.frame
            if frame.context != prior.context:
                raise ValueError("PSD context changed; reset the stream before comparing")
            if frame.start_sample != prior.start_sample+prior.context.hop_samples:
                raise ValueError("frame does not start at the next expected sample")
        current = _measure(frame, self._options)
        flux = FluxResult("first_frame") if previous is None else _flux(current, previous)
        observation = Observation(current.descriptors, flux)
        self._previous = current
        return observation
