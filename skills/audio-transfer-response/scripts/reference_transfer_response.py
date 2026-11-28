"""H1 and H2 transfer estimates on the accepted paired Welch products."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import inf, ldexp, log10, sqrt, ulp
import sys
from typing import Literal

from reference_group_delay import Scalar, TransferProvenance, WelchQuality, _exact
from reference_phase_coherence import PhaseCoherenceAnalysis, PhaseCoherenceBin


_MIN_MAGNITUDE_SQUARED = Fraction(ulp(0.0)) ** 2
_MAX_MAGNITUDE_SQUARED = Fraction(sys.float_info.max) ** 2
TransferStatus = Literal[
    "unexcited", "zero_output", "zero_cross", "weak_reference", "weak_output",
    "insufficient_energized_pairs", "low_coherence", "weak_cross", "qualified",
]


@dataclass(frozen=True)
class TransferQuality(WelchQuality):
    """Qualify the paired levels and the separate H2 denominator."""

    minimum_energized_pairs: int = 2
    cross_density_floor: Scalar = 0

    def __post_init__(self) -> None:
        super().__post_init__()
        if type(self.minimum_energized_pairs) is not int or self.minimum_energized_pairs < 1:
            raise ValueError("minimum energized pairs must be a positive integer")
        cross = _exact(self.cross_density_floor, "cross density floor")
        if cross < 0:
            raise ValueError("cross density floor must be nonnegative")
        object.__setattr__(self, "cross_density_floor", cross)


def _scaled_power(power: Fraction) -> tuple[float, int]:
    exponent = (power.numerator.bit_length() - power.denominator.bit_length()) // 2
    return float(power / Fraction(2) ** (2 * exponent)), exponent


@dataclass(frozen=True)
class TransferEstimate:
    real: Fraction
    imag: Fraction

    @property
    def magnitude_squared(self) -> Fraction:
        return self.real**2 + self.imag**2

    @property
    def magnitude(self) -> float | None:
        power = self.magnitude_squared
        if power == 0:
            return 0.0
        if not _MIN_MAGNITUDE_SQUARED <= power <= _MAX_MAGNITUDE_SQUARED:
            return None
        mantissa, exponent = _scaled_power(power)
        try:
            return ldexp(sqrt(mantissa), exponent)
        except OverflowError:
            # At the upper boundary, rounding the scaled mantissa can reach the next power of two.
            return sys.float_info.max

    @property
    def magnitude_db(self) -> float:
        power = self.magnitude_squared
        if power == 0:
            return -inf
        mantissa, exponent = _scaled_power(power)
        return 10 * (log10(mantissa) + 2 * exponent * log10(2))


@dataclass(frozen=True)
class TransferBin:
    spectra: PhaseCoherenceBin
    h1: TransferEstimate | None
    h2: TransferEstimate | None
    h1_status: TransferStatus
    h2_status: TransferStatus


@dataclass(frozen=True)
class TransferResponse:
    paired: PhaseCoherenceAnalysis
    quality: TransferQuality
    reference_units: str
    measurement_units: str
    provenance: TransferProvenance | None
    output_advance_samples: Fraction
    bins: tuple[TransferBin, ...]

    @property
    def warming_up(self) -> bool:
        return self.paired.warming_up


def _qualification(point: PhaseCoherenceBin, cross_power: Fraction, quality: TransferQuality) -> TransferStatus:
    if point.reference_density == 0:
        return "unexcited"
    if point.measurement_density == 0:
        return "zero_output"
    if cross_power == 0:
        return "zero_cross"
    if point.reference_density < quality.reference_density_floor:
        return "weak_reference"
    if point.measurement_density < quality.measurement_density_floor:
        return "weak_output"
    if point.energized_pairs < quality.minimum_energized_pairs:
        return "insufficient_energized_pairs"
    if point.magnitude_squared_coherence < quality.minimum_coherence:
        return "low_coherence"
    return "qualified"


def _measure(point: PhaseCoherenceBin, quality: TransferQuality) -> TransferBin:
    px, py = point.reference_density, point.measurement_density
    cr, ci = point.cross_density_real, point.cross_density_imag
    cross_power = cr**2 + ci**2
    h1 = TransferEstimate(cr / px, ci / px) if px else None
    # H2 divides by the conjugate of C, so its phase has the sign of C.
    h2 = TransferEstimate(py * cr / cross_power, py * ci / cross_power) if cross_power else None
    status = _qualification(point, cross_power, quality)
    h2_status = "weak_cross" if status == "qualified" and cross_power < quality.cross_density_floor**2 else status
    return TransferBin(point, h1, h2, status, h2_status)


def analyze_transfer_response(
    analysis: PhaseCoherenceAnalysis, *, quality: TransferQuality = TransferQuality(),
    reference_units: str | None = None, measurement_units: str | None = None,
    provenance: TransferProvenance | None = None, output_advance_samples: Scalar = 0,
) -> TransferResponse:
    """Retain aligned Welch support and estimate a single reference-to-response path."""
    if type(analysis) is not PhaseCoherenceAnalysis or type(quality) is not TransferQuality:
        raise ValueError("provide paired Welch analysis and TransferQuality")
    epoch = analysis.epoch
    input_units = epoch.units if reference_units is None else reference_units
    output_units = epoch.units if measurement_units is None else measurement_units
    if any(type(unit) is not str or not unit.strip() for unit in (input_units, output_units)):
        raise ValueError("reference and measurement units must be nonempty labels")
    if provenance is not None and (
        type(provenance) is not TransferProvenance
        or (provenance.clock_domain, provenance.epoch_id) != (epoch.clock_domain, epoch.epoch_id)
    ):
        raise ValueError("original tap support must use the paired clock domain and epoch")
    advance = _exact(output_advance_samples, "output advance in samples")
    return TransferResponse(
        analysis, quality, input_units, output_units,
        provenance, advance, tuple(_measure(point, quality) for point in analysis.bins),
    )
