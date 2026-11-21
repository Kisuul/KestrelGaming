"""Analytic, boundary, and capture fixtures for the stereo correlation reference."""

from dataclasses import replace
from fractions import Fraction
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/audio-oscilloscope/scripts"))
sys.path.insert(0, str(ROOT / "skills/audio-stereo-correlation/scripts"))
from reference_oscilloscope import CaptureWindow, ScopeAcquisition, ScopeEpoch
from reference_stereo_correlation import _sqrt_binary64, measure_stereo_correlation


EPOCH = ScopeEpoch("take-a", 0, Fraction(48_000), "input-clock", "pre-gain", "FS", ("L", "R"))
TINY = float.fromhex("0x0.0000000000001p-1022")
BIG = sys.float_info.max


def measure(left, right):
    capture = CaptureWindow(EPOCH, 0, (left, right))
    return measure_stereo_correlation(capture, left_channel="L", right_channel="R")


class MeasurementTests(unittest.TestCase):
    def test_proportional_channels_keep_sign_and_show_mono_retention(self):
        left = (1, -1, 1, -1)
        for gain, coefficient, retention in (
            (0.5, 1, Fraction(9, 10)), (-0.5, -1, Fraction(1, 10)),
            (1, 1, Fraction(1)), (-1, -1, Fraction(0)),
        ):
            with self.subTest(gain=gain):
                result = measure(left, [gain * sample for sample in left])
                self.assertEqual((result.coefficient, result.coefficient_status),
                                 (coefficient, "exact_endpoint"))
                self.assertEqual((result.left.rms, result.right.rms), (1, abs(gain)))
                self.assertEqual(result.mono.rms, (1 + gain) / 2)
                self.assertEqual(result.mean_cross_product, gain)
                self.assertEqual(result.mono_retention, retention)
        self.assertEqual(measure(left, [-x for x in left]).mono.status, "exact_zero")

    def test_single_silent_channel_does_not_erase_mono(self):
        signal = (1, -1, 1, -1)
        zeros = (0, 0, 0, 0)
        for left, right, status in (
            (zeros, signal, "left_zero_energy"), (signal, zeros, "right_zero_energy")
        ):
            with self.subTest(status=status):
                result = measure(left, right)
                self.assertIsNone(result.coefficient)
                self.assertEqual(result.coefficient_status, status)
                self.assertEqual(result.mono_retention, Fraction(1, 2))
                self.assertEqual(result.mono.mean_square, Fraction(1, 4))

    def test_both_silent_channels_make_both_ratios_unavailable(self):
        result = measure([0.0, -0.0], [-0.0, 0.0])
        self.assertIsNone(result.coefficient)
        self.assertIsNone(result.mono_retention)
        self.assertEqual(result.coefficient_status, "both_zero_energy")
        for levels in (result.left, result.right, result.mono):
            self.assertEqual((levels.status, levels.rms, levels.mean_square), ("exact_zero", 0, 0))

    def test_cross_product_zero_is_available_with_energy_in_both_channels(self):
        result = measure([1, -1, 1, -1], [1, 1, -1, -1])
        self.assertEqual((result.coefficient, result.coefficient_status), (0, "exact_zero"))
        self.assertEqual((result.left.rms, result.right.rms), (1, 1))
        self.assertEqual(result.mono_retention, Fraction(1, 2))

    def test_raw_dc_and_centered_fluctuations_have_different_signs(self):
        left, right = [0.25, 0.75] * 2, [-0.75, -0.25] * 2
        raw = measure(left, right)
        self.assertEqual((raw.coefficient, raw.mean_cross_product), (-0.6, Fraction(-3, 16)))
        self.assertEqual(raw.mono_retention, Fraction(1, 5))
        centered = measure([x - 0.5 for x in left], [y + 0.5 for y in right])
        self.assertEqual(centered.coefficient, 1)

    def test_nonzero_constant_channels_and_a_single_pair_are_valid(self):
        for length in (1, 16):
            with self.subTest(length=length):
                result = measure([3] * length, [-5] * length)
                self.assertEqual(result.estimator, "raw_zero_lag")
                self.assertEqual((result.coefficient, result.left.rms, result.right.rms), (-1, 3, 5))
                self.assertEqual(result.mono_retention, Fraction(1, 17))

    def test_pooled_window_uses_moments_before_division(self):
        left = [1, -1, 0.125, -0.125]
        right = [1, -1, -0.125, 0.125]
        a = measure(left[:2], right[:2])
        b = measure(left[2:], right[2:])
        pooled = measure(left, right)
        self.assertEqual((a.coefficient, b.coefficient, pooled.coefficient), (1, -1, 63 / 65))
        self.assertEqual(pooled.mono_retention, Fraction(64, 65))
        weighted = (a.frame_count * a.mean_cross_product + b.frame_count * b.mean_cross_product)
        self.assertEqual(pooled.frame_count * pooled.mean_cross_product, weighted)

    def test_swapping_channels_preserves_correlation_and_exchanges_levels(self):
        left, right = [1, 0, 1], [1, -0.25, 0]
        first, swapped = measure(left, right), measure(right, left)
        self.assertEqual(first.left, swapped.right)
        self.assertEqual(first.right, swapped.left)
        self.assertEqual((first.mono, first.coefficient, first.mono_retention),
                         (swapped.mono, swapped.coefficient, swapped.mono_retention))

    def test_ids_and_capture_provenance_survive_the_measurement(self):
        start = 2**130 + 17
        epoch = replace(
            EPOCH, origin_sample=start, channel_ids=("input-B", "unused", "input-A"),
            rate_hz=Fraction(48_000_000, 1001), units="V", tap_id="post-gain",
        )
        capture = CaptureWindow(epoch, start + 2, ((0, 2), (99, 99), (0, 1)))
        result = measure_stereo_correlation(capture, left_channel="input-A", right_channel="input-B")
        self.assertIs(result.epoch, epoch)
        self.assertEqual((result.start_sample, result.end_sample_exclusive), (start + 2, start + 4))
        self.assertEqual((result.frame_count, result.center_sample_twice), (2, 2 * start + 5))
        self.assertEqual((result.left_channel, result.right_channel), ("input-A", "input-B"))
        self.assertEqual((result.left.mean_square, result.right.mean_square), (Fraction(1, 2), 2))

    def test_wrong_capture_or_selectors_raise(self):
        capture = CaptureWindow(EPOCH, 0, ((0,), (0,)))
        for left, right in (("L", "L"), ("X", "R"), ("L", None)):
            with self.subTest(left=left, right=right), self.assertRaises(ValueError):
                measure_stereo_correlation(capture, left_channel=left, right_channel=right)
        with self.assertRaisesRegex(ValueError, "CaptureWindow"):
            measure_stereo_correlation(([0], [0]), left_channel="L", right_channel="R")

    def test_full_capture_support_and_pcm32_bounds(self):
        left = [2**31 - 1, -2**31] * 512
        right = [-2**31, 2**31 - 1] * 512
        result = measure(left, right)
        self.assertEqual((result.frame_count, result.end_sample_exclusive), (1024, 1024))
        self.assertEqual(result.left.mean_square, Fraction((2**31 - 1)**2 + (2**31)**2, 2))
        self.assertEqual(result.mono.mean_square, Fraction(1, 4))
        # Their offset prevents exact proportionality even when the reported float is -1.
        self.assertEqual((result.coefficient, result.coefficient_status), (-1, "rounded_to_endpoint"))


