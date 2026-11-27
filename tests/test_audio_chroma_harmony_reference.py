"""Numerical, spectral, and timing fixtures for the chroma reference."""

from dataclasses import replace
from fractions import Fraction as F
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
for skill in (
    "audio-oscilloscope", "audio-pitch-tracking", "audio-power-spectral-density",
    "audio-tuning-analysis", "audio-chroma-harmony",
):
    sys.path.insert(0, str(ROOT / "skills" / skill / "scripts"))

from reference_chroma_harmony import (
    MAX_FFT_LENGTH, MAX_POWER_POINTS, BassObservation, ChromaGrid, ChromaProfile,
    PowerFrame, PowerPoint, analyze_chroma, power_frame_from_psd, score_triads, split_pitch,
)
from reference_oscilloscope import ScopeEpoch
from reference_psd import periodogram
from reference_tuning_analysis import TuningObservation, TuningSupport, estimate_tuning


ORIGIN = 2**60 + 37
EPOCH = ScopeEpoch("fixture", ORIGIN, F(48000), "capture clock", "input", "FS", ("mono",))


def support(start=0, length=64, *, epoch=EPOCH, ready=None, release=None):
    end = start + length
    ready = end if ready is None else ready
    return TuningSupport(
        epoch, ORIGIN + start, ORIGIN + end, ORIGIN + end, ORIGIN + ready,
        None if release is None else ORIGIN + release,
    )


def hz(midi, a4=440):
    return a4 * 2**((midi - 69) / 12)


def frame(points, where=None):
    return PowerFrame(support() if where is None else where, "FS^2",
                      tuple(PowerPoint(frequency, power) for frequency, power in points))


def triad(notes=(60, 64, 67), a4=440, where=None):
    return frame([(hz(note, a4), 1) for note in notes], where)


def label(row):
    return row.root, row.quality


