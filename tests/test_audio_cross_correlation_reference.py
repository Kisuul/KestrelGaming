"""Analytic, range, and acquisition fixtures for integer-lag correlation."""

from dataclasses import replace
from fractions import Fraction as F
from itertools import product
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
for skill in ("audio-oscilloscope", "audio-stereo-correlation", "audio-cross-correlation"):
    sys.path.insert(0, str(ROOT / "skills" / skill / "scripts"))

from reference_cross_correlation import LagProfile, correlate_captures
from reference_oscilloscope import CaptureWindow, ScopeAcquisition, ScopeEpoch
from reference_stereo_correlation import measure_stereo_correlation


RATE = 48_000
X_EPOCH = ScopeEpoch("take-a", 0, F(RATE), "sample-clock", "probe", "V", ("X",))
Y_EPOCH = replace(X_EPOCH, tap_id="response", units="FS", channel_ids=("Y",))
BIG = sys.float_info.max
TINY = math.ulp(0.0)


def measure(x, y, *, sx=0, sy=0, bounds=None, minimum=1, mode="raw", rule="positive",
            floors=(0, 0)):
    if bounds is None:
        bounds = (sy - sx + 1 - len(x), sy - sx + len(y) - 1)
    profile = LagProfile(bounds, minimum, mode, rule, *floors)
    return correlate_captures(
        CaptureWindow(X_EPOCH, sx, (x,)), CaptureWindow(Y_EPOCH, sy, (y,)), profile,
        reference_channel="X", measurement_channel="Y",
    )


