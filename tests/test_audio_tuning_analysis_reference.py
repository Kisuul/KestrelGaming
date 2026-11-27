"""Tuning, note weighting, and sample-clock checks for the offline reference."""

from dataclasses import replace
from fractions import Fraction
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
for skill in ("audio-oscilloscope", "audio-pitch-tracking", "audio-tuning-analysis"):
    sys.path.insert(0, str(ROOT / "skills" / skill / "scripts"))

from reference_oscilloscope import MAX_SAMPLE_INDEX, ScopeEpoch
from reference_pitch_tracking import PitchGrid, PitchProfile, PitchTracker, measure_pitch
from reference_tuning_analysis import (
    MAX_OBSERVATIONS, TuningObservation, TuningProfile, TuningSupport, estimate_tuning,
    observation_from_pitch, wrap_cents,
)


ORIGIN = 2**60 + 37
EPOCH = ScopeEpoch("fixture", ORIGIN, Fraction(48000), "capture clock", "input", "FS", ("mono",))
BY_OBSERVATION = TuningProfile(weighting="observation")


def detuned(cents, note_id=None, *, weight=1, known_midi_note=None):
    return TuningObservation(440 * 2**(cents / 1200), note_id, known_midi_note, weight)


class PitchCoordinateTests(unittest.TestCase):
    def test_a442_vs_two_declared_references(self):
        rows = tuple(TuningObservation(442 * 2**((note - 69) / 12), str(note), note)
                     for note in (60, 64, 69, 72))
        default = estimate_tuning(rows)
        actual = estimate_tuning(rows, TuningProfile(442))
        self.assertEqual((default.status, default.note_count, default.eligible_count), ("estimated", 4, 4))
        self.assertAlmostEqual(default.concentration, 1.0, delta=2e-15)
        self.assertAlmostEqual(default.offset_cents, 7.8514150401265, delta=5e-12)
        self.assertAlmostEqual(float(default.representative_a4_hz), 442, delta=1e-11)
        self.assertAlmostEqual(actual.offset_cents, 0, delta=5e-12)
        for evidence in default.evidence:
            self.assertAlmostEqual(evidence.known_note_error_cents, 7.8514150401265, delta=5e-12)

    def test_known_note_error_remains_unwrapped(self):
        rows = [detuned(55, "A4", known_midi_note=69),
                TuningObservation(880, "octave high", 69),
                TuningObservation(220, "octave low", 69)]
        high, octave_high, octave_low = estimate_tuning(rows).evidence
        self.assertAlmostEqual(high.residue_cents, -45, delta=5e-12)
        self.assertAlmostEqual(high.known_note_error_cents, 55, delta=5e-12)
        self.assertAlmostEqual(high.known_note_error_cents - high.residue_cents, 100, delta=5e-12)
        self.assertEqual((octave_high.residue_cents, octave_high.known_note_error_cents), (0, 1200))
        self.assertEqual((octave_low.residue_cents, octave_low.known_note_error_cents), (0, -1200))

    def test_exact_seam_and_adjacent_binary64_values(self):
        higher = math.nextafter(50, math.inf)
        lower = math.nextafter(50, -math.inf)
        self.assertEqual([wrap_cents(v) for v in (50, -50, 150, -150)], [-50] * 4)
        self.assertEqual(wrap_cents(lower), lower)
        self.assertEqual(wrap_cents(higher), math.nextafter(-50, math.inf))
        self.assertEqual(wrap_cents(math.nextafter(-50, -math.inf)), lower)
        self.assertEqual(wrap_cents(math.nextafter(-50, math.inf)), math.nextafter(-50, math.inf))
        with self.assertRaises(ValueError):
            wrap_cents(math.nan)

    def test_scale_and_octave_invariance_with_exact_frequency_ratios(self):
        hertz = Fraction(123456789, 313371)
        row = TuningObservation(hertz, "note")
        original = estimate_tuning([row])
        for scale in (Fraction(7, 5), Fraction(2)**-1000, Fraction(2)**1000):
            with self.subTest(scale=scale):
                scaled = estimate_tuning([replace(row, frequency_hz=hertz * scale)],
                                         TuningProfile(440 * scale))
                self.assertEqual(scaled.offset_cents, original.offset_cents)
                moved = estimate_tuning([replace(row, frequency_hz=hertz * 2**40)])
                self.assertEqual(moved.offset_cents, original.offset_cents)

    def test_nearly_exact_octave_preserves_small_signed_error(self):
        few_ulp = [math.nextafter(880, -math.inf), math.nextafter(880, math.inf)]
        rows = [TuningObservation(x, str(i), 81) for i, x in enumerate(few_ulp)]
        for row, evidence in zip(rows, estimate_tuning(rows).evidence):
            fractional_difference = float((row.frequency_hz - 880) / 880)
            expected = 1200 * math.log1p(fractional_difference) / math.log(2)
            self.assertAlmostEqual(evidence.known_note_error_cents, expected, delta=1e-26)

    def test_frequency_ratio_beyond_binary64_range(self):
        smallest, largest = math.ldexp(1.0, -1074), sys.float_info.max
        factor = Fraction(largest) / Fraction(smallest)
        wrapped = wrap_cents(1200 * (math.log2(largest) - math.log2(smallest)))
        for hz, reference, expected in ((largest, smallest, wrapped), (smallest, largest, -wrapped)):
            with self.subTest(hz=hz):
                row = TuningObservation(hz, "extreme")
                result = estimate_tuning([row], TuningProfile(reference))
                self.assertEqual(result.evidence[0].calibrated_frequency_hz, Fraction(hz))
                self.assertAlmostEqual(wrap_cents(result.offset_cents - expected), 0, delta=5e-10)
        nontrivial = estimate_tuning([TuningObservation(math.ldexp(1.5, 1023), "large")],
                                     TuningProfile(smallest))
        self.assertAlmostEqual(nontrivial.offset_cents, 1.9550008653874, delta=1e-12)
        self.assertGreater(factor, largest)

    def test_harmonic_preprocessing_changes_the_observable(self):
        partials = [TuningObservation(440 * h, "same note") for h in (2, 3, 5)]
        pooled = estimate_tuning(partials)
        corrected = estimate_tuning([replace(row, frequency_hz=row.frequency_hz / h)
                                     for h, row in zip((2, 3, 5), partials)])
        residues = [row.residue_cents for row in pooled.evidence]
        for estimate, expected in zip(residues, (0, 1.9550008653874, -13.6862861351652)):
            self.assertAlmostEqual(estimate, expected, delta=1e-10)
        self.assertAlmostEqual(pooled.offset_cents, -3.751567470961, delta=1e-10)
        self.assertAlmostEqual(pooled.concentration, 0.9067243980513, delta=1e-10)
        self.assertEqual((corrected.offset_cents, corrected.note_count), (0, 1))