class FoldAndPowerTests(unittest.TestCase):
    def test_exact_cyclic_split_and_mass(self):
        for pitch in (F(287, 4), F(-1, 4), F(47, 4)):
            with self.subTest(pitch=pitch):
                row = split_pitch(pitch, F(7, 3))
                self.assertEqual((row.lower_class, row.upper_class), (11, 0))
                self.assertEqual((row.lower_power, row.upper_power), (F(7, 12), F(7, 4)))
                self.assertEqual(row.lower_power + row.upper_power, F(7, 3))
        up = split_pitch(F(291, 4), 1)
        self.assertEqual((up.lower_class, up.upper_class, up.lower_power, up.upper_power),
                         (0, 1, F(1, 4), F(3, 4)))

    def test_exact_seam_and_adjacent_represented_pitches(self):
        below, above = (math.nextafter(72.0, direction) for direction in (-math.inf, math.inf))
        left, at, right = (split_pitch(p, 1) for p in (below, 72, above))
        self.assertEqual((left.lower_class, left.upper_class), (11, 0))
        self.assertGreater(left.lower_power, 0)
        self.assertEqual((at.lower_class, at.lower_power, at.upper_power), (0, 1, 0))
        self.assertEqual((right.lower_class, right.upper_class), (0, 1))
        self.assertGreater(right.upper_power, 0)

    def test_a_octaves_pool_with_exact_power(self):
        result = analyze_chroma(frame([(220, 2), (440, 1), (880, 4)]))
        self.assertEqual(result.raw_chroma, (0,) * 9 + (7, 0, 0))
        self.assertEqual(result.totals.admitted, 7)
        self.assertEqual(result.occupied_classes, (9,))
        self.assertEqual(len(result.competitors), 6)
        self.assertEqual(result.status, "ambiguous")
        self.assertIsNone(result.selected)

    def test_nearby_frequencies_keep_the_side_of_a_grid_center(self):
        lower = math.nextafter(440.0, -math.inf)
        higher = math.nextafter(440.0, math.inf)
        result = analyze_chroma(frame([(lower, 1), (higher, 1)]))
        left, right = (row.split for row in result.assignments)
        self.assertEqual((left.lower_class, left.upper_class), (8, 9))
        self.assertEqual((right.lower_class, right.upper_class), (9, 10))
        self.assertGreater(result.raw_chroma[8], 0)
        self.assertGreater(result.raw_chroma[10], 0)
        self.assertEqual(sum(result.raw_chroma), 2)

    def test_extreme_finite_power_and_frequency_scales(self):
        frequency = math.ldexp(1.5, 1023)
        very_low_reference = math.ldexp(1.0, -1074)
        epoch = replace(EPOCH, rate_hz=2 * F(frequency))
        power = sys.float_info.max
        result = analyze_chroma(frame([(frequency, power)] * 2, support(epoch=epoch)),
                                ChromaGrid(very_low_reference))
        self.assertGreater(result.totals.admitted, sys.float_info.max)
        self.assertEqual(sum(result.raw_chroma), 2 * F(power))
        split = result.assignments[0].split
        self.assertEqual((split.lower_class, split.upper_class), (4, 5))
        self.assertAlmostEqual(float(split.upper_power / F(power)), .019550008653874, delta=5e-14)

    def test_closed_band_and_point_gate_keep_a_power_ledger(self):
        source = frame([(0, 5), (100, 3), (220, 2), (440, F(1, 2)), (880, 4), (881, 1), (660, 0)])
        result = analyze_chroma(source, profile=ChromaProfile(220, 880, minimum_point_power=2))
        t = result.totals
        self.assertEqual((t.dc, t.outside_band, t.below_point_floor, t.admitted), (5, 4, F(1, 2), 6))
        self.assertEqual((t.in_band, t.input_total), (F(13, 2), F(31, 2)))
        self.assertEqual(result.raw_chroma[9], 6)
        self.assertEqual([item.point.frequency_hz for item in result.assignments], [220, 880])

    def test_zero_input_and_unavailable_frame_have_distinct_support(self):
        empty = analyze_chroma(frame([]))
        dc = analyze_chroma(frame([(0, 2), (440, 0)]))
        partial = TuningSupport(EPOCH, ORIGIN, ORIGIN + 64, ORIGIN + 20, None, ORIGIN + 25)
        missing = analyze_chroma(PowerFrame(partial, "FS^2"))
        for row in (empty, dc):
            self.assertEqual(row.status, "insufficient_power")
            self.assertEqual(row.raw_chroma, (0,) * 12)
            self.assertEqual(row.ranking, ())
            self.assertEqual(row.ready_sample_exclusive, ORIGIN + 64)
        self.assertEqual(dc.totals.dc, 2)
        self.assertEqual(missing.status, "input_unavailable")
        self.assertIsNone(missing.raw_chroma)
        self.assertIsNone(missing.totals)
        self.assertIsNone(missing.ready_sample_exclusive)
        self.assertEqual(missing.frame.support.available_end_sample_exclusive, ORIGIN + 20)

    def test_class_share_floor_reports_occupancy_without_losing_raw_power(self):
        source = frame([(440, 3), (hz(60), 1)])
        result = analyze_chroma(source, profile=ChromaProfile(minimum_class_share=F(1, 2)))
        self.assertEqual(result.occupied_classes, (9,))
        self.assertEqual(result.totals.admitted, 4)
        self.assertEqual(result.raw_chroma[9], 3)
        self.assertEqual(result.ranking, analyze_chroma(source).ranking)

    def test_psd_adapter_replays_dc_interior_and_even_nyquist(self):
        pcm = [.125 + .4 * math.cos(math.tau * 8 * n / 64) + .2 * (-1)**n for n in range(64)]
        epoch = replace(EPOCH, rate_hz=F(3520))
        _, density = periodogram(pcm, [1.0] * 64, 3520)
        source = power_frame_from_psd(density, fft_length=64, support=support(epoch=epoch), power_units="FS^2")
        result = analyze_chroma(source)
        self.assertEqual(source.fft_length, 64)
        self.assertEqual(tuple(source.points[i].frequency_hz for i in (0, 8, 32)), (0, 440, 1760))
        for i, expected in ((0, .015625), (8, .08), (32, .04)):
            self.assertAlmostEqual(float(source.points[i].power), expected, delta=2e-15)
        self.assertAlmostEqual(float(result.totals.input_total), .135625, delta=2e-15)
        self.assertAlmostEqual(float(result.raw_chroma[9]), .12, delta=2e-15)
        self.assertEqual(sum(result.raw_chroma), result.totals.admitted)

    def test_psd_adapter_replays_last_odd_bin(self):
        pcm = [.2 * math.cos(math.tau * 31 * n / 63) for n in range(63)]
        _, density = periodogram(pcm, [1.0] * 63, 3465)
        source = power_frame_from_psd(
            density, fft_length=63, support=support(length=63, epoch=replace(EPOCH, rate_hz=F(3465))),
            power_units="FS^2",
        )
        self.assertEqual(source.points[-1].frequency_hz, 1705)
        self.assertAlmostEqual(float(source.points[-1].power), .02, delta=2e-15)
        self.assertAlmostEqual(float(analyze_chroma(source).totals.admitted), .02, delta=2e-15)

    def test_psd_adapter_uses_exact_calibrated_spacing_and_padding(self):
        epoch = replace(EPOCH, rate_hz=F(48000, 1001))
        source = power_frame_from_psd([F(1, 8)] * 9, fft_length=16,
                                      support=support(length=10, epoch=epoch), power_units="FS^2")
        spacing = F(3000, 1001)
        self.assertEqual(source.points[1].frequency_hz, spacing)
        self.assertEqual(source.points[-1].frequency_hz, epoch.rate_hz / 2)
        self.assertTrue(all(p.power == spacing / 8 for p in source.points))
        self.assertEqual(source.support.end_sample_exclusive, ORIGIN + 10)