class ClockAndOverlap(unittest.TestCase):
    def test_unequal_delayed_impulse_has_positive_lag_and_declared_support(self):
        x, y = [0, 0, 2, 0, 0, 0, 0], [0] * 6 + [3] + [0] * 4
        result = measure(x, y)
        (peak,) = result.peaks
        self.assertEqual(result.status, "selected")
        self.assertEqual(result.evaluated_delay_bounds, (-6, 10))
        self.assertEqual(len(result.curve), 17)
        self.assertEqual((peak.local_lag, peak.delay_samples, peak.delay_seconds), (4, 4, F(1, 12_000)))
        self.assertEqual((peak.reference_interval, peak.measurement_interval), ((0, 7), (4, 11)))
        self.assertEqual((peak.pair_count, peak.score.value, peak.raw_sum), (7, 6, 6))
        self.assertFalse(result.on_search_edge)

    def test_shifted_origins_reverse_local_lag_and_keep_delay_exact(self):
        sx, sy = 2**60 + 1, 2**60 + 6
        result = measure([0, 0, 1, 0], [1, 0, 0, 0], sx=sx, sy=sy, bounds=(0, 4))
        self.assertEqual(result.evaluated_delay_bounds, (2, 4))
        (peak,) = result.peaks
        self.assertEqual((peak.local_lag, peak.delay_samples, peak.delay_seconds), (-2, 3, F(1, 16_000)))
        self.assertEqual((peak.reference_interval, peak.measurement_interval), ((sx + 2, sx + 4), (sy, sy + 2)))
        self.assertEqual(peak.pair_count, 2)

    def test_selected_planes_keep_each_tap_units_epoch_and_rational_rate(self):
        origin = 2**132 + 5
        clock = replace(X_EPOCH, origin_sample=origin, rate_hz=F(48_000_000, 1001))
        x_epoch = replace(clock, channel_ids=("unused", "X"))
        y_epoch = replace(clock, tap_id="measurement", units="Pa", channel_ids=("Y", "aux"))
        x = CaptureWindow(x_epoch, origin + 2, ((40, 41, 42), (1, 0, 0)))
        y = CaptureWindow(y_epoch, origin + 7, ((0, 2, 0), (30, 31, 32)))
        result = correlate_captures(x, y, LagProfile((4, 7), 1), reference_channel="X", measurement_channel="Y")
        self.assertIs(result.reference_epoch, x_epoch)
        self.assertIs(result.measurement_epoch, y_epoch)
        self.assertEqual((result.reference_channel, result.measurement_channel), ("X", "Y"))
        self.assertEqual((result.reference_interval, result.measurement_interval),
                         ((origin + 2, origin + 5), (origin + 7, origin + 10)))
        (peak,) = result.peaks
        self.assertEqual((peak.local_lag, peak.delay_samples, peak.raw_sum), (1, 6, 2))
        self.assertEqual(peak.delay_seconds, 6 / clock.rate_hz)

    def test_swapping_roles_negates_lag_and_delay_and_swaps_intervals(self):
        x, y = [1, -2, 3], [0, 3, -1, 2, 1]
        forward = measure(x, y, sx=7, sy=12, mode="cosine")
        reverse = measure(y, x, sx=12, sy=7, mode="cosine")
        for a, b in zip(forward.curve, reversed(reverse.curve)):
            self.assertEqual((a.local_lag, a.delay_samples), (-b.local_lag, -b.delay_samples))
            self.assertEqual(a.reference_interval, b.measurement_interval)
            self.assertEqual(a.measurement_interval, b.reference_interval)
            self.assertEqual((a.raw_sum, a.score, a.pair_count), (b.raw_sum, b.score, b.pair_count))
            self.assertEqual((a.reference_power, a.measurement_power), (b.measurement_power, b.reference_power))

    def test_known_offset_in_pcm_moves_peak_by_the_inserted_samples(self):
        x = [0, 0, 2, 0, 0, 0, 0]
        y = [0] * 6 + [3] + [0] * 4
        (before,) = measure(x, y).peaks
        (after,) = measure(x, [0] * 3 + y).peaks
        self.assertEqual(after.delay_samples - before.delay_samples, 3)
        self.assertEqual(before.score, after.score)

    def test_one_sample_capture_scores_all_feasible_single_pairs(self):
        result = measure([2], [1, -2, 4], rule="absolute")
        self.assertEqual([(r.local_lag, r.pair_count, r.raw_sum) for r in result.curve],
                         [(0, 1, 2), (1, 1, -4), (2, 1, 8)])
        self.assertEqual(result.peaks[0].delay_samples, 2)
        self.assertTrue(result.on_search_edge)

    def test_linear_end_event_wrap_case_has_negative_lag(self):
        result = measure([0, 0, 0, 1], [1, 0, 0, 0])
        self.assertEqual([row.raw_sum for row in result.curve], [1, 0, 0, 0, 0, 0, 0])
        self.assertEqual(result.peaks[0].local_lag, -3)

    def test_inclusive_search_reports_peak_at_edge_and_clipped_bounds(self):
        result = measure([0, 2, 0], [0, 0, 3, 0], bounds=(-200, 1))
        self.assertEqual(result.profile.delay_bounds, (-200, 1))
        self.assertEqual(result.evaluated_delay_bounds, (-2, 1))
        self.assertEqual(result.peaks[0].delay_samples, 1)
        self.assertTrue(result.on_search_edge)

    def test_empty_intersection_is_distinct_from_an_ineligible_curve(self):
        empty = measure([1, 0], [0, 1], bounds=(4, 6))
        self.assertEqual((empty.status, empty.curve, empty.peaks), ("empty_search", (), ()))
        self.assertIsNone(empty.evaluated_delay_bounds)
        self.assertFalse(empty.on_search_edge)
        result = measure([1, 0], [0, 1], minimum=3)
        self.assertEqual((result.status, len(result.curve), result.peaks), ("no_eligible_peak", 3, ()))