class WeightAndDirectionTests(unittest.TestCase):
    def test_seam_mean_and_opposing_observations(self):
        seam = estimate_tuning([detuned(c, str(c)) for c in (49, -49)])
        self.assertAlmostEqual(wrap_cents(seam.offset_cents + 50), 0, delta=5e-12)
        self.assertAlmostEqual(seam.concentration, 0.998026728428, delta=5e-12)
        opposite = estimate_tuning([detuned(c, str(c)) for c in (25, -25)])
        self.assertEqual((opposite.status, opposite.reason), ("ambiguous", "zero_resultant"))
        self.assertIsNone(opposite.offset_cents)
        self.assertIsNone(opposite.representative_a4_hz)
        self.assertLess(opposite.concentration, 1e-12)

    def test_frame_count_does_not_change_a_note_budget(self):
        single = [detuned(0, "one", known_midi_note=69), detuned(0, "two", known_midi_note=69)]
        long = detuned(20, "three", known_midi_note=69)
        many = [*single, *([long] * 100)]
        per_note = estimate_tuning(many)
        per_frame = estimate_tuning(many, BY_OBSERVATION)
        self.assertAlmostEqual(per_note.offset_cents, 6.21838265533243, delta=5e-12)
        self.assertAlmostEqual(per_frame.offset_cents, 19.69916462819055, delta=5e-12)
        self.assertEqual((per_note.note_count, per_frame.note_count, per_note.eligible_count), (3, 3, 102))
        self.assertEqual((per_note.eligible_weight, per_note.effective_weight, per_frame.effective_weight), (102, 3, 102))
        self.assertEqual(per_note.evidence[-1].effective_weight, Fraction(1, 100))
        self.assertAlmostEqual(per_note.offset_cents, estimate_tuning([*single, long]).offset_cents, delta=5e-12)

    def test_internal_note_weights_preserve_dispersion(self):
        rows = [detuned(25, "spread", weight=3), detuned(-25, "spread", weight=3), detuned(0, "stable")]
        result = estimate_tuning(rows)
        self.assertEqual([v.effective_weight for v in result.evidence], [Fraction(1, 2), Fraction(1, 2), 1])
        self.assertAlmostEqual(result.offset_cents, 0, delta=5e-12)
        self.assertAlmostEqual(result.concentration, .5, delta=5e-12)

    def test_extreme_weights_keep_the_total_and_direction(self):
        wide = [detuned(0, "one", weight=1e308), detuned(20, "two", weight=1e308),
                detuned(-20, "three", weight=math.ldexp(1.0, -1074))]
        result = estimate_tuning(wide, BY_OBSERVATION)
        self.assertEqual(result.eligible_weight, sum(row.weight for row in wide))
        self.assertGreater(result.effective_weight, sys.float_info.max)
        self.assertEqual(result.eligible_count, 3)
        self.assertAlmostEqual(result.offset_cents, 10, delta=5e-12)
        scaled = [replace(row, weight=row.weight * Fraction(7, 2**1000)) for row in wide]
        self.assertEqual(estimate_tuning(scaled, BY_OBSERVATION).resultant, result.resultant)

    def test_concentration_floor_includes_equality(self):
        rows = [detuned(c, str(c)) for c in (-10, 10)]
        result = estimate_tuning(rows)
        admitted = estimate_tuning(rows, TuningProfile(minimum_concentration=result.concentration))
        rejected = estimate_tuning(rows, TuningProfile(
            minimum_concentration=math.nextafter(result.concentration, math.inf),
        ))
        self.assertEqual(admitted.status, "estimated")
        self.assertAlmostEqual(admitted.offset_cents, 0, delta=5e-12)
        self.assertAlmostEqual(admitted.concentration, math.cos(math.tau / 10), delta=5e-12)
        self.assertEqual((rejected.status, rejected.reason), ("ambiguous", "below_concentration"))
        self.assertIsNone(rejected.offset_cents)
        self.assertEqual(rejected.resultant, admitted.resultant)

    def test_single_residue_passes_unit_concentration_floor(self):
        result = estimate_tuning([detuned(13.25, "one")], TuningProfile(minimum_concentration=1))
        self.assertEqual((result.status, result.concentration), ("estimated", 1))
        self.assertAlmostEqual(result.offset_cents, 13.25, delta=5e-12)

    def test_minimum_notes_counts_events_with_positive_evidence(self):
        rows = [detuned(0, "one")] * 24 + [detuned(20, "zero weight", weight=0),
                TuningObservation(None, "unvoiced", status="unvoiced")]
        result = estimate_tuning(rows, TuningProfile(minimum_notes=2))
        self.assertEqual((result.status, result.reason), ("unavailable", "insufficient_notes"))
        self.assertEqual((result.eligible_count, result.note_count, result.concentration), (24, 1, 1))
        self.assertIsNone(result.offset_cents)

    def test_empty_zero_weight_and_excluded_input_remains_unavailable(self):
        excluded = [detuned(0, weight=0), TuningObservation(None, status="dc_only"),
                    replace(detuned(15, "excluded"), status="excluded"),
                    TuningObservation(None, status="unavailable")]
        for rows in ([], excluded):
            result = estimate_tuning(rows)
            self.assertEqual((result.status, result.reason), ("unavailable", "no_eligible_weight"))
            self.assertEqual((result.eligible_count, result.eligible_weight), (0, 0))
            self.assertIsNone(result.offset_cents)
            self.assertIsNone(result.concentration)
            self.assertEqual([v.observation for v in result.evidence], rows)

    def test_observation_weighting_accepts_unidentified_events(self):
        row = detuned(9)
        with self.assertRaises(ValueError):
            estimate_tuning([row])
        result = estimate_tuning([row], BY_OBSERVATION)
        self.assertEqual((result.note_count, result.eligible_count), (0, 1))
        self.assertAlmostEqual(result.offset_cents, 9, delta=5e-12)

    def test_mixed_groups_can_have_high_concentration(self):
        flat, sharp = (detuned(c, label) for c, label in ((-10, "flat"), (10, "sharp")))
        mixed = estimate_tuning([flat, sharp])
        self.assertAlmostEqual(mixed.offset_cents, 0, delta=5e-12)
        self.assertGreater(mixed.concentration, .8)
        self.assertTrue(all(abs(v.residue_cents) > 9 for v in mixed.evidence))
        for row, expected in ((flat, -10), (sharp, 10)):
            self.assertAlmostEqual(estimate_tuning([row]).offset_cents, expected, delta=5e-12)

    def test_invalid_profiles_and_observations_are_rejected(self):
        for constructor in (
            lambda: TuningProfile(0), lambda: TuningProfile(math.inf), lambda: TuningProfile(weighting="all"),
            lambda: TuningProfile(minimum_concentration=1.1), lambda: TuningProfile(minimum_notes=True),
            lambda: TuningObservation(-440, "n"), lambda: TuningObservation(math.nan, "n"),
            lambda: TuningObservation(None, "n"), lambda: TuningObservation(440, note_id=" "),
            lambda: TuningObservation(440, known_midi_note=128), lambda: TuningObservation(440, weight=-1),
            lambda: TuningObservation(440, weight=True), lambda: TuningObservation(440, weight=math.inf),
            lambda: TuningObservation(440, status="unvoiced"), lambda: TuningObservation(None, status="unknown"),
            lambda: estimate_tuning([detuned(0, "n")] * (MAX_OBSERVATIONS + 1)),
        ):
            with self.subTest(constructor=constructor), self.assertRaises(ValueError):
                constructor()