class TemplateAndBassTests(unittest.TestCase):
    def test_exact_triads_dyad_four_note_and_flat_evidence(self):
        cases = (
            ((0, 4, 7), F(1), ((0, "maj"),)),
            ((0, 3, 7), F(1), ((0, "min"),)),
            ((0, 7), F(2, 3), ((0, "maj"), (0, "min"))),
            ((0, 4, 7, 9), F(3, 4), ((0, "maj"), (9, "min"))),
        )
        for pcs, expected, winners in cases:
            with self.subTest(pcs=pcs):
                ranking = score_triads([int(k in pcs) for k in range(12)])
                self.assertEqual(ranking[0].score_squared, expected)
                self.assertEqual(tuple(label(row) for row in ranking if row.score_squared == expected), winners)
                self.assertEqual(len(ranking), 24)
        self.assertTrue(all(row.score_squared == F(1, 4) for row in score_triads([1] * 12)))
        self.assertEqual(score_triads([0] * 12), ())

    def test_near_tie_inclusive_exact_margin(self):
        masses = [0] * 12
        for i in (0, 4, 7, 9):
            masses[i] = 1
        masses[7] = F(4097, 4096)
        ranking = score_triads(masses)
        self.assertEqual(ranking[0].score_squared - ranking[1].score_squared, F(3511, 28764453))
        source = frame([(hz(60 + i), mass) for i, mass in enumerate(masses) if mass])
        winner = analyze_chroma(source)
        self.assertEqual(winner.status, "matched")
        self.assertAlmostEqual(float(winner.margin_squared), 0.00012206037778643, delta=2e-14)
        tied = analyze_chroma(source, profile=ChromaProfile(ambiguity_margin_squared=winner.margin_squared))
        self.assertEqual((tied.status, tied.selected), ("ambiguous", None))
        self.assertEqual(tuple(map(label, tied.competitors)), ((0, "maj"), (9, "min")))
        loose = analyze_chroma(source, profile=ChromaProfile(ambiguity_margin_squared=F(1, 8000)))
        self.assertEqual(loose.competitors, tied.competitors)

    def test_template_floor_includes_equality_and_exposes_poor_fit(self):
        source = frame([(hz(60), 3), (hz(64), 1), (hz(67), 1)])
        ranking = analyze_chroma(source).ranking
        score = ranking[0].score_squared
        exactly = analyze_chroma(source, profile=ChromaProfile(minimum_score_squared=score))
        higher = analyze_chroma(source, profile=ChromaProfile(minimum_score_squared=score + F(1, 10**20)))
        self.assertEqual(exactly.status, "matched")
        self.assertEqual((higher.status, higher.selected), ("poor_fit", None))
        self.assertEqual(higher.ranking, ranking)

    def test_absolute_power_gate_preserves_scale_invariant_shape(self):
        loud = triad()
        soft = replace(loud, points=tuple(replace(point, power=F(1, 10**6)) for point in loud.points))
        self.assertEqual(analyze_chroma(loud).ranking, analyze_chroma(soft).ranking)
        threshold = ChromaProfile(minimum_admitted_power=F(1, 1000))
        rejected = analyze_chroma(soft, profile=threshold)
        self.assertEqual((rejected.status, rejected.ranking), ("insufficient_power", ()))
        self.assertEqual(rejected.totals.admitted, F(3, 10**6))
        self.assertEqual(sum(rejected.raw_chroma), F(3, 10**6))
        self.assertEqual(analyze_chroma(loud, profile=replace(threshold, minimum_admitted_power=3)).status,
                         "matched")

    def test_harmonic_partials_can_match_a_triad_from_one_source(self):
        source = frame([(hz(60) * harmonic, 1) for harmonic in (1, 3, 5)])
        match = analyze_chroma(source)
        self.assertEqual(label(match.selected), (0, "maj"))
        self.assertAlmostEqual(float(match.selected.score_squared), .98896592100493, delta=1e-12)
        self.assertIsNone(match.inversion)

    def test_inversions_share_chroma_and_require_an_independent_bass(self):
        fundamental, third, fifth = (F(hz(n)) for n in (60, 64, 67))
        root = frame([(fundamental, 1), (third, 1), (fifth, 1)])
        inverted = frame([(third / 2, 1), (fifth / 2, 1), (fundamental, 1)])
        root_match = analyze_chroma(root, bass=BassObservation(fundamental, support()))
        third_match = analyze_chroma(inverted, bass=BassObservation(third / 2, support()))
        fifth_match = analyze_chroma(inverted, bass=BassObservation(fifth / 2, support()))
        self.assertEqual(root_match.raw_chroma, third_match.raw_chroma)
        self.assertEqual(root_match.selected, third_match.selected)
        self.assertEqual((root_match.inversion, third_match.inversion, fifth_match.inversion), (0, 1, 2))
        self.assertIsNone(analyze_chroma(inverted).inversion)

    def test_bass_off_grid_or_outside_the_triad_cannot_supply_inversion(self):
        source = triad()
        off = analyze_chroma(source, bass=BassObservation(hz(52.4), support()))
        outside = analyze_chroma(source, bass=BassObservation(hz(50), support()))
        self.assertAlmostEqual(float(off.bass_error_cents), 40, delta=5e-12)
        self.assertIsNone(off.bass_class)
        self.assertEqual(outside.bass_class, 2)
        self.assertEqual((off.status, outside.status), ("matched", "matched"))
        self.assertIsNone(off.inversion)
        self.assertIsNone(outside.inversion)