class ScoringAndSelection(unittest.TestCase):
    def test_raw_and_mean_use_the_same_local_pairs(self):
        x, y = [1, 2, 3], [4, 5]
        raw = measure(x, y, bounds=(-1, -1)).curve[0]
        mean = measure(x, y, bounds=(-1, -1), mode="mean_product").curve[0]
        self.assertEqual((raw.raw_sum, mean.raw_sum), (23, 23))
        self.assertEqual((raw.score.value, mean.score.value), (23, F(23, 2)))
        self.assertEqual((mean.reference_power, mean.measurement_power), (F(13, 2), F(41, 2)))

    def test_absolute_rule_keeps_an_inverted_impulse_with_negative_sign(self):
        x, y = [0, 0, 2, 0, 0, 0, 0], [0] * 6 + [-3] + [0] * 4
        self.assertEqual(measure(x, y).status, "no_eligible_peak")
        (peak,) = measure(x, y, rule="absolute").peaks
        self.assertEqual((peak.local_lag, peak.score.value, peak.score.sign), (4, -6, -1))
        (reverse,) = measure(y, x, rule="absolute").peaks
        self.assertEqual((reverse.local_lag, reverse.score.sign), (-4, -1))

    def test_overlap_gate_keeps_short_rows_and_finds_the_supported_peak(self):
        x, y = [3, -1, 4, -2, 1, 5, -4, 2], [2, -3, 3, -1, 4, -1, 1, 5]
        result = measure(x, y, minimum=6, mode="cosine", rule="absolute")
        for row in (result.curve[0], result.curve[-1]):
            self.assertEqual((row.pair_count, row.score.value, row.eligibility), (1, 1, "insufficient_pairs"))
        (peak,) = result.peaks
        self.assertEqual((peak.local_lag, peak.pair_count), (2, 6))
        self.assertAlmostEqual(peak.score.value, 0.991201182589, delta=5e-13)

    def test_fixed_support_periodic_peaks_remain_tied_and_keep_polarity(self):
        p = [1, 0, -1, 0]
        x, y = (p * 8)[8:24], [p[(n - 1) % 4] for n in range(32)]
        options = dict(sx=8, bounds=(-6, 6), minimum=16)
        positive = measure(x, y, **options)
        absolute = measure(x, y, rule="absolute", **options)
        self.assertTrue(all(row.pair_count == 16 and row.reference_interval == (8, 24) for row in absolute.curve))
        self.assertEqual(positive.status, "ambiguous")
        self.assertEqual([row.delay_samples for row in positive.peaks], [-3, 1, 5])
        self.assertEqual([row.delay_samples for row in absolute.peaks], [-5, -3, -1, 1, 3, 5])
        self.assertEqual([row.score.sign for row in absolute.peaks], [-1, 1, -1, 1, -1, 1])

    def test_strongest_reflection_keeps_the_earlier_competing_arrival(self):
        x, y = [0] * 32, [0] * 32
        x[4], y[7], y[13] = 1, 0.25, 1
        result = measure(x, y, bounds=(0, 12))
        self.assertEqual([(p.delay_samples, p.raw_sum) for p in result.peaks], [(9, 1)])
        self.assertEqual([(p.delay_samples, p.raw_sum) for p in result.next_best], [(3, F(1, 4))])

    def test_two_channel_power_floors_use_paired_units_and_include_equality(self):
        x, y = [2, 0], [1, 0]
        a = measure(x, y, bounds=(0, 0), floors=(2, F(1, 2)))
        b = measure(x, y, bounds=(0, 0), floors=(2, F(3, 4)))
        c = measure(x, y, bounds=(0, 0), floors=(3, F(1, 2)))
        self.assertEqual(a.status, "selected")
        self.assertEqual((a.curve[0].reference_power, a.curve[0].measurement_power), (2, F(1, 2)))
        self.assertEqual([v.curve[0].eligibility for v in (b, c)], ["below_level", "below_level"])
        self.assertEqual([v.curve[0].score.value for v in (b, c)], [2, 2])

    def test_raw_silence_and_normalized_missing_score_have_distinct_states(self):
        raw = measure([1, 0], [0, 0], bounds=(0, 0))
        cosine = measure([1, 0], [0, 0], bounds=(0, 0), mode="cosine")
        self.assertEqual((raw.curve[0].raw_sum, raw.curve[0].score.value, raw.curve[0].eligibility),
                         (0, 0, "zero_power"))
        self.assertIsNone(cosine.curve[0].score)
        self.assertEqual((raw.status, cosine.status), ("no_eligible_peak", "no_eligible_peak"))

    def test_zero_cross_sum_with_positive_energy_is_a_measured_zero(self):
        result = measure([1, 0], [0, 1], bounds=(0, 0), mode="cosine")
        (row,) = result.curve
        self.assertEqual((row.eligibility, row.score.value, row.score.status), ("eligible", 0.0, "exact_zero"))
        self.assertEqual(result.status, "no_eligible_peak")

    def test_pearson_centers_each_overlap_on_a_large_dc_offset(self):
        base = float(2**40)
        x, y = [base + j for j in (-2, -1, 1, 2)], [base + j for j in (2, 1, -1, -2)]
        centered = measure(x, y, bounds=(0, 0), mode="pearson", rule="absolute")
        (peak,) = centered.peaks
        self.assertEqual((peak.reference_power, peak.measurement_power), (F(5, 2), F(5, 2)))
        self.assertEqual((peak.score.value, peak.score.status), (-1.0, "exact_endpoint"))
        below = measure(x, y, bounds=(0, 0), mode="pearson", rule="absolute", floors=(3, 1))
        self.assertEqual(below.curve[0].eligibility, "below_level")
        self.assertGreater(measure(x, y, bounds=(0, 0), mode="cosine").curve[0].score.value, 0)

    def test_pearson_reports_missing_constant_vector_and_two_pair_degeneracy(self):
        constant = measure([1, 1], [1, 2], bounds=(0, 0), mode="pearson")
        short = measure([7, 3], [2, 4], bounds=(0, 0), minimum=3, mode="pearson")
        self.assertIsNone(constant.curve[0].score)
        self.assertEqual(constant.curve[0].eligibility, "zero_power")
        self.assertEqual((short.curve[0].score.value, short.curve[0].eligibility), (-1.0, "insufficient_pairs"))

    def test_zero_lag_cosine_matches_the_stereo_correlation_skill(self):
        epoch = replace(X_EPOCH, channel_ids=("X", "Y"))
        frame = CaptureWindow(epoch, 0, ((1, -2, 3, 4), (2, 3, -4, 5)))
        result = correlate_captures(frame, frame, LagProfile((0, 0), 4, "cosine"),
                                    reference_channel="X", measurement_channel="Y")
        baseline = measure_stereo_correlation(frame, left_channel="X", right_channel="Y")
        (row,) = result.curve
        self.assertEqual((row.score.value, row.score.status), (baseline.coefficient, baseline.coefficient_status))
        self.assertEqual(row.raw_sum / row.pair_count, baseline.mean_cross_product)


