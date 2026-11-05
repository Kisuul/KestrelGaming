"""Calibrations and analytic ballistics for a bounded VU-inspired meter.

Educational model only: a full-wave *mean-rectified* detector followed by an
exact sampled second-order underdamped needle model. The moving-coil and
rectifier in IEC 60268-17:1990 have further performance requirements which
are NOT certified by this small Python oracle. Not RMS, PPM, or LUFS.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math

MAX_CHANNELS = 8
MAX_BLOCK_FRAMES = 32768
VU_RISE_SECONDS = 0.3
VU_OVERSHOOT_FRACTION = 0.0125  # design choice inside usual 1..1.5% target band


def _finite(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite real number")
    try:
        result = float(value)
    except (OverflowError, ValueError) as exc:
        raise ValueError(f"{name} is not representable") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _index(value: int, name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")


@dataclass(frozen=True)
class ToneCalibration:
    """Input scalar units and the peak amplitude of a 1 kHz 0-VU test tone.

    Digital dBFS is defined as a sine *peak* fraction of |PCM|=1. This is
    NOT a general RMS-dBFS/AES17 convention or a claim of digital clipping.
    """
    reference_sine_peak: float
    input_unit: str
    reference_label: str

    def __post_init__(self) -> None:
        value = _finite(self.reference_sine_peak, "reference_sine_peak")
        if value <= 0:
            raise ValueError("reference_sine_peak must be positive")
        if not isinstance(self.input_unit, str) or not self.input_unit.strip():
            raise ValueError("input_unit is required")
        if not isinstance(self.reference_label, str) or not self.reference_label.strip():
            raise ValueError("reference_label is required")
        object.__setattr__(self, "reference_sine_peak", value)

    @classmethod
    def digital_tone_dbfs_peak(cls, dbfs_peak: float = -20.0) -> ToneCalibration:
        """0 VU = an explicitly chosen sine *peak* dBFS alignment level."""
        db = _finite(dbfs_peak, "dbfs_peak")
        if db > 0:
            raise ValueError("digital alignment sine peak must be <= 0 dBFS-peak")
        peak = 10.0 ** (db / 20.0)
        if not math.isfinite(peak) or peak == 0:
            raise ValueError("requested digital reference is outside binary64 range")
        return cls(peak, "unit-normalized float PCM", f"{db:g} dBFS-peak alignment sine")

    @classmethod
    def analog_tone_dbu(cls, dbu: float = 4.0) -> ToneCalibration:
        """0 VU = a chosen analog sine's dBu voltage; source values in volts."""
        db = _finite(dbu, "dbu")
        try:
            vrms = 0.775 * (10.0 ** (db / 20.0))
            peak = vrms * math.sqrt(2.0)
        except OverflowError as exc:
            raise ValueError("requested voltage reference is outside binary64 range") from exc
        if not math.isfinite(peak) or peak == 0:
            raise ValueError("requested voltage reference is outside binary64 range")
        return cls(peak, "volts", f"{db:g} dBu RMS voltage alignment sine")


def damping_ratio_for_overshoot(overshoot: float = VU_OVERSHOOT_FRACTION) -> float:
    """Inverse of exp(-pi*zeta/sqrt(1-zeta^2))."""
    v = _finite(overshoot, "overshoot")
    if not 0 < v < 1:
        raise ValueError("overshoot must lie strictly between zero and one")
    logarithm = -math.log(v)
    return logarithm / math.hypot(math.pi, logarithm)


def _unit_step(x: float, zeta: float) -> float:
    """Analytic second-order step, dimensionless time omega_n*t."""
    damped = math.sqrt(1.0 - zeta*zeta)
    return 1.0 - math.exp(-zeta*x) * (
        math.cos(damped*x) + (zeta/damped)*math.sin(damped*x))


def _omega_n_for_rise(zeta: float, rise_seconds: float) -> float:
    """Solve first crossing of 99% in rise_seconds, *not* time constant."""
    hi = math.pi / math.sqrt(1.0-zeta*zeta)
    lo = 0.0
    for _ in range(70):
        middle = (lo+hi)*0.5
        if _unit_step(middle, zeta) >= 0.99:
            hi = middle
        else:
            lo = middle
    return 0.5*(hi+lo)/rise_seconds


def expected_unit_step(seconds: float) -> float:
    """Independent continuous envelope check, not sampled input tone data."""
    t = _finite(seconds, "seconds")
    if t < 0:
        raise ValueError("negative time")
    zeta = damping_ratio_for_overshoot()
    omega = _omega_n_for_rise(zeta, VU_RISE_SECONDS)
    return _unit_step(omega*t, zeta)