class TuningAndTimeTests(unittest.TestCase):
    def test_merged_tuning_and_a_declared_shifted_grid_agree(self):
        notes = (60, 64, 67)
        source = triad(notes, 442)
        tune = estimate_tuning([TuningObservation(hz(n, 442), str(n), n) for n in notes])
        corrected = analyze_chroma(source, ChromaGrid.from_tuning(tune, semitone_lift=0))
        shifted = analyze_chroma(source, ChromaGrid(442))
        raw = analyze_chroma(source)
        self.assertAlmostEqual(float(corrected.grid.correction_cents), 7.8514150401265, delta=1e-12)
        self.assertAlmostEqual(float(sum(raw.raw_chroma[k] for k in (1, 5, 8))), .2355424512, delta=1e-10)
        for left, right in zip(corrected.raw_chroma, shifted.raw_chroma):
            self.assertAlmostEqual(float(left - right), 0, delta=2e-12)
        self.assertEqual((label(corrected.selected), label(shifted.selected)), ((0, "maj"), (0, "maj")))
        with self.assertRaises(ValueError):
            ChromaGrid(442, tune, semitone_lift=0)

    def test_wrapped_offset_ranks_relative_classes_until_anchored(self):
        notes = (60, 64, 67)
        sharp = 440 * 2**(55 / 1200)
        tuning = estimate_tuning([TuningObservation(hz(n, sharp), str(n), n) for n in notes])
        source = triad(notes, sharp)
        unanchored = analyze_chroma(source, ChromaGrid.from_tuning(tuning))
        anchored = analyze_chroma(source, ChromaGrid.from_tuning(tuning, semitone_lift=1))
        self.assertEqual(unanchored.status, "unanchored")
        self.assertIsNone(unanchored.selected)
        self.assertEqual(label(unanchored.ranking[0]), (1, "maj"))
        self.assertAlmostEqual(float(unanchored.grid.correction_cents), -45, delta=5e-12)
        self.assertAlmostEqual(float(anchored.grid.correction_cents), 55, delta=5e-12)
        self.assertEqual(label(anchored.selected), (0, "maj"))
        self.assertAlmostEqual(tuning.evidence[0].known_note_error_cents, 55, delta=5e-12)

    def test_opposing_tuning_has_no_grid_direction(self):
        tuning = estimate_tuning([TuningObservation(440 * 2**(c / 1200), str(c)) for c in (-25, 25)])
        result = analyze_chroma(triad(), ChromaGrid.from_tuning(tuning))
        self.assertEqual(tuning.status, "ambiguous")
        self.assertEqual(result.status, "tuning_unavailable")
        self.assertIsNone(result.raw_chroma)
        self.assertIsNone(result.ready_sample_exclusive)
        self.assertIsNone(result.selected)

    def test_timed_calibration_changes_band_coordinates_without_changing_mass(self):
        rate = F(240024, 5)
        factor = rate / EPOCH.rate_hz
        source = frame([(F(440) / factor, 3)], support(start=12, length=16))
        tune = estimate_tuning([
            TuningObservation(F(440) / factor, "calibration", 69, support=support(length=40)),
        ], actual_rate_hz=rate)
        band = ChromaProfile(440, 440)
        result = analyze_chroma(source, ChromaGrid.from_tuning(tune, semitone_lift=0), band)
        self.assertEqual(tune.clock_factor, F(10001, 10000))
        self.assertEqual(result.totals.admitted, 3)
        self.assertEqual(result.assignments[0].calibrated_frequency_hz, 440)
        self.assertEqual(result.assignments[0].point.frequency_hz, F(440) / factor)
        self.assertEqual(result.raw_chroma[9], 3)
        self.assertEqual(result.ready_sample_exclusive, ORIGIN + 40)
        self.assertEqual(analyze_chroma(source, profile=band).totals.outside_band, 3)

    def test_tuning_and_bass_preserve_late_ready_and_release_boundaries(self):
        source = triad(where=support(start=20, length=40, ready=63, release=66))
        tune = estimate_tuning([
            TuningObservation(440, "note", support=support(length=80, ready=128, release=140)),
        ])
        grid = ChromaGrid.from_tuning(tune, semitone_lift=0)
        bass = BassObservation(hz(52), support(start=39, length=2, ready=146, release=158))
        result = analyze_chroma(source, grid, bass=bass)
        self.assertEqual(result.frame.support.center_sample_twice, 2 * ORIGIN + 79)
        self.assertEqual((result.ready_sample_exclusive, result.evidence_release_sample_exclusive),
                         (ORIGIN + 146, ORIGIN + 158))
        self.assertEqual(result.inversion, 1)
        timing = analyze_chroma(source, grid)
        self.assertEqual((timing.ready_sample_exclusive, timing.evidence_release_sample_exclusive),
                         (ORIGIN + 128, ORIGIN + 140))
        missing = analyze_chroma(source, grid, bass=replace(
            bass, support=replace(bass.support, observed_release_sample_exclusive=None),
        ))
        self.assertEqual(missing.ready_sample_exclusive, ORIGIN + 146)
        self.assertIsNone(missing.evidence_release_sample_exclusive)

    def test_timed_tuning_cannot_cross_its_epoch_or_available_scope(self):
        tune = estimate_tuning([TuningObservation(440, "note", support=support(length=65))])
        grid = ChromaGrid.from_tuning(tune, semitone_lift=0)
        admitted = analyze_chroma(triad(where=support(start=1, length=64)), grid)
        self.assertEqual(admitted.status, "matched")
        for location in (support(start=2), support(epoch=replace(EPOCH, tap_id="another tap"))):
            with self.subTest(location=location):
                result = analyze_chroma(triad(where=location), grid)
                self.assertEqual(result.status, "tuning_out_of_scope")
                self.assertIsNone(result.raw_chroma)
                self.assertIsNone(result.ready_sample_exclusive)

    def test_bass_support_is_half_open_on_the_frame_center(self):
        source = triad(where=support(length=65))
        outside = BassObservation(hz(52), support(start=30, length=2, ready=80))
        admitted = BassObservation(hz(52), support(start=32, length=2, ready=80))
        wrong_epoch = replace(admitted, support=replace(admitted.support, epoch=replace(EPOCH, epoch_id="seek")))
        absent = analyze_chroma(source, bass=outside)
        other = analyze_chroma(source, bass=wrong_epoch)
        qualified = analyze_chroma(source, bass=admitted)
        self.assertIsNone(absent.bass_class)
        self.assertEqual(absent.ready_sample_exclusive, ORIGIN + 65)
        self.assertIsNone(other.bass_class)
        self.assertEqual((qualified.ready_sample_exclusive, qualified.inversion), (ORIGIN + 80, 1))


