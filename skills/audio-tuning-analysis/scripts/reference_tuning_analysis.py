"""Bounded offline 12-TET tuning estimates over qualified pitch observations."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction
from math import atan2, cos, fsum, hypot, isfinite, log, log1p, remainder, sin, tau
from typing import Literal, Optional, Sequence

from reference_oscilloscope import MAX_SAMPLE_INDEX, ScopeEpoch, _check_integer, _is_label
from reference_pitch_tracking import PitchFrame, Scalar, _scalar


MAX_OBSERVATIONS = 4096
NUMERICAL_RESULTANT_FLOOR = 1e-12
_CENTS_PER_NEPER = 1200 / log(2)
_ZERO = Fraction()
_ONE = Fraction(1)
Weighting = Literal["note", "observation"]
ObservationStatus = Literal[
    "qualified", "excluded", "unavailable", "silence", "dc_only", "below_floor", "unvoiced",
]
TuningStatus = Literal["unavailable", "ambiguous", "estimated"]
TuningReason = Literal["no_eligible_weight", "insufficient_notes", "zero_resultant", "below_concentration"]


@dataclass(frozen=True)
class TuningProfile:
    reference_a4_hz: Scalar = 440
    weighting: Weighting = "note"
    minimum_concentration: Scalar = 0
    minimum_notes: int = 0

    def __post_init__(self) -> None:
        reference = _scalar(self.reference_a4_hz, "A4 reference")
        concentration = _scalar(self.minimum_concentration, "minimum concentration")
        if reference <= 0 or not 0 <= concentration <= 1:
            raise ValueError("use a positive A4 reference and a concentration floor in [0, 1]")
        if self.weighting not in ("note", "observation"):
            raise ValueError("choose note or observation weighting")
        _check_integer(self.minimum_notes, "minimum notes", 0, MAX_OBSERVATIONS)
        object.__setattr__(self, "reference_a4_hz", reference)
        object.__setattr__(self, "minimum_concentration", concentration)


@dataclass(frozen=True)
class TuningSupport:
    epoch: ScopeEpoch
    start_sample: int
    end_sample_exclusive: int
    available_end_sample_exclusive: int
    ready_sample_exclusive: Optional[int]
    observed_release_sample_exclusive: Optional[int] = None

    def __post_init__(self) -> None:
        if type(self.epoch) is not ScopeEpoch:
            raise ValueError("support requires a sample-clock epoch")
        _check_integer(self.start_sample, "support start", self.epoch.origin_sample, MAX_SAMPLE_INDEX - 1)
        _check_integer(self.end_sample_exclusive, "support end", self.start_sample + 1, MAX_SAMPLE_INDEX)
        present = self.available_end_sample_exclusive
        _check_integer(present, "available end", self.start_sample, self.end_sample_exclusive)
        ready = self.ready_sample_exclusive
        if ready is not None:
            if present != self.end_sample_exclusive:
                raise ValueError("pitch support must be complete at readiness")
            _check_integer(ready, "ready boundary", present, MAX_SAMPLE_INDEX)
        if self.observed_release_sample_exclusive is not None:
            earliest = present if ready is None else ready
            _check_integer(self.observed_release_sample_exclusive, "observed release", earliest, MAX_SAMPLE_INDEX)

    @property
    def center_sample_twice(self) -> int:
        return self.start_sample + self.end_sample_exclusive - 1


@dataclass(frozen=True)
class TuningObservation:
    frequency_hz: Optional[Scalar]
    note_id: Optional[str] = None
    known_midi_note: Optional[int] = None
    weight: Scalar = 1
    status: ObservationStatus = "qualified"
    support: Optional[TuningSupport] = None

    def __post_init__(self) -> None:
        if self.status not in ("qualified", "excluded", "unavailable", "silence", "dc_only", "below_floor", "unvoiced"):
            raise ValueError("use a declared pitch observation state")
        weight = _scalar(self.weight, "weight")
        if weight < 0:
            raise ValueError("weight must be nonnegative")
        object.__setattr__(self, "weight", weight)
        if self.note_id is not None and not _is_label(self.note_id):
            raise ValueError("supply a nonempty note event ID")
        if self.known_midi_note is not None:
            _check_integer(self.known_midi_note, "known MIDI note", 0, 127)
        if self.support is not None and type(self.support) is not TuningSupport:
            raise ValueError("supply a TuningSupport record")
        if self.frequency_hz is None:
            if self.status == "qualified":
                raise ValueError("a qualified observation requires a frequency")
            return
        frequency = _scalar(self.frequency_hz, "observed frequency")
        if frequency <= 0 or self.status not in ("qualified", "excluded"):
            raise ValueError("retain a positive frequency on a qualified or excluded observation")
        if self.support is not None and self.support.ready_sample_exclusive is None:
            raise ValueError("a measured frequency requires ready support")
        object.__setattr__(self, "frequency_hz", frequency)


@dataclass(frozen=True)
class TuningEvidence:
    observation: TuningObservation
    calibrated_frequency_hz: Optional[Fraction]
    residue_cents: Optional[float]
    known_note_error_cents: Optional[float]
    effective_weight: Fraction


@dataclass(frozen=True)
class TuningCoverage:
    epoch: ScopeEpoch
    start_sample: int
    end_sample_exclusive: int
    available_end_sample_exclusive: int
    evidence_ready_sample_exclusive: Optional[int]
    evidence_release_sample_exclusive: Optional[int]


@dataclass(frozen=True)
class TuningResult:
    profile: TuningProfile
    status: TuningStatus
    reason: Optional[TuningReason]
    evidence: tuple[TuningEvidence, ...]
    coverage: Optional[TuningCoverage]
    calibrated_rate_hz: Optional[Fraction]
    clock_factor: Fraction
    eligible_count: int
    note_count: int
    eligible_weight: Fraction
    effective_weight: Fraction
    resultant: Optional[complex]
    concentration: Optional[float]
    offset_cents: Optional[float]

    @property
    def representative_a4_hz(self) -> Optional[Fraction]:
        if self.offset_cents is None:
            return None
        return self.profile.reference_a4_hz * Fraction(2.0**(self.offset_cents / 1200))


def wrap_cents(cents: float) -> float:
    """Map finite binary64 cents to the half-open semitone interval."""
    if not isfinite(cents):
        raise ValueError("cents must be finite")
    folded = remainder(cents, 100.0)
    return -50.0 if folded == 50.0 else folded


def observation_from_pitch(
    frame: PitchFrame, *, note_id: Optional[str] = None, known_midi_note: Optional[int] = None,
    weight: Scalar = 1,
) -> TuningObservation:
    """Keep the selected pitch, voicing state, and original frame support."""
    if type(frame) is not PitchFrame:
        raise ValueError("supply a PitchFrame")
    support = TuningSupport(
        frame.grid.epoch, frame.start_sample, frame.end_sample_exclusive,
        frame.available_end_sample_exclusive, frame.ready_sample_exclusive,
        frame.observed_release_sample_exclusive,
    )
    return TuningObservation(
        frame.selected.frequency_hz if frame.selected is not None else None,
        note_id, known_midi_note, weight, "qualified" if frame.status == "voiced" else frame.status, support,
    )


def _octave_and_cents(ratio: Fraction) -> tuple[int, float]:
    # Scale the rational ratio before conversion. This keeps the log argument
    # well conditioned near 1 and avoids overflow for extreme frequency scales.
    numerator, denominator = ratio.numerator, ratio.denominator
    octave = numerator.bit_length() - denominator.bit_length()
    if octave >= 0:
        denominator <<= octave
    else:
        numerator <<= -octave
    if 4 * numerator < 3 * denominator:
        numerator *= 2
        octave -= 1
    elif 2 * numerator >= 3 * denominator:
        denominator *= 2
        octave += 1
    delta = Fraction(numerator - denominator, denominator)
    return octave, _CENTS_PER_NEPER * log1p(float(delta))


def _evidence(
    row: TuningObservation, target_hz: Fraction, clock_factor: Fraction, weight: Fraction,
) -> TuningEvidence:
    if row.frequency_hz is None:
        return TuningEvidence(row, None, None, None, weight)
    calibrated = row.frequency_hz * clock_factor
    octave, cents = _octave_and_cents(calibrated / target_hz)
    error = None
    if row.known_midi_note is not None:
        error = 100 * (12 * octave + 69 - row.known_midi_note) + cents
    return TuningEvidence(row, calibrated, wrap_cents(cents), error, weight)


def _coverage(
    spans: tuple[TuningSupport, ...], contributing: tuple[TuningEvidence, ...],
) -> TuningCoverage:
    contributing_spans = [item.observation.support for item in contributing]
    ready = max((span.ready_sample_exclusive for span in contributing_spans), default=None)
    releases = [span.observed_release_sample_exclusive for span in contributing_spans]
    return TuningCoverage(
        spans[0].epoch, min(span.start_sample for span in spans),
        max(span.end_sample_exclusive for span in spans),
        max(span.available_end_sample_exclusive for span in spans),
        ready, max(releases) if releases and all(end is not None for end in releases) else None,
    )


def _resultant(
    contributions: tuple[TuningEvidence, ...], total: Fraction,
) -> tuple[complex, float, Optional[float]]:
    angles = [tau * (item.residue_cents / 100.0) for item in contributions]
    weights = [float(item.effective_weight / total) for item in contributions]
    real = fsum(weight * cos(angle) for weight, angle in zip(weights, angles))
    imaginary = fsum(weight * sin(angle) for weight, angle in zip(weights, angles))
    first = contributions[0].residue_cents
    if all(item.residue_cents == first for item in contributions):
        return complex(real, imaginary), 1.0, first
    magnitude = min(1.0, hypot(real, imaginary))
    offset = wrap_cents(atan2(imaginary, real) / tau * 100.0) if magnitude > NUMERICAL_RESULTANT_FLOOR else None
    return complex(real, imaginary), magnitude, offset


def estimate_tuning(
    observations: Sequence[TuningObservation], profile: TuningProfile = TuningProfile(), *,
    actual_rate_hz: Optional[Scalar] = None,
) -> TuningResult:
    """Aggregate one timed epoch or one untimed set of observations."""
    if type(profile) is not TuningProfile:
        raise ValueError("supply a TuningProfile")
    if type(observations) not in (tuple, list) or len(observations) > MAX_OBSERVATIONS:
        raise ValueError("supply a bounded tuple or list of tuning observations")
    rows = tuple(observations)
    if any(type(row) is not TuningObservation for row in rows):
        raise ValueError("supply TuningObservation records")
    spans = tuple(row.support for row in rows if row.support is not None)
    if spans and (len(spans) != len(rows) or any(span.epoch != spans[0].epoch for span in spans)):
        raise ValueError("an estimate requires one epoch or exclusively untimed observations")
    actual = None
    clock_factor = _ONE
    if actual_rate_hz is not None:
        actual = _scalar(actual_rate_hz, "actual sample rate")
        if actual <= 0 or not spans:
            raise ValueError("rate correction requires a positive rate and a timed epoch")
        clock_factor = actual / spans[0].epoch.rate_hz

    note_totals = defaultdict(Fraction)
    raw_weights = [row.weight if row.status == "qualified" else _ZERO for row in rows]
    for row, weight in zip(rows, raw_weights):
        if weight and row.note_id is not None:
            note_totals[row.note_id] += weight
    weights = raw_weights
    if profile.weighting == "note":
        if any(weight and row.note_id is None for row, weight in zip(rows, raw_weights)):
            raise ValueError("note weighting requires an event ID on every positive eligible observation")
        weights = [weight / note_totals[row.note_id] if weight else _ZERO
                   for row, weight in zip(rows, raw_weights)]

    evidence = tuple(_evidence(row, profile.reference_a4_hz, clock_factor, weight)
                     for row, weight in zip(rows, weights))
    contributing = tuple(item for item in evidence if item.effective_weight)
    coverage = _coverage(spans, contributing) if spans else None
    total = sum(weights, _ZERO)
    vector = concentration = offset = None
    status = "unavailable"
    reason = "no_eligible_weight"
    if contributing:
        vector, concentration, offset = _resultant(contributing, total)
        if len(note_totals) < profile.minimum_notes:
            reason = "insufficient_notes"
        elif offset is None:
            status, reason = "ambiguous", "zero_resultant"
        elif concentration < profile.minimum_concentration:
            status, reason = "ambiguous", "below_concentration"
        else:
            status, reason = "estimated", None
    return TuningResult(
        profile, status, reason, evidence, coverage, actual, clock_factor,
        len(contributing), len(note_totals), sum(raw_weights, _ZERO), total,
        vector, concentration, offset if status == "estimated" else None,
    )
