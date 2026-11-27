"""Bounded frame-wise pitch-class folding and major/minor triad evidence."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import floor
from typing import Literal, Optional, Sequence

from reference_oscilloscope import _check_integer, _is_label
from reference_pitch_tracking import Scalar, _scalar
from reference_tuning_analysis import TuningResult, TuningSupport, _octave_and_cents


MAX_FFT_LENGTH = 8192
MAX_POWER_POINTS = MAX_FFT_LENGTH // 2 + 1
_ZERO = Fraction()
_HALF = Fraction(1, 2)
_TRIADS = {"maj": (0, 4, 7), "min": (0, 3, 7)}
Status = Literal[
    "input_unavailable", "tuning_unavailable", "tuning_out_of_scope", "insufficient_power",
    "poor_fit", "ambiguous", "unanchored", "matched",
]


@dataclass(frozen=True)
class PowerPoint:
    frequency_hz: Scalar
    power: Scalar

    def __post_init__(self) -> None:
        frequency = _scalar(self.frequency_hz, "point frequency")
        power = _scalar(self.power, "point power")
        if frequency < 0 or power < 0:
            raise ValueError("point frequency and power must be nonnegative")
        object.__setattr__(self, "frequency_hz", frequency)
        object.__setattr__(self, "power", power)


@dataclass(frozen=True)
class PowerFrame:
    support: TuningSupport
    power_units: str
    points: tuple[PowerPoint, ...] = ()
    fft_length: Optional[int] = None

    def __post_init__(self) -> None:
        if type(self.support) is not TuningSupport or not _is_label(self.power_units):
            raise ValueError("supply sample-clock support and declared power units")
        if type(self.points) is not tuple or len(self.points) > MAX_POWER_POINTS:
            raise ValueError("supply a bounded tuple of power points")
        if self.points and self.support.ready_sample_exclusive is None:
            raise ValueError("point power requires complete, ready input")
        nyquist = self.support.epoch.rate_hz / 2
        if any(type(p) is not PowerPoint or p.frequency_hz > nyquist for p in self.points):
            raise ValueError("provide power points from DC through the epoch's Nyquist")
        if self.fft_length is not None:
            spacing = _bin_spacing(self.support, self.fft_length)
            if len(self.points) != self.fft_length // 2 + 1 or any(
                p.frequency_hz != k * spacing for k, p in enumerate(self.points)
            ):
                raise ValueError("one-sided PSD points must cover the complete bin grid")


def _bin_spacing(support: TuningSupport, fft_length: int) -> Fraction:
    if type(support) is not TuningSupport or support.ready_sample_exclusive is None:
        raise ValueError("PSD bins require complete, ready input")
    length = support.end_sample_exclusive - support.start_sample
    _check_integer(fft_length, "transform length", max(2, length), MAX_FFT_LENGTH)
    return support.epoch.rate_hz / fft_length


def power_frame_from_psd(
    density: Sequence[Scalar], *, fft_length: int, support: TuningSupport, power_units: str,
) -> PowerFrame:
    """Convert an already calibrated one-sided PSD to full-bin power masses."""
    spacing = _bin_spacing(support, fft_length)
    if type(density) not in (list, tuple) or len(density) != fft_length // 2 + 1:
        raise ValueError("supply one PSD ordinate at every one-sided bin")
    points = tuple(PowerPoint(k * spacing, _scalar(value, "PSD density") * spacing)
                   for k, value in enumerate(density))
    return PowerFrame(support, power_units, points, fft_length)


@dataclass(frozen=True)
class ChromaGrid:
    reference_a4_hz: Scalar = 440
    tuning: Optional[TuningResult] = None
    semitone_lift: Optional[int] = None

    def __post_init__(self) -> None:
        reference = _scalar(self.reference_a4_hz, "A4 reference")
        if reference <= 0:
            raise ValueError("A4 reference must be positive")
        if self.tuning is not None and (
            type(self.tuning) is not TuningResult or self.tuning.profile.reference_a4_hz != reference
        ):
            raise ValueError("use the A4 reference that produced the tuning estimate")
        if self.semitone_lift is not None and (
            type(self.semitone_lift) is not int or self.tuning is None or self.tuning.status != "estimated"
        ):
            raise ValueError("a semitone lift requires a supported tuning estimate and an integer")
        object.__setattr__(self, "reference_a4_hz", reference)

    @classmethod
    def from_tuning(cls, tuning: TuningResult, *, semitone_lift: Optional[int] = None) -> ChromaGrid:
        if type(tuning) is not TuningResult:
            raise ValueError("provide a TuningResult")
        return cls(tuning.profile.reference_a4_hz, tuning, semitone_lift)

    @property
    def correction_cents(self) -> Optional[Fraction]:
        if self.tuning is None:
            return _ZERO
        if self.tuning.status != "estimated":
            return None
        return Fraction(self.tuning.offset_cents) + 100 * (self.semitone_lift or 0)

    @property
    def has_absolute_labels(self) -> bool:
        return self.tuning is None or self.semitone_lift is not None


@dataclass(frozen=True)
class ChromaProfile:
    minimum_hz: Scalar = 0
    maximum_hz: Optional[Scalar] = None
    minimum_point_power: Scalar = 0
    minimum_admitted_power: Scalar = 0
    minimum_class_share: Scalar = 0
    minimum_score_squared: Scalar = 0
    ambiguity_margin_squared: Scalar = 0
    bass_tolerance_cents: Scalar = 25

    def __post_init__(self) -> None:
        for field in (
            "minimum_hz", "minimum_point_power", "minimum_admitted_power", "minimum_class_share",
            "minimum_score_squared", "ambiguity_margin_squared", "bass_tolerance_cents",
        ):
            value = _scalar(getattr(self, field), field)
            if value < 0:
                raise ValueError(f"{field} must be nonnegative")
            object.__setattr__(self, field, value)
        if self.maximum_hz is not None:
            high = _scalar(self.maximum_hz, "maximum frequency")
            if high <= 0 or high < self.minimum_hz:
                raise ValueError("frequency bounds must be ordered with a positive upper bound")
            object.__setattr__(self, "maximum_hz", high)
        if max(self.minimum_class_share, self.minimum_score_squared, self.ambiguity_margin_squared) > 1:
            raise ValueError("class share, score, and score margin limits must be in [0, 1]")
        if self.bass_tolerance_cents >= 50:
            raise ValueError("bass tolerance must be below half a semitone")


@dataclass(frozen=True)
class BassObservation:
    frequency_hz: Scalar
    support: TuningSupport

    def __post_init__(self) -> None:
        frequency = _scalar(self.frequency_hz, "bass frequency")
        if type(self.support) is not TuningSupport or self.support.ready_sample_exclusive is None:
            raise ValueError("bass evidence requires complete, ready sample support")
        if not 0 < frequency <= self.support.epoch.rate_hz / 2:
            raise ValueError("bass frequency must be positive and at or below Nyquist")
        object.__setattr__(self, "frequency_hz", frequency)


@dataclass(frozen=True)
class PitchSplit:
    pitch: Fraction
    lower_class: int
    lower_power: Fraction
    upper_class: int
    upper_power: Fraction


@dataclass(frozen=True)
class ChromaAssignment:
    point: PowerPoint
    calibrated_frequency_hz: Fraction
    split: PitchSplit


@dataclass(frozen=True)
class PowerTotals:
    dc: Fraction
    outside_band: Fraction
    below_point_floor: Fraction
    admitted: Fraction

    @property
    def in_band(self) -> Fraction:
        return self.below_point_floor + self.admitted

    @property
    def input_total(self) -> Fraction:
        return self.dc + self.outside_band + self.in_band


@dataclass(frozen=True)
class TriadScore:
    root: int
    quality: Literal["maj", "min"]
    score_squared: Fraction

    @property
    def classes(self) -> tuple[int, ...]:
        return tuple((self.root + step) % 12 for step in _TRIADS[self.quality])


@dataclass(frozen=True)
class ChromaResult:
    frame: PowerFrame
    grid: ChromaGrid
    profile: ChromaProfile
    status: Status
    bass: Optional[BassObservation] = None
    totals: Optional[PowerTotals] = None
    raw_chroma: Optional[tuple[Fraction, ...]] = None
    assignments: tuple[ChromaAssignment, ...] = ()
    occupied_classes: tuple[int, ...] = ()
    ranking: tuple[TriadScore, ...] = ()
    bass_class: Optional[int] = None
    bass_error_cents: Optional[Fraction] = None
    ready_sample_exclusive: Optional[int] = None
    evidence_release_sample_exclusive: Optional[int] = None

    @property
    def margin_squared(self) -> Optional[Fraction]:
        if self.ranking:
            return self.ranking[0].score_squared - self.ranking[1].score_squared
        return None

    @property
    def competitors(self) -> tuple[TriadScore, ...]:
        if not self.ranking:
            return ()
        limit = self.ranking[0].score_squared - self.profile.ambiguity_margin_squared
        return tuple(row for row in self.ranking if row.score_squared >= limit)

    @property
    def selected(self) -> Optional[TriadScore]:
        return self.ranking[0] if self.status == "matched" else None

    @property
    def inversion(self) -> Optional[int]:
        chord = self.selected
        if chord is not None and self.bass_class in chord.classes:
            return chord.classes.index(self.bass_class)
        return None


def split_pitch(pitch: Scalar, power: Scalar) -> PitchSplit:
    """Split a supplied pitch coordinate between adjacent cyclic classes."""
    position = _scalar(pitch, "pitch")
    mass = _scalar(power, "pitch power")
    if mass < 0:
        raise ValueError("pitch power must be nonnegative")
    lower = floor(position)
    upper_power = mass * (position - lower)
    return PitchSplit(position, lower % 12, mass - upper_power, (lower + 1) % 12, upper_power)


def score_triads(chroma: Sequence[Scalar]) -> tuple[TriadScore, ...]:
    """Rank all 24 templates by exact squared cosine on represented masses."""
    if type(chroma) not in (tuple, list) or len(chroma) != 12:
        raise ValueError("provide twelve pitch-class masses")
    masses = tuple(_scalar(value, "pitch-class power") for value in chroma)
    if min(masses) < 0:
        raise ValueError("pitch-class masses must be nonnegative")
    denominator = 3 * sum(mass**2 for mass in masses)
    if not denominator:
        return ()
    scores = []
    for quality, steps in _TRIADS.items():
        for root in range(12):
            projection = sum(masses[(root + step) % 12] for step in steps)
            scores.append(TriadScore(root, quality, projection**2 / denominator))
    return tuple(sorted(scores, key=lambda row: (-row.score_squared, row.root, row.quality)))


def _pitch(frequency: Fraction, reference: Fraction, correction: Fraction) -> Fraction:
    octave, cents = _octave_and_cents(frequency / reference)
    return 69 + 12 * octave + (Fraction(cents) - correction) / 100


def _fold_frame(
    frame: PowerFrame, profile: ChromaProfile, reference: Fraction, correction: Fraction, factor: Fraction,
) -> tuple[PowerTotals, tuple[Fraction, ...], tuple[ChromaAssignment, ...]]:
    dc = outside = below = admitted = _ZERO
    masses = [_ZERO] * 12
    assignments = []
    for point in frame.points:
        power = point.power
        frequency = point.frequency_hz * factor
        if frequency == 0:
            dc += power
        elif (frequency < profile.minimum_hz
              or (profile.maximum_hz is not None and frequency > profile.maximum_hz)):
            outside += power
        elif power < profile.minimum_point_power:
            below += power
        elif power:
            split = split_pitch(_pitch(frequency, reference, correction), power)
            masses[split.lower_class] += split.lower_power
            masses[split.upper_class] += split.upper_power
            admitted += power
            assignments.append(ChromaAssignment(point, frequency, split))
    return PowerTotals(dc, outside, below, admitted), tuple(masses), tuple(assignments)


def _qualification(ranking: tuple[TriadScore, ...], profile: ChromaProfile, grid: ChromaGrid) -> Status:
    if not ranking:
        return "insufficient_power"
    best, runner_up = ranking[:2]
    if best.score_squared < profile.minimum_score_squared:
        return "poor_fit"
    if best.score_squared - runner_up.score_squared <= profile.ambiguity_margin_squared:
        return "ambiguous"
    return "matched" if grid.has_absolute_labels else "unanchored"


def analyze_chroma(
    frame: PowerFrame, grid: ChromaGrid = ChromaGrid(), profile: ChromaProfile = ChromaProfile(), *,
    bass: Optional[BassObservation] = None,
) -> ChromaResult:
    """Fold available frame evidence and qualify a bounded triad decision."""
    if type(frame) is not PowerFrame or type(grid) is not ChromaGrid or type(profile) is not ChromaProfile:
        raise ValueError("supply a PowerFrame, ChromaGrid, and ChromaProfile")
    if bass is not None and type(bass) is not BassObservation:
        raise ValueError("supply a BassObservation")
    support = frame.support
    if support.ready_sample_exclusive is None:
        return ChromaResult(frame, grid, profile, "input_unavailable", bass)
    correction = grid.correction_cents
    if correction is None:
        return ChromaResult(frame, grid, profile, "tuning_unavailable", bass)

    dependencies = [(support.ready_sample_exclusive, support.observed_release_sample_exclusive)]
    coverage = grid.tuning.coverage if grid.tuning is not None else None
    factor = Fraction(1)
    if coverage is not None:
        if (coverage.epoch != support.epoch or support.start_sample < coverage.start_sample
                or support.end_sample_exclusive > coverage.available_end_sample_exclusive):
            return ChromaResult(frame, grid, profile, "tuning_out_of_scope", bass)
        factor = grid.tuning.clock_factor
        dependencies.append((coverage.evidence_ready_sample_exclusive, coverage.evidence_release_sample_exclusive))

    totals, raw, assignments = _fold_frame(frame, profile, grid.reference_a4_hz, correction, factor)
    class_floor = profile.minimum_class_share * totals.admitted
    occupied = tuple(k for k, mass in enumerate(raw) if mass > 0 and mass >= class_floor)
    ranking = score_triads(raw) if totals.admitted >= profile.minimum_admitted_power else ()
    status = _qualification(ranking, profile, grid)
    bass_class = bass_error = None
    center = support.center_sample_twice
    if bass is not None and bass.support.epoch == support.epoch and (
        2 * bass.support.start_sample <= center < 2 * bass.support.end_sample_exclusive
    ):
        coordinate = _pitch(bass.frequency_hz * factor, grid.reference_a4_hz, correction)
        nearest = floor(coordinate + _HALF)
        bass_error = 100 * (coordinate - nearest)
        if abs(bass_error) <= profile.bass_tolerance_cents:
            bass_class = nearest % 12
        dependencies.append((bass.support.ready_sample_exclusive, bass.support.observed_release_sample_exclusive))

    ready = max(first for first, _ in dependencies)
    releases = tuple(observed for _, observed in dependencies)
    released = max(releases) if all(value is not None for value in releases) else None
    return ChromaResult(
        frame, grid, profile, status, bass, totals, raw, assignments, occupied, ranking,
        bass_class, bass_error, ready, released,
    )