class ValidationTests(unittest.TestCase):
    def test_reject_invalid_evidence_and_profiles(self):
        complete = support(length=64)
        partial = replace(complete, available_end_sample_exclusive=ORIGIN + 30, ready_sample_exclusive=None)
        checks = (
            lambda: PowerPoint(-1, 2), lambda: PowerPoint(440, -1),
            lambda: PowerPoint(440, math.inf), lambda: PowerPoint(math.nan, 1),
            lambda: frame([(24001, 1)]), lambda: frame([(440, 1)], partial),
            lambda: PowerFrame(complete, " "), lambda: PowerFrame(complete, "FS^2", [PowerPoint(440, 1)]),
            lambda: PowerFrame(complete, "FS^2", (PowerPoint(440, 1),) * (MAX_POWER_POINTS + 1)),
            lambda: power_frame_from_psd([1] * 32, fft_length=64, support=complete, power_units="FS^2"),
            lambda: power_frame_from_psd([1] * 33, fft_length=64, support=partial, power_units="FS^2"),
            lambda: power_frame_from_psd([1] * 17, fft_length=32, support=complete, power_units="FS^2"),
            lambda: power_frame_from_psd([], fft_length=MAX_FFT_LENGTH + 1, support=complete, power_units="FS^2"),
            lambda: ChromaProfile(maximum_hz=0), lambda: ChromaProfile(100, 10),
            lambda: ChromaProfile(minimum_point_power=-1), lambda: ChromaProfile(minimum_class_share=2),
            lambda: ChromaProfile(minimum_score_squared=math.nan), lambda: ChromaProfile(ambiguity_margin_squared=2),
            lambda: ChromaProfile(bass_tolerance_cents=50),
            lambda: BassObservation(0, complete), lambda: BassObservation(440, partial),
            lambda: ChromaGrid(0), lambda: ChromaGrid(semitone_lift=1),
            lambda: split_pitch(math.inf, 1), lambda: split_pitch(60, -1),
            lambda: score_triads([0] * 11), lambda: score_triads([-1] + [0] * 11),
        )
        for i, check in enumerate(checks):
            with self.subTest(check=i), self.assertRaises(ValueError):
                check()
