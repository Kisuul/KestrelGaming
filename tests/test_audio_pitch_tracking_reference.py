"""Exact support, voicing, range, and timing fixtures for monophonic pitch."""

from bisect import bisect_left
from dataclasses import replace
from fractions import Fraction as F
import math
from pathlib import Path
import random
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
for skill in ("audio-oscilloscope", "audio-pitch-tracking"):
    sys.path.insert(0, str(ROOT / "skills" / skill / "scripts"))

from reference_oscilloscope import MAX_SAMPLE_INDEX, ScopeEpoch
from reference_pitch_tracking import (
    MAX_BLOCK_SAMPLES, MAX_COMPARISON_SAMPLES, PitchGrid, PitchProfile, PitchTracker, measure_pitch,
)


RATE = 48000
ORIGIN = 2**60 + 37
EPOCH = ScopeEpoch("fixture", ORIGIN, F(RATE), "sample clock", "input", "FS", ("mono",))


def period_grid(width, low=48, high=240, *, mode="raw", hop=1, epoch=EPOCH, floor=0, threshold=F(1, 10)):
    rate = epoch.rate_hz
    profile = PitchProfile(width, rate / F(high), rate / F(low), threshold, floor, mode)
    return PitchGrid(epoch, profile, hop)


def periodic(grid, signals, period):
    cycle = [sum(a * math.cos(math.tau * j / p) for p, a in signals) for j in range(period)]
    return [cycle[j % period] for j in range(grid.frame_length)]


def tone(grid, period, amplitude=0.4, phase=0.0):
    return [amplitude * math.cos(math.tau * j / period + phase) for j in range(grid.frame_length)]