class PrecisionTests(unittest.TestCase):
    def test_representable_cross_product_survives_scaling_and_cancellation(self):
        d = 2**-52
        left, right = [1, 1 + d], [1, -(1 - d)]
        result = measure(left, right)
        self.assertEqual(result.mean_cross_product, Fraction(1, 2**105))
        self.assertEqual(result.coefficient, 2**-105)
        self.assertEqual(result.coefficient_status, "finite")
        self.assertEqual(math.fsum((1 / (1 + d), -(1 - d))), 0.0)

    def test_small_mono_residual_is_evaluated_before_rounding(self):
        gain = 1 - 2**-40
        result = measure([1, -1], [-gain, gain])
        self.assertEqual(result.mono.mean_square, Fraction(1, 2**82))
        self.assertEqual(result.mono.rms, 2**-41)
        self.assertGreater(result.mono_retention, 0)
        rounded = (1 + gain * gain - 2 * gain) / 4
        self.assertEqual(rounded, 0.0)

    def test_power_can_underflow_or_overflow_before_the_norm_fits(self):
        a, b = 2.0**-600, 2.0**600
        result = measure([a, -a], [b, -b])
        self.assertEqual((result.coefficient, result.coefficient_status), (1, "exact_endpoint"))
        self.assertEqual((result.left.rms, result.right.rms), (a, b))
        self.assertEqual(result.left.mean_square, Fraction(1, 2**1200))
        self.assertEqual(result.right.mean_square, 2**1200)
        self.assertEqual(a * a, 0.0)
        self.assertTrue(math.isinf(b * b))

    def test_subnormal_rms_rounding_does_not_decide_channel_availability(self):
        for frame_count, expected in ((3, TINY), (4, 0.0), (5, 0.0)):
            with self.subTest(frame_count=frame_count):
                channel = [TINY] + [0] * (frame_count - 1)
                result = measure(channel, channel)
                self.assertEqual(result.left.mean_square, Fraction(TINY)**2 / frame_count)
                self.assertEqual(result.left.rms, expected)
                self.assertEqual(result.left.status, "finite" if expected else "rounded_to_zero")
                self.assertEqual(result.right, result.left)
                self.assertEqual(result.mono, result.left)
                self.assertEqual((result.coefficient, result.mono_retention), (1, 1))

    def test_subnormal_mono_rounding_does_not_erase_retention(self):
        result = measure([TINY], [0])
        self.assertEqual(result.mono.mean_square, Fraction(TINY)**2 / 4)
        self.assertEqual((result.mono.rms, result.mono.status), (0.0, "rounded_to_zero"))
        self.assertEqual(result.mono_retention, Fraction(1, 2))

    def test_correlation_below_float_range_preserves_its_sign(self):
        for sign in (-1, 1):
            with self.subTest(sign=sign):
                result = measure([BIG, 0], [sign * TINY, BIG])
                self.assertEqual((result.coefficient, result.coefficient_status), (0, "rounded_to_zero"))
                self.assertEqual(math.copysign(1.0, result.coefficient), sign)
                self.assertGreater(sign * result.mean_cross_product, 0)
                self.assertGreater(result.left.rms, 0)
                self.assertGreater(result.right.rms, 0)

    def test_proportionality_uses_exact_moments_even_when_rounded_to_one(self):
        for sign in (-1, 1):
            with self.subTest(sign=sign):
                result = measure([1, 1], [sign, sign * math.nextafter(1.0, 2.0)])
                self.assertEqual((result.coefficient, result.coefficient_status),
                                 (sign, "rounded_to_endpoint"))
                self.assertLess(result.mean_cross_product**2, result.left.mean_square * result.right.mean_square)

    def test_common_full_range_does_not_overflow_the_mono_level(self):
        result = measure([BIG, -BIG], [BIG, -BIG])
        self.assertEqual(result.mono.rms, BIG)
        self.assertEqual(result.mono.mean_square, Fraction(BIG)**2)
        self.assertEqual(result.mono_retention, 1)

    def test_square_root_rounds_to_even_on_both_sides_of_binade_edges(self):
        for lower in (TINY, 2 * TINY, 1.0, math.nextafter(1.0, 2.0), math.nextafter(1.0, 0.0)):
            with self.subTest(lower=lower):
                upper = math.nextafter(lower, math.inf)
                a, b = Fraction(lower), Fraction(upper)
                middle = (a + b) / 2
                step = (b - a) / 4
                self.assertEqual(_sqrt_binary64((middle - step)**2), lower)
                self.assertEqual(_sqrt_binary64(middle**2), float(middle))
                self.assertEqual(_sqrt_binary64((middle + step)**2), upper)


