"""Bounded coherent two-tone measurements with explicit product assignments."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, replace
from fractions import Fraction
import math
import sys
from typing import Literal, Optional, Union

from reference_oscilloscope import CaptureWindow, PCMSample, ScopeEpoch
from reference_psd import MAX_REFERENCE_NFFT, periodogram


Exact = Union[int, Fraction]
Power = Union[int, float, Fraction]
Coefficients = tuple[int, int]
SamplingPolicy = Literal["digital_fold", "band_limited"]
CarrierReference = Literal["low_carrier", "high_carrier", "both_carriers"]
LineStatus = Literal[
    "resolved", "collision", "above_nyquist", "out_of_band", "excluded_endpoint",
    "zero_power", "below_floor",
]

# One representative of each conjugate pair through third order.
_CANDIDATES = (
    (0, 0), (1, 0), (0, 1),
    (2, 0), (0, 2), (1, 1), (1, -1),
    (3, 0), (0, 3), (2, 1), (2, -1), (1, 2), (1, -2),
)
_MAX_PEAK_SQUARED = Fraction(sys.float_info.max) ** 2


def _order(coefficients: Coefficients) -> int:
    low, high = coefficients
    return abs(low) + abs(high)


def _canonical(coefficients: Coefficients) -> Coefficients:
    low, high = coefficients
    return (-low, -high) if coefficients < (0, 0) else coefficients


@dataclass(frozen=True)
class ImdProfile:
    """Declare the numerator, carrier reference, and candidate family."""

    carrier_bins: tuple[int, int]
    products: tuple[Coefficients, ...]
    sampling_policy: SamplingPolicy
    ratio_reference: CarrierReference
    max_order: int = 3
    band_hz: Optional[tuple[Exact, Exact]] = None
    include_dc: bool = False
    include_nyquist: bool = True
    minimum_carrier_power: Power = 0

    def __post_init__(self) -> None:
        bins = self.carrier_bins
        if (type(bins) is not tuple or len(bins) != 2
                or any(type(index) is not int for index in bins)
                or not 0 < bins[0] < bins[1]):
            raise ValueError("carrier bins must be ascending positive integers")
        if type(self.max_order) is not int or self.max_order not in (2, 3):
            raise ValueError("max_order must be two or three")
        if type(self.sampling_policy) is not str or self.sampling_policy not in (
            "digital_fold", "band_limited",
        ):
            raise ValueError("select a sampling policy")
        if type(self.ratio_reference) is not str or self.ratio_reference not in (
            "low_carrier", "high_carrier", "both_carriers",
        ):
            raise ValueError("select a carrier reference")
        if type(self.products) is not tuple or not 1 <= len(self.products) <= 6:
            raise ValueError("provide a tuple of one to six mixed products")
        for product in self.products:
            if (type(product) is not tuple or len(product) != 2
                    or any(type(coefficient) is not int or coefficient == 0 for coefficient in product)
                    or _order(product) > self.max_order):
                raise ValueError("product must be a mixed integer pair in the declared order range")
        if len({_canonical(product) for product in self.products}) != len(self.products):
            raise ValueError("requested products must be distinct up to conjugation")
        if self.band_hz is not None:
            band = self.band_hz
            if type(band) is not tuple or len(band) != 2:
                raise ValueError("provide a pair of band endpoints")
            if any(type(endpoint) not in (int, Fraction) for endpoint in band):
                raise ValueError("band endpoints must use exact Hz")
            lower, upper = map(Fraction, band)
            if not 0 <= lower <= upper:
                raise ValueError("band endpoints must be nonnegative and ordered")
            object.__setattr__(self, "band_hz", (lower, upper))
        if type(self.include_dc) is not bool or type(self.include_nyquist) is not bool:
            raise ValueError("endpoint admission flags must be bools")
        floor = self.minimum_carrier_power
        if (type(floor) not in (int, float, Fraction)
                or (type(floor) is float and not math.isfinite(floor)) or floor < 0):
            raise ValueError("minimum_carrier_power must be finite and nonnegative")
        object.__setattr__(self, "minimum_carrier_power", Fraction(floor))


def _scaled_power(power: Fraction) -> tuple[float, int]:
    """Keep a positive mantissa near one before converting power to binary64."""
    exponent = (power.numerator.bit_length() - power.denominator.bit_length()) // 2
    return float(power / Fraction(2) ** (2 * exponent)), exponent


@dataclass(frozen=True)
class PowerBin:
    index: int
    frequency_hz: Fraction
    power: Fraction
    paired: bool
    admitted: bool
    candidates: tuple[Coefficients, ...]

    @property
    def peak_amplitude(self) -> Optional[float]:
        """Return the peak in PCM units when it is in the finite binary64 range."""
        squared = self.power * (2 if self.paired else 1)
        if squared == 0:
            return 0.0
        if squared > _MAX_PEAK_SQUARED:
            return None
        mantissa, exponent = _scaled_power(squared)
        # Rounding the scaled mantissa can reach the next power of two.
        try:
            return math.ldexp(math.sqrt(mantissa), exponent)
        except OverflowError:
            return sys.float_info.max


@dataclass(frozen=True)
class Ratio:
    linear: float
    decibels: float

    @property
    def percent(self) -> float:
        return 100 * self.linear


def _ratio(power: Fraction, reference: Fraction) -> Ratio:
    if power == 0:
        return Ratio(0.0, -math.inf)
    mantissa, exponent = _scaled_power(power / reference)
    return Ratio(
        math.ldexp(math.sqrt(mantissa), exponent),
        10 * (math.log10(mantissa) + 2 * exponent * math.log10(2)),
    )


@dataclass(frozen=True)
class LineMeasurement:
    coefficients: Coefficients
    nominal_bin: int
    nominal_frequency_hz: Fraction
    possible_fold_bin: Optional[int]
    observed_bin: Optional[PowerBin]
    status: LineStatus
    ratio: Optional[Ratio] = None

    @property
    def order(self) -> int:
        return _order(self.coefficients)


@dataclass(frozen=True)
class ImdReport:
    epoch: ScopeEpoch
    channel_id: str
    start_sample: int
    end_sample_exclusive: int
    profile: ImdProfile
    band_hz: tuple[Fraction, Fraction]
    bin_width_hz: Fraction
    bins: tuple[PowerBin, ...]
    carriers: tuple[LineMeasurement, LineMeasurement]
    products: tuple[LineMeasurement, ...]
    reference_power: Optional[Fraction]
    aggregate_power: Optional[Fraction]
    aggregate_ratio: Optional[Ratio]


@dataclass(frozen=True)
class _Location:
    nominal_bin: int
    observed_index: Optional[int]
    possible_fold_bin: Optional[int]


def _locate(coefficients: Coefficients, profile: ImdProfile, size: int) -> _Location:
    low, high = profile.carrier_bins
    m, n = coefficients
    nominal = m * low + n * high
    if 2 * abs(nominal) <= size:
        return _Location(nominal, abs(nominal), None)
    remainder = nominal % size
    fold = min(remainder, size - remainder)
    return _Location(nominal, fold if profile.sampling_policy == "digital_fold" else None, fold)


def _coherent_powers(samples: tuple[PCMSample, ...]) -> tuple[Fraction, ...]:
    """Obtain unit-bin-width powers from the calibrated rectangular PSD."""
    size = len(samples)
    _, exponent = math.frexp(max(map(abs, samples)))
    normalized = [math.ldexp(value, -exponent) for value in samples]
    _, density = periodogram(normalized, [1.0] * size, float(size), detrend_mean=True)
    restore = Fraction(2) ** (2 * exponent)
    mean = sum(map(Fraction, samples), Fraction(0)) / size
    return (mean**2,) + tuple(Fraction(power) * restore for power in density[1:])


def _measure_bins(
    samples: tuple[PCMSample, ...], profile: ImdProfile, width: Fraction,
    band: tuple[Fraction, Fraction],
) -> tuple[PowerBin, ...]:
    size = len(samples)
    groups = defaultdict(list)
    for candidate in _CANDIDATES:
        if _order(candidate) <= profile.max_order:
            index = _locate(candidate, profile, size).observed_index
            if index is not None:
                groups[index].append(candidate)
    lower, upper = band
    bins = []
    for index, power in enumerate(_coherent_powers(samples)):
        frequency = index * width
        nyquist = 2 * index == size
        enabled = (index != 0 or profile.include_dc) and (not nyquist or profile.include_nyquist)
        bins.append(PowerBin(
            index, frequency, power, index != 0 and not nyquist,
            lower <= frequency <= upper and enabled, tuple(groups.get(index, ())),
        ))
    return tuple(bins)


def _line(
    coefficients: Coefficients, profile: ImdProfile, bins: tuple[PowerBin, ...],
    size: int, width: Fraction, band: tuple[Fraction, Fraction],
) -> LineMeasurement:
    location = _locate(coefficients, profile, size)
    index = location.observed_index
    observed = None if index is None else bins[index]
    status: LineStatus
    if observed is None:
        status = "above_nyquist"
    elif len(observed.candidates) > 1:
        status = "collision"
    elif not band[0] <= observed.frequency_hz <= band[1]:
        status = "out_of_band"
    elif not observed.admitted:
        status = "excluded_endpoint"
    else:
        status = "resolved"
    return LineMeasurement(
        coefficients, location.nominal_bin, location.nominal_bin * width,
        location.possible_fold_bin, observed, status,
    )


def _qualify_carrier(line: LineMeasurement, floor: Fraction) -> LineMeasurement:
    if line.status == "resolved":
        power = line.observed_bin.power
        if power == 0:
            return replace(line, status="zero_power")
        if power < floor:
            return replace(line, status="below_floor")
    return line


def _reference_power(
    carriers: tuple[LineMeasurement, LineMeasurement], reference: CarrierReference,
) -> Optional[Fraction]:
    low, high = carriers
    if low.status != "resolved" or high.status != "resolved":
        return None
    low_power, high_power = low.observed_bin.power, high.observed_bin.power
    return {
        "low_carrier": low_power, "high_carrier": high_power, "both_carriers": low_power + high_power,
    }[reference]


def measure_intermodulation(
    capture: CaptureWindow, profile: ImdProfile, *, channel_id: str,
) -> ImdReport:
    """Measure a declared line group on one coherent rectangular capture."""
    if type(capture) is not CaptureWindow or type(profile) is not ImdProfile:
        raise ValueError("provide a CaptureWindow and an ImdProfile")
    channels = capture.epoch.channel_ids
    if type(channel_id) is not str or channel_id not in channels:
        raise ValueError("select a declared channel")
    size = capture.frame_count
    if size > MAX_REFERENCE_NFFT or 2 * profile.carrier_bins[1] >= size:
        raise ValueError("carriers must be interior in a capture within the PSD reference limit")
    rate = capture.epoch.rate_hz
    nyquist = rate / 2
    width = rate / size
    band = profile.band_hz if profile.band_hz is not None else (Fraction(0), nyquist)
    if band[1] > nyquist:
        raise ValueError("band upper endpoint exceeds Nyquist")

    bins = _measure_bins(capture.planes[channels.index(channel_id)], profile, width, band)
    low = _qualify_carrier(_line((1, 0), profile, bins, size, width, band), profile.minimum_carrier_power)
    high = _qualify_carrier(_line((0, 1), profile, bins, size, width, band), profile.minimum_carrier_power)
    carriers = (low, high)
    reference = _reference_power(carriers, profile.ratio_reference)
    products = tuple(_line(pair, profile, bins, size, width, band) for pair in profile.products)
    if reference is not None:
        products = tuple(
            replace(line, ratio=_ratio(line.observed_bin.power, reference))
            if line.status == "resolved" else line for line in products
        )

    # Every resolved product owns one unique bin after candidate grouping.
    aggregate = None
    if all(line.status == "resolved" for line in products):
        aggregate = sum((line.observed_bin.power for line in products), Fraction(0))
    return ImdReport(
        capture.epoch, channel_id, capture.start_sample, capture.end_sample_exclusive,
        profile, band, width, bins, carriers, products, reference, aggregate,
        _ratio(aggregate, reference) if aggregate is not None and reference is not None else None,
    )
