"""Bounded offline THD and THD+N reference for coherent captures."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import frexp, inf, isfinite, ldexp, log10, sqrt
from typing import Literal, Optional, Union

from reference_oscilloscope import CaptureWindow, PCMSample, ScopeEpoch
from reference_psd import MAX_REFERENCE_NFFT, periodogram


MAX_HARMONIC_ORDERS = 64
Exact = Union[int, Fraction]
Power = Union[int, float, Fraction]
HarmonicStatus = Literal["admitted", "out_of_band", "above_nyquist"]
FundamentalStatus = Literal["qualified", "out_of_band", "zero_power", "below_floor"]


@dataclass(frozen=True)
class ThdProfile:
    """Declare the known bin, harmonic orders, and admitted measurement band."""

    fundamental_bin: int
    harmonic_orders: tuple[int, ...] = tuple(range(2, 25))
    band_hz: Optional[tuple[Exact, Exact]] = None
    include_dc: bool = False
    minimum_fundamental_power: Power = 0

    def __post_init__(self) -> None:
        if type(self.fundamental_bin) is not int or self.fundamental_bin < 1:
            raise ValueError("fundamental_bin must be a positive integer")
        orders = self.harmonic_orders
        if type(orders) is not tuple or len(orders) > MAX_HARMONIC_ORDERS:
            raise ValueError(f"provide a tuple of up to {MAX_HARMONIC_ORDERS} harmonic orders")
        if any(type(order) is not int or order < 2 for order in orders):
            raise ValueError("harmonic orders must be integers >= 2")
        if len(orders) != len(set(orders)):
            raise ValueError("harmonic orders must be distinct")
        object.__setattr__(self, "harmonic_orders", tuple(sorted(orders)))
        if self.band_hz is not None:
            band = self.band_hz
            if type(band) is not tuple or len(band) != 2:
                raise ValueError("provide a pair of band endpoints")
            if any(type(endpoint) not in (int, Fraction) for endpoint in band):
                raise ValueError("band endpoints must be integers or Fractions")
            lower, upper = map(Fraction, band)
            if not 0 <= lower <= upper:
                raise ValueError("band endpoints must be nonnegative and ordered")
            object.__setattr__(self, "band_hz", (lower, upper))
        if type(self.include_dc) is not bool:
            raise ValueError("include_dc must be a bool")
        floor = self.minimum_fundamental_power
        if type(floor) not in (int, float, Fraction) or (
            type(floor) is float and not isfinite(floor)
        ) or floor < 0:
            raise ValueError("minimum_fundamental_power must be finite and nonnegative")
        object.__setattr__(self, "minimum_fundamental_power", Fraction(floor))


@dataclass(frozen=True)
class PowerBin:
    index: int
    frequency_hz: Fraction
    power: Fraction
    admitted: bool


@dataclass(frozen=True)
class HarmonicOrder:
    order: int
    nominal_bin: int
    nominal_frequency_hz: Fraction
    status: HarmonicStatus
    admitted_power: Optional[Fraction]
    possible_fold_bin: Optional[int] = None


@dataclass(frozen=True)
class Ratio:
    linear: float
    decibels: float

    @property
    def percent(self) -> float:
        return 100 * self.linear


@dataclass(frozen=True)
class ThdReport:
    epoch: ScopeEpoch
    channel_id: str
    start_sample: int
    end_sample_exclusive: int
    profile: ThdProfile
    band_hz: tuple[Fraction, Fraction]
    bin_width_hz: Fraction
    bins: tuple[PowerBin, ...]
    harmonics: tuple[HarmonicOrder, ...]
    fundamental_status: FundamentalStatus
    fundamental_power: Fraction
    distortion_power: Fraction
    residual_power: Fraction
    band_power: Fraction
    thd: Optional[Ratio]
    thdn_fundamental: Optional[Ratio]
    thdn_total: Optional[Ratio]


def _bin_powers(samples: tuple[PCMSample, ...]) -> tuple[Fraction, ...]:
    """Use a unit bin width in the PSD call, then restore PCM units."""
    size = len(samples)
    _, exponent = frexp(max(map(abs, samples)))
    normalized = [ldexp(value, -exponent) for value in samples]
    _, density = periodogram(normalized, [1.0] * size, float(size), detrend_mean=True)
    scale = Fraction(2) ** (2 * exponent)
    mean = sum(map(Fraction, samples), Fraction(0)) / size
    return (mean**2,) + tuple(Fraction(value) * scale for value in density[1:])


def _harmonic_orders(
    profile: ThdProfile, bins: tuple[PowerBin, ...], size: int, width: Fraction
) -> tuple[HarmonicOrder, ...]:
    harmonics = []
    for order in profile.harmonic_orders:
        nominal = order * profile.fundamental_bin
        frequency = nominal * width
        if 2 * nominal > size:
            remainder = nominal % size
            fold = min(remainder, size - remainder)
            harmonics.append(HarmonicOrder(order, nominal, frequency, "above_nyquist", None, fold))
        else:
            entry = bins[nominal]
            status = "admitted" if entry.admitted else "out_of_band"
            power = entry.power if entry.admitted else None
            harmonics.append(HarmonicOrder(order, nominal, frequency, status, power))
    return tuple(harmonics)


def _ratio(numerator: Fraction, denominator: Fraction) -> Ratio:
    if numerator == 0:
        return Ratio(0.0, -inf)
    power_ratio = numerator / denominator
    # Scale before float conversion so a small power ratio retains its square root.
    exponent = (power_ratio.numerator.bit_length() - power_ratio.denominator.bit_length()) // 2
    mantissa = float(power_ratio / Fraction(2) ** (2 * exponent))
    return Ratio(
        ldexp(sqrt(mantissa), exponent),
        10 * (log10(mantissa) + 2 * exponent * log10(2)),
    )


def measure_thd_thdn(
    capture: CaptureWindow, profile: ThdProfile, *, channel_id: Optional[str] = None
) -> ThdReport:
    """Measure one channel using the rectangular, unpadded capture grid."""
    if type(capture) is not CaptureWindow or type(profile) is not ThdProfile:
        raise ValueError("provide a CaptureWindow and a ThdProfile")
    channels = capture.epoch.channel_ids
    if channel_id is None and len(channels) == 1:
        channel_id = channels[0]
    if type(channel_id) is not str or channel_id not in channels:
        raise ValueError("select a declared channel")
    size = capture.frame_count
    fundamental = profile.fundamental_bin
    if size > MAX_REFERENCE_NFFT or 2 * fundamental >= size:
        raise ValueError("the capture must fit the PSD reference and have an interior fundamental")
    rate = capture.epoch.rate_hz
    nyquist = rate / 2
    width = rate / size
    lower, upper = profile.band_hz if profile.band_hz is not None else (Fraction(0), nyquist)
    if upper > nyquist:
        raise ValueError("band upper endpoint exceeds Nyquist")

    entries = []
    for index, power in enumerate(_bin_powers(capture.planes[channels.index(channel_id)])):
        frequency = index * width
        admitted = lower <= frequency <= upper and (index > 0 or profile.include_dc)
        entries.append(PowerBin(index, frequency, power, admitted))
    bins = tuple(entries)
    harmonics = _harmonic_orders(profile, bins, size, width)
    fundamental_power = bins[fundamental].power
    distortion_power = sum(
        (entry.admitted_power for entry in harmonics if entry.admitted_power is not None), Fraction(0)
    )
    residual_power = sum(
        (entry.power for entry in bins if entry.admitted and entry.index != fundamental), Fraction(0)
    )
    band_power = sum((entry.power for entry in bins if entry.admitted), Fraction(0))

    status: FundamentalStatus
    if not bins[fundamental].admitted:
        status = "out_of_band"
    elif fundamental_power == 0:
        status = "zero_power"
    elif fundamental_power < profile.minimum_fundamental_power:
        status = "below_floor"
    else:
        status = "qualified"
    qualified = status == "qualified"
    return ThdReport(
        epoch=capture.epoch, channel_id=channel_id,
        start_sample=capture.start_sample, end_sample_exclusive=capture.end_sample_exclusive,
        profile=profile, band_hz=(lower, upper), bin_width_hz=width,
        bins=bins, harmonics=harmonics, fundamental_status=status,
        fundamental_power=fundamental_power, distortion_power=distortion_power,
        residual_power=residual_power, band_power=band_power,
        thd=_ratio(distortion_power, fundamental_power) if qualified else None,
        thdn_fundamental=_ratio(residual_power, fundamental_power) if qualified else None,
        thdn_total=_ratio(residual_power, band_power) if qualified else None,
    )
