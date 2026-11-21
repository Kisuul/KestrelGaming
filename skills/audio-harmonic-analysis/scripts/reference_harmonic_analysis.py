"""Offline peak measurements and harmonic assignment from a supplied fundamental."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math

MAX_NFFT = 32768
MAX_SAMPLE_RATE = 384000
MAX_FREQUENCY = MAX_SAMPLE_RATE / 2
MAX_SAMPLE_INDEX = (1 << 256) - 1


def _integer(value: int, low: int, high: int, name: str) -> None:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in [{low}, {high}]")


def _nonnegative(value: float, name: str) -> float:
    if type(value) not in (int, float) or value < 0:
        raise ValueError(f"{name} must be finite and nonnegative")
    try:
        number = float(value)
    except OverflowError as error:
        raise ValueError(f"{name} must fit in binary64") from error
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite and nonnegative")
    return number


@dataclass(frozen=True)
class AmplitudeFrame:
    """One original coherent-gain, one-sided peak-amplitude frame."""

    clock_id: str
    epoch_id: str
    source_tap: str
    channel: str
    amplitude_unit: str
    amplitude_reference: str
    window_id: str
    sample_rate_hz: int
    window_samples: int
    nfft: int
    hop_samples: int
    start_sample: int
    amplitudes: tuple[float, ...]
    detrend: str = "none"

    def __post_init__(self) -> None:
        for name in ("clock_id", "epoch_id", "source_tap", "channel",
                     "amplitude_unit", "amplitude_reference", "window_id", "detrend"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip() or len(value) > 128:
                raise ValueError(f"{name} must be a nonblank string of at most 128 characters")
        _integer(self.sample_rate_hz, 2, MAX_SAMPLE_RATE, "sample_rate_hz")
        _integer(self.nfft, 2, MAX_NFFT, "nfft")
        _integer(self.window_samples, 2, self.nfft, "window_samples")
        _integer(self.hop_samples, 1, MAX_NFFT, "hop_samples")
        _integer(self.start_sample, 0, MAX_SAMPLE_INDEX - self.window_samples, "start_sample")
        if not isinstance(self.amplitudes, tuple) or len(self.amplitudes) != self.nfft // 2 + 1:
            raise ValueError("amplitudes must be a tuple with nfft//2+1 bins")
        object.__setattr__(self, "amplitudes",
                           tuple(_nonnegative(value, "amplitude") for value in self.amplitudes))

    @property
    def end_sample_exclusive(self) -> int:
        return self.start_sample + self.window_samples

    @property
    def center_sample_twice(self) -> int:
        return 2 * self.start_sample + self.window_samples - 1

    def bin_frequency_hz(self, index: int) -> float:
        _integer(index, 0, self.nfft // 2, "bin index")
        return index * self.sample_rate_hz / self.nfft


@dataclass(frozen=True)
class SearchBand:
    low_hz: float
    high_hz: float

    def __post_init__(self) -> None:
        low = _nonnegative(self.low_hz, "lower band edge")
        high = _nonnegative(self.high_hz, "upper band edge")
        if not low < high <= MAX_FREQUENCY:
            raise ValueError("band must have positive width within the reference frequency range")
        object.__setattr__(self, "low_hz", low)
        object.__setattr__(self, "high_hz", high)

    def contains(self, frequency: float) -> bool:
        return self.low_hz <= frequency < self.high_hz


@dataclass(frozen=True)
class Peak:
    """A positive-frequency candidate, with measured bin amplitude."""

    bin_index: int
    bin_frequency_hz: float
    bin_amplitude: float
    refinement: str = "bin_center"
    interpolated_hz: float | None = None

    def __post_init__(self) -> None:
        _integer(self.bin_index, 1, MAX_NFFT // 2, "bin index")
        frequency = _nonnegative(self.bin_frequency_hz, "bin center")
        amplitude = _nonnegative(self.bin_amplitude, "peak amplitude")
        if not 0 < frequency <= MAX_FREQUENCY or amplitude == 0:
            raise ValueError("peak requires a positive frequency and amplitude")
        if self.refinement not in ("bin_center", "refined", "missing_flank",
                                   "unpaired_flank", "zero_flank", "invalid_fit"):
            raise ValueError("unknown peak refinement status")
        if (self.refinement == "refined") != (self.interpolated_hz is not None):
            raise ValueError("refined peaks require an interpolated frequency")
        if self.interpolated_hz is not None:
            fitted = _nonnegative(self.interpolated_hz, "interpolated frequency")
            if not 0 < fitted <= MAX_FREQUENCY:
                raise ValueError("interpolated frequency is outside the reference range")
            object.__setattr__(self, "interpolated_hz", fitted)
        object.__setattr__(self, "bin_frequency_hz", frequency)
        object.__setattr__(self, "bin_amplitude", amplitude)

    @property
    def frequency_hz(self) -> float:
        if self.interpolated_hz is None:
            return self.bin_frequency_hz
        return self.interpolated_hz


@dataclass(frozen=True)
class Plateau:
    first_bin: int
    last_bin: int
    bin_amplitude: float


@dataclass(frozen=True)
class PeakSearch:
    frame: AmplitudeFrame
    band: SearchBand
    min_amplitude: float
    peaks: tuple[Peak, ...]
    plateaus: tuple[Plateau, ...]


def _relative_log(neighbor: float, center: float) -> float:
    if neighbor >= center / 2:
        return math.log1p((neighbor - center) / center)
    return math.log(neighbor) - math.log(center)


def _measure_peak(frame: AmplitudeFrame, index: int) -> Peak:
    values = frame.amplitudes
    center = frame.bin_frequency_hz(index)
    amplitude = values[index]
    if index + 1 == len(values):
        return Peak(index, center, amplitude, "missing_flank")
    if index == 1 or index + 1 > (frame.nfft - 1) // 2:
        return Peak(index, center, amplitude, "unpaired_flank")
    left, right = values[index - 1], values[index + 1]
    if left == 0 or right == 0:
        return Peak(index, center, amplitude, "zero_flank")

    u, v = _relative_log(left, amplitude), _relative_log(right, amplitude)
    curvature = u + v
    if not math.isfinite(curvature) or curvature >= 0:
        return Peak(index, center, amplitude, "invalid_fit")
    offset = (u - v) / (2 * curvature)
    if not math.isfinite(offset) or abs(offset) > 0.5:
        return Peak(index, center, amplitude, "invalid_fit")
    fitted = (index + offset) * frame.sample_rate_hz / frame.nfft
    return Peak(index, center, amplitude, "refined", fitted)


def find_peaks(frame: AmplitudeFrame, band: SearchBand, *, min_amplitude: float) -> PeakSearch:
    """Locate positive local maxima and report unresolved plateaus separately."""
    if not isinstance(frame, AmplitudeFrame) or not isinstance(band, SearchBand):
        raise ValueError("peak search requires an AmplitudeFrame and SearchBand")
    if band.high_hz > frame.sample_rate_hz / 2:
        raise ValueError("search band exceeds frame Nyquist")
    floor = _nonnegative(min_amplitude, "amplitude floor")
    values = frame.amplitudes
    peaks, plateaus = [], []
    first = 0
    while first < len(values):
        amplitude = values[first]
        stop = first + 1
        while stop < len(values) and values[stop] == amplitude:
            stop += 1
        if (amplitude > 0 and amplitude >= floor
                and (first == 0 or values[first - 1] < amplitude)
                and (stop == len(values) or values[stop] < amplitude)):
            if stop - first > 1:
                if any(band.contains(frame.bin_frequency_hz(k)) for k in range(max(1, first), stop)):
                    plateaus.append(Plateau(first, stop - 1, amplitude))
            elif first > 0:
                peak = _measure_peak(frame, first)
                if band.contains(peak.frequency_hz):
                    peaks.append(peak)
        first = stop
    return PeakSearch(frame, band, floor, tuple(peaks), tuple(plateaus))


@dataclass(frozen=True)
class HarmonicMatch:
    order: int
    target_hz: float
    status: str
    full_gate: bool
    peak: Peak | None = None
    residual_hz: float | None = None


@dataclass(frozen=True)
class HarmonicAssignment:
    fundamental_hz: float
    tolerance: Fraction
    band: SearchBand
    harmonics: tuple[HarmonicMatch, ...]
    unassigned_peaks: tuple[Peak, ...]

    @property
    def matched_count(self) -> int:
        return sum(result.status == "matched" for result in self.harmonics)

    @property
    def eligible_count(self) -> int:
        return sum(result.status != "out_of_band" for result in self.harmonics)

    @property
    def full_gate_count(self) -> int:
        return sum(result.full_gate for result in self.harmonics)


def assign_harmonics(
    peaks: tuple[Peak, ...],
    band: SearchBand,
    *,
    fundamental_hz: float,
    orders: tuple[int, ...],
    tolerance: Fraction,
) -> HarmonicAssignment:
    """Assign one frame's candidates to inclusive, disjoint harmonic gates."""
    if not isinstance(band, SearchBand) or not isinstance(peaks, tuple):
        raise ValueError("assignment requires a tuple of Peak values and a SearchBand")
    if any(not isinstance(peak, Peak) for peak in peaks):
        raise ValueError("assignment requires measured Peak values")
    if len({peak.bin_index for peak in peaks}) != len(peaks):
        raise ValueError("peak bin indices must be unique")
    fundamental_hz = _nonnegative(fundamental_hz, "fundamental")
    if not 0 < fundamental_hz <= MAX_FREQUENCY:
        raise ValueError("fundamental must be positive and within the reference frequency range")
    if not isinstance(tolerance, Fraction) or not 0 < tolerance < Fraction(1, 2):
        raise ValueError("tolerance must be a Fraction strictly between zero and one half")
    if not isinstance(orders, tuple) or not orders:
        raise ValueError("orders must be a nonempty tuple")
    for order in orders:
        _integer(order, 1, MAX_NFFT, "harmonic order")
    if len(set(orders)) != len(orders):
        raise ValueError("harmonic orders must be unique")

    f0, low, high = Fraction(fundamental_hz), Fraction(band.low_hz), Fraction(band.high_hz)
    width = tolerance * f0
    targets = {order: order * f0 for order in sorted(orders)}
    winners = {}
    for peak in peaks:
        frequency = Fraction(peak.frequency_hz)
        if not low <= frequency < high:
            continue
        # With alpha < 1/2, only the nearest order can contain a peak.
        nearest = int(frequency / f0 + Fraction(1, 2))
        target = targets.get(nearest)
        if target is None or not low <= target < high:
            continue
        residual = frequency - target
        if abs(residual) > width:
            continue
        rank = (abs(residual), -peak.bin_amplitude, frequency, peak.bin_index)
        if nearest not in winners or rank < winners[nearest][0]:
            winners[nearest] = rank, peak, residual

    harmonics = []
    assigned_bins = set()
    for order, target in targets.items():
        if not low <= target < high:
            harmonics.append(HarmonicMatch(order, float(target), "out_of_band", False))
            continue
        full_gate = low <= target - width and target + width < high
        winner = winners.get(order)
        if winner is None:
            status = "missing" if full_gate else "partial_band"
            harmonics.append(HarmonicMatch(order, float(target), status, full_gate))
        else:
            _, peak, residual = winner
            assigned_bins.add(peak.bin_index)
            harmonics.append(HarmonicMatch(order, float(target), "matched", full_gate,
                                           peak, float(residual)))
    unassigned = tuple(sorted((peak for peak in peaks if peak.bin_index not in assigned_bins),
                              key=lambda peak: peak.bin_index))
    return HarmonicAssignment(fundamental_hz, tolerance, band, tuple(harmonics), unassigned)
