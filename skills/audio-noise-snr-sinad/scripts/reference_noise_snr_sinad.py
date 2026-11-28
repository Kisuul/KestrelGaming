"""Bounded quiet-input noise, driven SNR, and full-residual SINAD."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import inf, isfinite, log10
from typing import Literal, Optional, Union

from reference_oscilloscope import CaptureWindow, ScopeEpoch
from reference_psd import MAX_REFERENCE_NFFT
from reference_thd_thdn import (
    Exact, FundamentalStatus, HarmonicOrder, Power, PowerBin, ThdProfile,
    _bin_powers, measure_thd_thdn,
)


BinRole = Literal["excluded", "signal", "harmonic", "snr_excluded_spur", "noise"]
SignalStatus = Union[Literal["no_stimulus"], FundamentalStatus]


@dataclass(frozen=True)
class NoiseBin(PowerBin):
    role: BinRole


@dataclass(frozen=True)
class NoiseReport:
    epoch: ScopeEpoch
    channel_id: str
    start_sample: int
    end_sample_exclusive: int
    band_hz: tuple[Fraction, Fraction]
    bin_width_hz: Fraction
    include_dc: bool
    bins: tuple[NoiseBin, ...]
    profile: Optional[ThdProfile]
    harmonics: tuple[HarmonicOrder, ...]
    snr_excluded_bins: tuple[int, ...]
    signal_status: SignalStatus
    signal_power: Optional[Fraction]
    distortion_power: Fraction
    excluded_spur_power: Fraction
    noise_power: Fraction
    residual_power: Fraction
    band_power: Fraction
    snr_db: Optional[float]
    sinad_db: Optional[float]

    def noise_level_db(self, reference_power: Power) -> float:
        """Express the noise term relative to a declared positive power in the same units."""
        if (type(reference_power) not in (int, float, Fraction)
                or (type(reference_power) is float and not isfinite(reference_power))
                or reference_power <= 0):
            raise ValueError("provide a finite positive reference power in squared PCM units")
        return _decibels(self.noise_power, Fraction(reference_power))


def _decibels(numerator: Fraction, denominator: Fraction) -> float:
    if numerator == 0:
        return -inf
    if denominator == 0:
        return inf
    ratio = numerator / denominator
    # Scale before conversion to keep the mantissa finite across the PCM power range.
    exponent = ratio.numerator.bit_length() - ratio.denominator.bit_length()
    mantissa = float(ratio / Fraction(2) ** exponent)
    return 10 * (log10(mantissa) + exponent * log10(2))


def _quiet_band(
    requested: Optional[tuple[Exact, Exact]], nyquist: Fraction,
) -> tuple[Fraction, Fraction]:
    if requested is None:
        return Fraction(0), nyquist
    if type(requested) is not tuple or len(requested) != 2:
        raise ValueError("provide a pair of band endpoints")
    if any(type(endpoint) not in (int, Fraction) for endpoint in requested):
        raise ValueError("band endpoints must be integers or Fractions")
    lower, upper = map(Fraction, requested)
    if not 0 <= lower <= upper <= nyquist:
        raise ValueError("band endpoints must be ordered and between zero and Nyquist")
    return lower, upper


def measure_quiet_noise(
    capture: CaptureWindow, *, channel_id: Optional[str] = None,
    band_hz: Optional[tuple[Exact, Exact]] = None, include_dc: bool = False,
) -> NoiseReport:
    """Measure all admitted power in one channel of a quiet-input capture."""
    if type(capture) is not CaptureWindow:
        raise ValueError("provide a CaptureWindow")
    channels = capture.epoch.channel_ids
    if channel_id is None and len(channels) == 1:
        channel_id = channels[0]
    if type(channel_id) is not str or channel_id not in channels:
        raise ValueError("select a declared channel")
    size = capture.frame_count
    if not 2 <= size <= MAX_REFERENCE_NFFT:
        raise ValueError("capture length must fit the PSD reference")
    if type(include_dc) is not bool:
        raise ValueError("include_dc must be a bool")
    rate = capture.epoch.rate_hz
    band = _quiet_band(band_hz, rate / 2)
    width = rate / size
    bins = []
    for index, power in enumerate(_bin_powers(capture.planes[channels.index(channel_id)])):
        frequency = index * width
        admitted = band[0] <= frequency <= band[1] and (index > 0 or include_dc)
        bins.append(NoiseBin(index, frequency, power, admitted, "noise" if admitted else "excluded"))
    noise = sum((entry.power for entry in bins if entry.admitted), Fraction(0))
    return NoiseReport(
        epoch=capture.epoch, channel_id=channel_id,
        start_sample=capture.start_sample, end_sample_exclusive=capture.end_sample_exclusive,
        band_hz=band, bin_width_hz=width, include_dc=include_dc, bins=tuple(bins),
        profile=None, harmonics=(), snr_excluded_bins=(),
        signal_status="no_stimulus", signal_power=None, distortion_power=Fraction(0),
        excluded_spur_power=Fraction(0), noise_power=noise, residual_power=noise,
        band_power=noise, snr_db=None, sinad_db=None,
    )


def _driven_bins(
    bins: tuple[PowerBin, ...], signal_bin: int, harmonics: set[int], spurs: set[int],
) -> tuple[NoiseBin, ...]:
    entries = []
    for entry in bins:
        role: BinRole
        if not entry.admitted:
            role = "excluded"
        elif entry.index == signal_bin:
            role = "signal"
        elif entry.index in harmonics:
            role = "harmonic"
        elif entry.index in spurs:
            role = "snr_excluded_spur"
        else:
            role = "noise"
        entries.append(NoiseBin(entry.index, entry.frequency_hz, entry.power, entry.admitted, role))
    return tuple(entries)


def measure_driven_noise(
    capture: CaptureWindow, profile: ThdProfile, *, channel_id: Optional[str] = None,
    snr_excluded_bins: tuple[int, ...] = (),
) -> NoiseReport:
    """Measure noise and full residual with a declared coherent fundamental."""
    thd = measure_thd_thdn(capture, profile, channel_id=channel_id)
    last_bin = len(thd.bins) - 1
    if (type(snr_excluded_bins) is not tuple or len(snr_excluded_bins) > last_bin
            or any(type(index) is not int or not 1 <= index <= last_bin for index in snr_excluded_bins)):
        raise ValueError("SNR exclusions must be a tuple of positive bins on the capture grid")
    spurs = set(snr_excluded_bins)
    if len(spurs) != len(snr_excluded_bins):
        raise ValueError("SNR exclusion bins must be distinct")
    fundamental = profile.fundamental_bin
    harmonics = {entry.nominal_bin for entry in thd.harmonics if entry.status != "above_nyquist"}
    if fundamental in spurs or harmonics & spurs:
        raise ValueError("SNR exclusions cannot include the fundamental or a declared harmonic")

    bins = _driven_bins(thd.bins, fundamental, harmonics, spurs)
    noise = sum((entry.power for entry in bins if entry.role == "noise"), Fraction(0))
    excluded = sum((entry.power for entry in bins if entry.role == "snr_excluded_spur"), Fraction(0))
    snr_db = _decibels(thd.fundamental_power, noise) if thd.fundamental_status == "qualified" else None
    sinad_db = None if thd.thdn_fundamental is None else -thd.thdn_fundamental.decibels
    return NoiseReport(
        epoch=thd.epoch, channel_id=thd.channel_id,
        start_sample=thd.start_sample, end_sample_exclusive=thd.end_sample_exclusive,
        band_hz=thd.band_hz, bin_width_hz=thd.bin_width_hz, include_dc=profile.include_dc,
        bins=bins, profile=profile, harmonics=thd.harmonics, snr_excluded_bins=tuple(sorted(spurs)),
        signal_status=thd.fundamental_status, signal_power=thd.fundamental_power,
        distortion_power=thd.distortion_power, excluded_spur_power=excluded, noise_power=noise,
        residual_power=thd.residual_power, band_power=thd.band_power, snr_db=snr_db, sinad_db=sinad_db,
    )