class ClockAndPitchIntegrationTests(unittest.TestCase):
    def test_rate_correction_sign_value_and_reported_provenance(self):
        support = TuningSupport(EPOCH, ORIGIN, ORIGIN + 10, ORIGIN + 10, ORIGIN + 10)
        row = TuningObservation(440, "reference tone", 69, support=support)
        actual = Fraction(240024, 5)
        result = estimate_tuning([row], actual_rate_hz=actual)
        self.assertEqual(result.evidence[0].calibrated_frequency_hz, Fraction(110011, 250))
        self.assertEqual((result.clock_factor, result.calibrated_rate_hz), (Fraction(10001, 10000), actual))
        self.assertAlmostEqual(result.offset_cents, 0.173114749313465, delta=5e-12)
        faster = replace(support, epoch=replace(EPOCH, epoch_id="fast", rate_hz=actual))
        reversed_rate = estimate_tuning([replace(row, support=faster)], actual_rate_hz=48000)
        self.assertAlmostEqual(reversed_rate.offset_cents, -result.offset_cents, delta=5e-12)
        no_correction = estimate_tuning([row])
        self.assertEqual((no_correction.offset_cents, no_correction.clock_factor), (0, 1))
        self.assertIsNone(no_correction.calibrated_rate_hz)

    def test_clock_replay_uses_merged_pitch_records(self):
        actual = Fraction(240024, 5)
        calibrated_epoch = replace(EPOCH, epoch_id="calibrated", rate_hz=actual)
        profile = PitchProfile(1440, 150, 1000)
        nominal = PitchGrid(EPOCH, profile, 1)
        calibrated = PitchGrid(calibrated_epoch, profile, 1)
        self.assertEqual((nominal.frame_length, calibrated.frame_length), (1761, 1762))
        nominal_rows, calibrated_rows = [], []
        for i, note in enumerate((60, 64, 69, 72)):
            frequency = 442 * 2**((note - 69) / 12)
            pcm = [0.4 * math.cos(math.tau * (j / float(actual)) * frequency + (i + 1) * .25)
                   for j in range(calibrated.frame_length)]
            start = ORIGIN + 2000 * i
            left = measure_pitch(pcm[:-1], nominal, start_sample=start)
            right = measure_pitch(pcm, calibrated, start_sample=start)
            self.assertEqual((left.status, right.status), ("voiced", "voiced"))
            self.assertEqual(left.selected.period_samples, right.selected.period_samples)
            nominal_rows.append(observation_from_pitch(left, note_id=str(i), known_midi_note=note))
            calibrated_rows.append(observation_from_pitch(right, note_id=str(i), known_midi_note=note))

        reported = estimate_tuning(nominal_rows)
        corrected = estimate_tuning(nominal_rows, actual_rate_hz=actual)
        replayed = estimate_tuning(calibrated_rows)
        self.assertAlmostEqual(reported.offset_cents, 7.67786575277, delta=1e-9)
        self.assertAlmostEqual(corrected.offset_cents, 7.85098050208, delta=1e-9)
        self.assertAlmostEqual(replayed.offset_cents, corrected.offset_cents, delta=1e-12)
        self.assertEqual(corrected.coverage, reported.coverage)
        self.assertEqual(corrected.coverage.evidence_ready_sample_exclusive, ORIGIN + 7761)
        self.assertEqual(replayed.coverage.evidence_ready_sample_exclusive, ORIGIN + 7762)
        self.assertEqual(corrected.evidence[-1].observation.support.center_sample_twice, 2*ORIGIN + 13760)

    def test_partial_input_and_delivery_do_not_change_evidence_boundaries(self):
        grid = PitchGrid(EPOCH, PitchProfile(7, 12000, 24000), hop_samples=4)
        tracker = PitchTracker(grid)
        pulse_train = [1, -1] * 11
        first, second, third = tracker.push(ORIGIN, pulse_train)
        partial = measure_pitch([0, 0], grid, start_sample=ORIGIN + 16)
        silence = measure_pitch([0] * 12, grid, start_sample=ORIGIN + 40)
        result = estimate_tuning([
            observation_from_pitch(first, note_id="one"),
            observation_from_pitch(second, note_id="one"),
            observation_from_pitch(third, note_id="one"),
            observation_from_pitch(partial),
            observation_from_pitch(silence),
        ])
        coverage = result.coverage
        self.assertEqual((coverage.epoch, coverage.start_sample, coverage.end_sample_exclusive),
                         (EPOCH, ORIGIN, ORIGIN + 52))
        self.assertEqual((coverage.available_end_sample_exclusive, coverage.evidence_ready_sample_exclusive,
                          coverage.evidence_release_sample_exclusive), (ORIGIN + 52, ORIGIN + 20, ORIGIN + 22))
        self.assertEqual(result.evidence[0].observation.support.center_sample_twice, 2*ORIGIN + 11)
        self.assertEqual(result.evidence[-2].observation.status, "unavailable")
        self.assertEqual(result.evidence[-2].observation.support.available_end_sample_exclusive, ORIGIN + 18)
        self.assertEqual(result.evidence[-1].observation.status, "silence")
        self.assertEqual((result.eligible_count, result.note_count), (3, 1))

    def test_unreported_release_remains_unknown_and_later_qualification_survives(self):
        one = TuningSupport(EPOCH, ORIGIN, ORIGIN + 12, ORIGIN + 12, ORIGIN + 20, ORIGIN + 22)
        two = TuningSupport(EPOCH, ORIGIN + 6, ORIGIN + 18, ORIGIN + 18, ORIGIN + 18)
        result = estimate_tuning([replace(detuned(0, "one"), support=one),
                                  replace(detuned(0, "one"), support=two)])
        self.assertEqual(result.coverage.evidence_ready_sample_exclusive, ORIGIN + 20)
        self.assertIsNone(result.coverage.evidence_release_sample_exclusive)
        self.assertEqual(result.evidence[0].observation.support.observed_release_sample_exclusive, ORIGIN + 22)

    def test_close_to_clock_limit_and_incomplete_ready_support(self):
        start = MAX_SAMPLE_INDEX - 4
        ep = replace(EPOCH, origin_sample=start)
        support = TuningSupport(ep, start, start + 4, start + 4, start + 4)
        self.assertEqual(support.center_sample_twice, 2 * start + 3)
        self.assertEqual(estimate_tuning([replace(detuned(0, "end"), support=support)]).coverage.end_sample_exclusive,
                         MAX_SAMPLE_INDEX)
        with self.assertRaises(ValueError):
            replace(support, end_sample_exclusive=MAX_SAMPLE_INDEX + 1)
        with self.assertRaises(ValueError):
            replace(support, available_end_sample_exclusive=start + 3)
        with self.assertRaises(ValueError):
            replace(support, observed_release_sample_exclusive=start + 3)

    def test_cannot_mix_epochs_or_invent_a_rate_for_untimed_data(self):
        a = TuningSupport(EPOCH, ORIGIN, ORIGIN + 6, ORIGIN + 6, ORIGIN + 6)
        row = replace(detuned(0, "set"), support=a)
        for other in (None, replace(a, epoch=replace(EPOCH, epoch_id="after seek")),
                      replace(a, epoch=replace(EPOCH, tap_id="other tap"))):
            with self.subTest(other=other), self.assertRaises(ValueError):
                estimate_tuning([row, replace(row, support=other)])
        with self.assertRaises(ValueError):
            estimate_tuning([detuned(0, "untimed")], actual_rate_hz=48000)
        with self.assertRaises(ValueError):
            estimate_tuning([row], actual_rate_hz=0)