class DifferenceTests(unittest.TestCase):
    def test_fixed_pair_count_and_normalization_includes_lower_lags(self):
        g = period_grid(3, 2, 3, mode="integer")
        row = measure_pitch([1, 3, 0, 2, 4, 1, -2], g)
        self.assertEqual((g.frame_length, g.maximum_lag), (7, 4))
        self.assertEqual(row.difference.raw, (0, 17, 18, 3, 17))
        self.assertEqual(row.difference.cmnd, (1, 1, F(36, 35), F(9, 38), F(68, 55)))

    def test_local_zero_denominator_is_unavailable(self):
        g = period_grid(1, 2, 3, mode="integer")
        row = measure_pitch([1, 1, 2, 1, 2], g)
        self.assertEqual(row.difference.cmnd, (1, None, 2, 0, 2))
        self.assertEqual(row.selected.seed_lag, 3)

    def test_finite_subnormal_and_maximum_pcm_keep_exact_energy(self):
        g = period_grid(7, 2, 4)
        for amplitude in (math.ldexp(1.0, -1074), sys.float_info.max):
            x = [amplitude, -amplitude] * 6
            exact = F(amplitude)
            row = measure_pitch(x, g)
            self.assertEqual(row.mean_pcm, 0)
            self.assertEqual(row.ac_mean_square, exact**2)
            self.assertEqual(row.difference.raw[1], 28 * exact**2)
            self.assertEqual(row.difference.cmnd[2], 0)
            self.assertEqual(row.selected.frequency_hz, RATE // 2)

    def test_small_modulation_on_dc_uses_represented_pcm(self):
        g = period_grid(960)
        x = [0.5 + math.ldexp(1.0, -30) * math.cos(math.tau*j / (768/7)) for j in range(g.frame_length)]
        row = measure_pitch(x, g)
        for lag in (1, 33, 109, g.maximum_lag):
            expected = sum((F(x[i]) - F(x[i + lag]))**2 for i in range(960))
            self.assertEqual(row.difference.raw[lag], expected)
        self.assertGreater(row.ac_mean_square, 0)
        self.assertTrue(all(d >= 0 for d in row.difference.raw))
        self.assertEqual(row.selected.seed_lag, 110)

    def test_linear_energy_identity_matches_direct_ingress(self):
        rng = random.Random(390039)
        for w, lag_max in ((5, 7), (8, 4), (13, 11), (17, 19)):
            g = period_grid(w, 2, lag_max, mode="integer")
            x = [rng.randrange(-128, 129)/64 for _ in range(g.frame_length)]
            row = measure_pitch(x, g)
            values = tuple(map(F, x))
            left = values[:w]
            p0 = sum(v*v for v in left)
            for lag, actual in enumerate(row.difference.raw):
                right = values[lag:lag+w]
                pp = sum(v*v for v in right)
                cross = sum(a*b for a, b in zip(left, right))
                self.assertEqual(actual, p0 + pp - 2*cross)

    def test_fixed_gain_and_offset_leave_exact_cmnd_unchanged(self):
        g = period_grid(20, 2, 20, mode="integer")
        base = (0, 1, 3, 1, 0, -1)
        v = [base[i % len(base)] for i in range(g.frame_length)]
        a = measure_pitch(v, g)
        b = measure_pitch([7 - 2*x for x in v], g)
        self.assertEqual(b.mean_pcm, 7 - 2*a.mean_pcm)
        self.assertEqual(b.ac_mean_square, 4*a.ac_mean_square)
        self.assertEqual(a.difference.cmnd, b.difference.cmnd)
        self.assertEqual(tuple(4*v for v in a.difference.raw), b.difference.raw)
        self.assertEqual(a.selected, b.selected)


class CandidateTests(unittest.TestCase):
    def test_missing_fundamental_and_even_only_period(self):
        g = period_grid(960)
        a = measure_pitch(periodic(g, [(60, 0.3), (40, 0.2)], 120), g)
        b = measure_pitch(periodic(g, [(60, 0.3)], 60), g)
        self.assertAlmostEqual(float(a.difference.raw[40] / 960), 0.135, delta=3e-16)
        self.assertAlmostEqual(float(a.difference.raw[60] / 960), 0.08, delta=3e-16)
        self.assertEqual(a.difference.raw[120], 0)
        self.assertEqual((a.selected.seed_lag, a.selected.frequency_hz), (120, 400))
        self.assertEqual((b.selected.seed_lag, b.selected.frequency_hz), (60, 800))

    def test_weak_odd_harmonic_keeps_the_other_octave_candidate(self):
        g = period_grid(960, mode="integer")
        cases = [(0.03, 60, 0.01979871308365), (0.09, 120, 0.16491067338525)]
        for amplitude, lag, depth in cases:
            with self.subTest(amplitude=amplitude):
                row = measure_pitch(periodic(g, [(60, 0.3), (40, amplitude)], 120), g)
                self.assertEqual(row.selected.seed_lag, lag)
                self.assertEqual(row.difference.cmnd[120], 0)
                self.assertAlmostEqual(float(row.difference.cmnd[60]), depth, delta=2e-14)
                depths = {v.seed_lag: v.status for v in row.candidates}
                self.assertEqual(depths[120], "eligible")
                self.assertEqual(depths[60], "eligible" if lag == 60 else "threshold_rejected")

    def test_threshold_equality_rejects_a_trough(self):
        g = period_grid(960, mode="integer")
        samples = periodic(g, [(60, 0.3), (40, 0.03)], 120)
        witness = measure_pitch(samples, g)
        tuned = replace(g, profile=replace(g.profile, threshold=witness.difference.cmnd[60]))
        row = measure_pitch(samples, tuned)
        modes = {v.seed_lag: v.status for v in row.candidates}
        self.assertEqual(modes[60], "threshold_rejected")
        self.assertEqual(row.selected.seed_lag, 120)

    def test_a_commensurate_mixture_has_a_new_repetition_period(self):
        g = period_grid(960, 48, 320)
        row = measure_pitch(periodic(g, [(120, .3), (80, .25)], 240), g)
        self.assertEqual((row.selected.seed_lag, row.selected.frequency_hz), (240, 200))

    def test_white_noise_stays_unvoiced_with_trough_evidence(self):
        g = period_grid(960, 48, 320)
        rng = random.Random(390091)
        row = measure_pitch([rng.uniform(-.2, .2) for _ in range(g.frame_length)], g)
        self.assertEqual(row.status, "unvoiced")
        self.assertIsNone(row.selected)
        self.assertTrue(row.candidates)
        self.assertTrue(all(c.status == "threshold_rejected" for c in row.candidates))

    def test_plateau_selects_first_member_and_can_fit_a_half_lag(self):
        samples = [0, 1, 0, 0, 1, 1]
        coarse = period_grid(1, 2, 4, mode="integer")
        a = measure_pitch(samples, coarse)
        b = measure_pitch(samples, replace(coarse, profile=replace(coarse.profile, refinement="raw")))
        self.assertEqual([c.seed_lag for c in a.candidates], [2])
        self.assertEqual(a.selected.period_samples, 2)
        self.assertEqual(b.selected.period_samples, F(5, 2))

    def test_nonconvex_raw_candidate_retains_explicit_integer_fallback(self):
        g = period_grid(1, 2, 4)
        row = measure_pitch([0, 100, 100, 10, 9.99, 1], g)
        c = row.selected
        self.assertEqual((c.seed_lag, c.period_samples, c.method), (3, 3, "integer_fallback"))
        self.assertLess(row.difference.raw[4], row.difference.raw[3])

    def test_raw_and_cmnd_interpolate_the_same_seed_differently(self):
        raw_grid = period_grid(960)
        cmnd_grid = replace(raw_grid, profile=replace(raw_grid.profile, refinement="cmnd"))
        x = tone(raw_grid, F(768, 7))
        a = measure_pitch(x, raw_grid).selected
        b = measure_pitch(x, cmnd_grid).selected
        self.assertEqual((a.seed_lag, b.seed_lag, a.method, b.method), (110, 110, "raw", "cmnd"))
        self.assertAlmostEqual(float(a.frequency_hz), 437.50135765, delta=1e-7)
        self.assertAlmostEqual(float(b.frequency_hz), 437.51494149, delta=1e-7)
        self.assertLess(abs(a.frequency_hz - F(875, 2)), abs(b.frequency_hz - F(875, 2)))

    def test_interpolation_uses_guard_seeds_at_both_edges(self):
        cases = [
            (F("96.125"), F("98.125"), F("96.25"), 96, 100, 96.24991686),
            (F("118.25"), F("119.875"), F("119.75"), 120, 121, 119.75004015),
        ]
        for lo, hi, ideal, seed, boundary, expect in cases:
            with self.subTest(ideal=ideal):
                plain = period_grid(960, lo, hi, mode="integer")
                good = period_grid(960, lo, hi)
                self.assertEqual(good.maximum_lag, boundary)
                self.assertEqual(measure_pitch(tone(plain, ideal), plain).status, "unvoiced")
                self.assertFalse(plain.first_seed_lag <= seed <= plain.last_seed_lag)
                row = measure_pitch(tone(good, ideal), good)
                self.assertIsNotNone(row.selected)
                self.assertEqual(row.selected.seed_lag, seed)
                self.assertAlmostEqual(float(row.selected.period_samples), expect, delta=1e-8)
                self.assertTrue(lo <= row.selected.period_samples <= hi)

    def test_out_of_band_refinement_is_kept_without_a_selected_pitch(self):
        g = period_grid(960, F("109.7141"), F("109.715"))
        row = measure_pitch(tone(g, F(768, 7)), g)
        self.assertEqual(row.status, "unvoiced")
        self.assertIsNone(row.selected)
        fit, = row.candidates
        self.assertEqual((fit.seed_lag, fit.status), (110, "out_of_band"))
        self.assertLess(fit.period_samples, g.period_min)

    def test_integer_band_without_a_seed_has_no_candidate(self):
        g = period_grid(8, F(9, 4), F(11, 4), mode="integer")
        row = measure_pitch(tone(g, 2.5), g)
        self.assertEqual((g.first_seed_lag, g.last_seed_lag), (3, 2))
        self.assertEqual(row.status, "unvoiced")
        self.assertEqual(row.candidates, ())

    def test_short_low_pitch_support_can_fit_the_wrong_period(self):
        small = period_grid(63, 48, 960, mode="cmnd")
        long = period_grid(1920, 48, 960, mode="cmnd")
        phase = -math.tau * 315 / 960
        a = measure_pitch(tone(small, 960, phase=phase), small)
        b = measure_pitch(tone(long, 960, phase=phase), long)
        self.assertEqual((small.frame_length, long.frame_length), (1024, 2881))
        self.assertEqual((a.selected.seed_lag, b.selected.seed_lag), (568, 960))
        self.assertAlmostEqual(float(a.selected.depth), .06374775925, delta=1e-9)
        self.assertAlmostEqual(float(a.selected.frequency_hz), 84.47736456, delta=1e-5)
        self.assertAlmostEqual(float(b.selected.frequency_hz), 50, delta=1e-3)


class LevelAndClockTests(unittest.TestCase):
    def test_typed_silence_and_nonzero_dc_have_unsupported_positive_lags(self):
        g = period_grid(7, 2, 4)
        for constant, label in ((0.0, "silence"), (.125, "dc_only"), (-7, "dc_only")):
            with self.subTest(constant=constant):
                p = measure_pitch([constant] * g.frame_length, g)
                self.assertEqual((p.status, p.mean_pcm, p.ac_mean_square), (label, F(constant), 0))
                self.assertEqual(p.difference.raw, (0,) * (g.maximum_lag + 1))
                self.assertEqual(p.difference.cmnd, (1,) + (None,) * g.maximum_lag)
                self.assertIsNone(p.selected)
                self.assertEqual(p.ready_sample_exclusive, p.end_sample_exclusive)

    def test_ac_floor_uses_ac_power_and_has_inclusive_equality(self):
        g = period_grid(7, 2, 4, floor=F(1, 4))
        at_floor = [.75, .25] * 6
        low = [.625, .375] * 6
        a = measure_pitch(at_floor, g)
        b = measure_pitch(low, g)
        self.assertEqual((a.mean_pcm, a.ac_mean_square, a.status), (F(1, 2), F(1, 16), "voiced"))
        self.assertEqual((b.mean_pcm, b.ac_mean_square, b.status), (F(1, 2), F(1, 64), "below_floor"))
        self.assertEqual(a.difference.cmnd, b.difference.cmnd)
        self.assertTrue(b.candidates)
        self.assertIsNone(b.selected)

    def test_short_frame_keeps_nominal_support_and_missing_readiness_separate(self):
        g = period_grid(7, 2, 4, hop=4)
        p = measure_pitch([1, -1], g, start_sample=ORIGIN+8, observed_release_sample_exclusive=ORIGIN+13)
        self.assertEqual(p.status, "unavailable")
        self.assertEqual(p.available_end_sample_exclusive, ORIGIN+10)
        self.assertEqual(p.end_sample_exclusive, ORIGIN+20)
        self.assertEqual(p.center_sample_twice, 2*ORIGIN+27)
        self.assertEqual(p.observed_release_sample_exclusive, ORIGIN+13)
        self.assertIsNone(p.ready_sample_exclusive)
        self.assertIsNone(p.mean_pcm)
        self.assertIsNone(p.difference)

    def test_rate_and_time_remain_exact_at_large_origin(self):
        ep = replace(EPOCH, rate_hz=F(48000, 1001))
        g = period_grid(7, 2, 4, epoch=ep, hop=4)
        p = measure_pitch([1, -1]*6, g, start_sample=ORIGIN+12, observed_release_sample_exclusive=ORIGIN+27)
        self.assertEqual((p.start_sample, p.end_sample_exclusive), (ORIGIN+12, ORIGIN+24))
        self.assertEqual(p.center_sample_twice, 2*ORIGIN+35)
        self.assertEqual(p.ready_sample_exclusive, ORIGIN+24)
        self.assertEqual(p.selected.frequency_hz, F(24000, 1001))
        self.assertEqual(p.observed_release_sample_exclusive, ORIGIN+27)

    def test_clock_end_is_bounded_even_for_a_partial_request(self):
        origin = MAX_SAMPLE_INDEX-12
        ep = replace(EPOCH, origin_sample=origin)
        g = period_grid(7, 2, 4, epoch=ep)
        self.assertEqual(measure_pitch([1, -1]*6, g).ready_sample_exclusive, MAX_SAMPLE_INDEX)
        with self.assertRaises(ValueError):
            measure_pitch([], g, start_sample=origin+1)

    def test_invalid_profiles_and_input_are_reported_before_analysis(self):
        g = period_grid(7, 2, 4, hop=4)
        cases = (
            lambda: PitchProfile(True, 50, 1000), lambda: PitchProfile(0, 50, 1000),
            lambda: PitchProfile(MAX_COMPARISON_SAMPLES+1, 50, 1000),
            lambda: PitchProfile(8, 200, 100), lambda: PitchProfile(8, 0, 100),
            lambda: PitchProfile(8, 100, math.nan),
            lambda: PitchProfile(8, 100, 200, 0), lambda: PitchProfile(8, 100, 200, F(11, 10)),
            lambda: PitchProfile(8, 100, 200, ac_rms_floor=-3),
            lambda: PitchProfile(8, 100, 200, refinement="unknown"),
            lambda: replace(g, profile=replace(g.profile, maximum_hz=24001)),
            lambda: replace(g, profile=replace(g.profile, minimum_hz=1)),
            lambda: replace(g, hop_samples=13), lambda: replace(g, first_start_sample=ORIGIN-1),
            lambda: replace(g, epoch=replace(g.epoch, channel_ids=("L", "R"))),
            lambda: measure_pitch([0, math.inf], g), lambda: measure_pitch([0, True], g),
            lambda: measure_pitch([2**31], g), lambda: measure_pitch([0]*13, g),
            lambda: measure_pitch([], g, start_sample=ORIGIN+1),
            lambda: measure_pitch([0], g, observed_release_sample_exclusive=ORIGIN),
        )
        for i, check in enumerate(cases):
            with self.subTest(case=i), self.assertRaises(ValueError):
                check()


class DeliveryTests(unittest.TestCase):
    def test_partition_replay_keeps_estimate_and_exact_center_but_changes_delivery(self):
        g = period_grid(24, 8, 16, hop=16, mode="integer")
        tape = [math.cos(math.tau * j / (12 if j < 90 else 8)) for j in range(180)]
        whole = PitchTracker(g).push(ORIGIN, tape)
        rng = random.Random(390039)
        random_ends = []
        end = 0
        while end < len(tape):
            end = min(len(tape), end + rng.randrange(1, 31))
            random_ends.append(end)
        for ends in ([len(tape)], list(range(1, len(tape)+1)), random_ends):
            tracker = PitchTracker(g)
            delivery = []
            for left, right in zip([0, *ends], ends):
                delivery.extend(tracker.push(ORIGIN+left, tape[left:right]))
            self.assertEqual([replace(f, observed_release_sample_exclusive=ORIGIN+len(tape))
                              for f in delivery], list(whole))
            for i, frame in enumerate(delivery):
                relative = frame.ready_sample_exclusive-ORIGIN
                self.assertEqual(relative, i*16+g.frame_length)
                self.assertEqual(frame.observed_release_sample_exclusive, ORIGIN+ends[bisect_left(ends, relative)])
        self.assertEqual(whole[0].selected.seed_lag, 12)
        self.assertEqual(whole[-1].selected.seed_lag, 8)

    def test_rejected_blocks_leave_the_pending_frame_intact(self):
        g = period_grid(7, 2, 4, hop=2)
        tracker = PitchTracker(g)
        pcm = [1, -1]*6
        self.assertEqual(tracker.push(ORIGIN, pcm[:5]), ())
        for start, block in (
            (ORIGIN+6, pcm[5:]),
            (ORIGIN+4, pcm[5:]),
            (ORIGIN+5, [math.nan]),
            (ORIGIN+5, [0]*(MAX_BLOCK_SAMPLES+1)),
            (ORIGIN+5, [0]*400),
        ):
            with self.subTest(start=start, count=len(block)), self.assertRaises(ValueError):
                tracker.push(start, block)
        one, = tracker.push(ORIGIN+5, pcm[5:])
        self.assertEqual(one, measure_pitch(pcm, g, observed_release_sample_exclusive=ORIGIN+12))

    def test_reset_requires_new_epoch_and_discards_pending_data(self):
        g = period_grid(7, 2, 4, hop=4)
        tracker = PitchTracker(g)
        self.assertEqual(tracker.push(ORIGIN, [1, -1, 1, -1, 1, -1]), ())
        with self.assertRaises(ValueError):
            tracker.reset(g)
        shifted = replace(g, epoch=replace(EPOCH, epoch_id="after seek"), first_start_sample=ORIGIN+75)
        tracker.reset(shifted)
        self.assertEqual(tracker.push(ORIGIN+75, [0]*6), ())
        complete, = tracker.push(ORIGIN+81, [0]*6)
        self.assertEqual((complete.status, complete.start_sample, complete.grid.epoch.epoch_id),
                         ("silence", ORIGIN+75, "after seek"))

    def test_empty_delivery_does_not_invent_samples(self):
        g = period_grid(7, 2, 4)
        tracker = PitchTracker(g)
        self.assertEqual(tracker.push(ORIGIN, []), ())
        result, = tracker.push(ORIGIN, [1, -1]*6)
        self.assertEqual((result.available_end_sample_exclusive, result.observed_release_sample_exclusive),
                         (ORIGIN+12, ORIGIN+12))