class ExactArithmetic(unittest.TestCase):
    def test_curve_equals_exact_pair_enumeration_for_all_small_record_lengths(self):
        x, y = (-1.25, 2, 0, 3.5, -0.125), (1, -2.25, 4, 0, 0.5)
        for nx, ny in product(range(1, 6), repeat=2):
            result = measure(x[:nx], y[:ny], mode="pearson")
            pairs = [(j - i, F(x[i]), F(y[j])) for i in range(nx) for j in range(ny)]
            self.assertEqual(sum(row.pair_count for row in result.curve), nx * ny)
            for row in result.curve:
                actual_pairs = [(a, b) for k, a, b in pairs if k == row.local_lag]
                left, right = zip(*actual_pairs)
                count = len(left)
                lx, ry = (tuple(q - sum(v) / count for q in v) for v in (left, right))
                power_x, power_y = sum(a*a for a in lx), sum(b*b for b in ry)
                dot = sum(a*b for a, b in zip(lx, ry))
                expected = dot * abs(dot) / (power_x * power_y) if power_x and power_y else None
                self.assertEqual(row.raw_sum, sum(a*b for a, b in actual_pairs))
                self.assertEqual((row.reference_power, row.measurement_power), (power_x / count, power_y / count))
                self.assertEqual(row.score.rank_value if row.score else None, expected)

    def test_scaled_inversion_remains_exact_through_huge_and_quiet_inputs(self):
        for scale in (2.0**600, 2.0**-600, TINY):
            x = [scale, -2*scale, 3*scale]
            (row,) = measure(x, [-a for a in x], bounds=(0, 0), mode="cosine", rule="absolute").peaks
            self.assertEqual(row.raw_sum, -14 * F(scale)**2)
            self.assertEqual((row.score.rank_value, row.score.value, row.score.status),
                             (-1, -1.0, "exact_endpoint"))

    def test_exact_score_ranks_two_lags_that_both_round_to_one(self):
        result = measure([1, 0], [1, 2.0**-30, 1, 0], bounds=(0, 2), minimum=2, mode="cosine")
        self.assertEqual(result.status, "selected")
        (winner,) = result.peaks
        (runner,) = result.next_best
        self.assertEqual((winner.local_lag, runner.local_lag), (2, 0))
        self.assertEqual(runner.score.rank_value, F(2**60, 2**60 + 1))
        self.assertEqual((winner.score.value, runner.score.value), (1.0, 1.0))
        self.assertEqual((winner.score.status, runner.score.status), ("exact_endpoint", "rounded_to_endpoint"))

    def test_sqrt_does_not_round_squared_ratio_before_the_coefficient(self):
        epsilon = 2.0**-600
        (peak,) = measure([1, 0], [epsilon, 1], bounds=(0, 0), mode="cosine").peaks
        self.assertEqual(float(peak.score.rank_value), 0.0)
        self.assertEqual((peak.score.value, peak.score.status), (epsilon, "finite"))

    def test_signed_coefficient_underflow_still_selects_an_exact_nonzero_peak(self):
        (peak,) = measure([BIG, 0], [-TINY, BIG], bounds=(0, 0), mode="cosine", rule="absolute").peaks
        self.assertEqual(peak.raw_sum, -F(BIG) * F(TINY))
        self.assertEqual((peak.score.value, peak.score.sign, peak.score.status), (0.0, -1, "rounded_to_zero"))
        self.assertEqual(math.copysign(1, peak.score.value), -1)