class SignalTests(unittest.TestCase):
    def test_broadband_positive_coefficient_can_hide_narrow_band_mono_loss(self):
        cycles = tuple(math.tau * n / 480 for n in range(480))
        a = tuple(0.75 * math.cos(10 * t) for t in cycles)
        b = tuple(0.25 * math.cos(20 * t) for t in cycles)
        left = [x + y for x, y in zip(a, b)]
        right = [x - y for x, y in zip(a, b)]
        result = measure(left, right)
        self.assertAlmostEqual(result.coefficient, 0.8, delta=2e-15)
        self.assertAlmostEqual(float(result.mono_retention), 0.9, delta=2e-15)
        self.assertAlmostEqual(float(result.mono.mean_square), 0.75**2 / 2, delta=2e-15)

        def amplitude_2khz(wave):
            re = math.fsum(x * math.cos(20 * t) for x, t in zip(wave, cycles))
            im = math.fsum(x * math.sin(20 * t) for x, t in zip(wave, cycles))
            return 2 / len(cycles) * math.hypot(re, im)

        fold = [(x + y) / 2 for x, y in zip(left, right)]
        self.assertAlmostEqual(amplitude_2khz(left), 0.25, delta=2e-15)
        self.assertAlmostEqual(amplitude_2khz(right), 0.25, delta=2e-15)
        self.assertLess(amplitude_2khz(fold), 1e-15)

    def test_equal_and_opposite_delays_agree_for_an_integer_cycle_tone(self):
        for period, expected in ((96, math.sqrt(0.5)), (48, 0), (24, -1)):
            cycle = tuple(math.cos(math.tau * n / period) for n in range(period))
            left = tuple(cycle[n % period] for n in range(480))
            for delay in (-12, 12):
                with self.subTest(period=period, delay=delay):
                    right = tuple(cycle[(n - delay) % period] for n in range(480))
                    self.assertAlmostEqual(measure(left, right).coefficient, expected, delta=2e-15)