class CaptureValidation(unittest.TestCase):
    def test_callback_partitions_yield_identical_delay_curves(self):
        x, y = (1, 0, -1, 3, 0, 4, 0, 0), (0, 0, 1, 0, -1, 3, 0, 4)
        epoch = replace(X_EPOCH, origin_sample=2**53 + 1, channel_ids=("X", "Y"))
        start = epoch.origin_sample
        profile = LagProfile((-4, 4), 4, "pearson")
        expected = CaptureWindow(epoch, start, (x, y))
        exact = correlate_captures(expected, expected, profile, reference_channel="X", measurement_channel="Y")
        for mask in range(1 << 7):
            cuts = [0] + [k for k in range(1, 8) if mask & (1 << (k - 1))] + [8]
            producer = ScopeAcquisition(epoch, window_frames=8, hop_frames=8, history_frames=8)
            windows = []
            for lo, hi in zip(cuts, cuts[1:]):
                windows.extend(producer.ingest(epoch=epoch, start_sample=start + lo, planes=(x[lo:hi], y[lo:hi])))
            (frame,) = windows
            observed = correlate_captures(frame, frame, profile, reference_channel="X", measurement_channel="Y")
            self.assertEqual(observed, exact)

    def test_clock_rate_epoch_and_origin_incompatibilities_are_rejected(self):
        x = CaptureWindow(X_EPOCH, 0, ((1, 0),))
        for options in ({"epoch_id": "different"}, {"clock_domain": "other-device"},
                        {"rate_hz": F(RATE * 1001, 1000)}, {"origin_sample": 1}):
            y = CaptureWindow(replace(Y_EPOCH, **options), 1, ((1, 0),))
            with self.subTest(options=options), self.assertRaisesRegex(ValueError, "share"):
                correlate_captures(x, y, LagProfile((-5, 5), 1), reference_channel="X", measurement_channel="Y")

    def test_shared_capture_rejects_nonfinite_pcm(self):
        for bad in (math.nan, math.inf, -math.inf):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                CaptureWindow(Y_EPOCH, 0, ((1, bad),))

    def test_invalid_profiles_and_selectors_fail_before_measurement(self):
        profile = LagProfile((0, 0), 1)
        for params in ({"delay_bounds": (1, 0)}, {"delay_bounds": (False, 1)},
                       {"delay_bounds": (0, 1.5)}, {"delay_bounds": [0, 1]},
                       {"minimum_pairs": 0}, {"minimum_pairs": True}, {"score_mode": "scaled"},
                       {"peak_rule": "max"}, {"reference_power_floor": math.nan},
                       {"measurement_power_floor": -1}, {"measurement_power_floor": True}):
            with self.subTest(params=params), self.assertRaises(ValueError):
                replace(profile, **params)
        x, y = CaptureWindow(X_EPOCH, 0, ((1,),)), CaptureWindow(Y_EPOCH, 0, ((1,),))
        for a, b, label in ((x, y, "missing"), (x, y, None), (x.planes, y, "Y")):
            with self.subTest(label=label), self.assertRaises(ValueError):
                correlate_captures(a, b, profile, reference_channel="X", measurement_channel=label)


if __name__ == "__main__":
    unittest.main()