class CaptureTests(unittest.TestCase):
    def test_all_callback_partitions_preserve_the_exact_indexed_windows(self):
        origin = 2**53 + 1
        epoch = replace(EPOCH, origin_sample=origin, channel_ids=("R", "L"))
        left = (1, -1, 1, -1, 0.125, -0.125, 0.125, -0.125)
        right = left[:4] + tuple(-sample for sample in left[4:])
        expected = [
            measure_stereo_correlation(
                CaptureWindow(epoch, origin + k, (right[k:k + 4], left[k:k + 4])),
                left_channel="L", right_channel="R",
            ) for k in (0, 2, 4)
        ]
        self.assertEqual([x.coefficient for x in expected], [1, 63 / 65, -1])
        self.assertEqual([x.center_sample_twice for x in expected],
                         [18014398509481989, 18014398509481993, 18014398509481997])
        for mask in range(1 << 7):
            cuts = [0] + [i for i in range(1, 8) if mask & (1 << (i - 1))] + [8]
            acquisition = ScopeAcquisition(epoch, window_frames=4, hop_frames=2, history_frames=4)
            actual = []
            for lo, hi in zip(cuts, cuts[1:]):
                windows = acquisition.ingest(epoch=epoch, start_sample=origin + lo,
                                             planes=(right[lo:hi], left[lo:hi]))
                actual.extend(
                    measure_stereo_correlation(frame, left_channel="L", right_channel="R")
                    for frame in windows
                )
            self.assertEqual(actual, expected, f"partition mask={mask}")

    def test_bad_block_and_epoch_reset_keep_capture_provenance_coherent(self):
        epoch = replace(EPOCH, origin_sample=2**53 + 1)
        start = epoch.origin_sample
        acquisition = ScopeAcquisition(epoch, window_frames=2, hop_frames=1, history_frames=2)
        self.assertEqual(acquisition.ingest(epoch=epoch, start_sample=start, planes=([1], [-1])), ())
        with self.assertRaises(ValueError):
            acquisition.ingest(epoch=epoch, start_sample=start + 1, planes=([8, 9], [8, math.nan]))
        with self.assertRaisesRegex(ValueError, "gap"):
            acquisition.ingest(epoch=epoch, start_sample=start + 2, planes=([8], [8]))
        (before,) = acquisition.ingest(epoch=epoch, start_sample=start + 1, planes=([-1], [1]))
        measured_before = measure_stereo_correlation(before, left_channel="L", right_channel="R")
        self.assertEqual(measured_before.coefficient, -1)

        fresh = replace(epoch, epoch_id="take-b")
        acquisition.reset_epoch(fresh)
        self.assertEqual(acquisition.ingest(epoch=fresh, start_sample=start, planes=([1], [1])), ())
        (after,) = acquisition.ingest(epoch=fresh, start_sample=start + 1, planes=([-1], [-1]))
        measured_after = measure_stereo_correlation(after, left_channel="L", right_channel="R")
        self.assertEqual(measured_after.coefficient, 1)
        self.assertEqual(measured_after.start_sample, measured_before.start_sample)
        self.assertEqual((measured_before.epoch.epoch_id, measured_after.epoch.epoch_id),
                         ("take-a", "take-b"))


if __name__ == "__main__":
    unittest.main()
