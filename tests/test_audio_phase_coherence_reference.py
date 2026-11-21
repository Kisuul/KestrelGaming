"""Measurement and integration fixtures for paired Welch phase and coherence."""

from dataclasses import replace
from fractions import Fraction as F
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
for skill in ("audio-oscilloscope", "audio-phase-coherence", "audio-power-spectral-density"):
    sys.path.insert(0, str(ROOT / "skills" / skill / "scripts"))

from reference_oscilloscope import CaptureWindow, ScopeAcquisition, ScopeEpoch
from reference_phase_coherence import WelchProfile, analyze_phase_coherence
from reference_psd import welch_mean


RATE = 48_000
EPOCH = ScopeEpoch("take-a", 0, F(RATE), "capture-clock", "post-input", "FS", ("X", "Y"))
BIG = sys.float_info.max
TINY = float.fromhex("0x0.0000000000001p-1022")
PAIR = WelchProfile((1, 1), 2, 2)


def measure(x, y, profile=PAIR):
    return analyze_phase_coherence(CaptureWindow(EPOCH, 0, (x, y)), profile,
                                   reference_channel="X", measurement_channel="Y")


class WelchMeasurements(unittest.TestCase):
    def test_single_segment_identity_is_reported_as_warm_up(self):
        profile = WelchProfile((1, 1, 1, 1), 2, 8)
        for length, starts, used_end in ((3, (), None), (4, (0,), 4), (5, (0,), 4)):
            result = measure([1] * length, [1] * length, profile)
            with self.subTest(length=length):
                self.assertEqual((result.segment_starts, result.used_end_sample_exclusive), (starts, used_end))
                self.assertEqual(result.segment_count, len(starts))
                self.assertTrue(result.warming_up)
                self.assertEqual(result.bins, ())

    def test_silent_channel_keeps_powers_and_marks_the_ratio_unavailable(self):
        for value in measure([1, 0, 1, 0], [0, 0, 0, 0]).bins:
            self.assertEqual(value.reference_density, F(1, 2 * RATE))
            self.assertEqual(value.measurement_density, 0)
            self.assertEqual((value.cross_density_real, value.cross_density_imag), (0, 0))
            self.assertIsNone(value.magnitude_squared_coherence)
            self.assertIsNone(value.phase_radians)
            self.assertEqual((value.status, value.energized_pairs), ("zero_auto_power", 0))

    def test_silence_on_both_channels_is_valid_data(self):
        for value in measure([0] * 4, [0] * 4).bins:
            self.assertEqual((value.reference_density, value.measurement_density), (0, 0))
            self.assertEqual(value.status, "zero_auto_power")
            self.assertIsNone(value.magnitude_squared_coherence)

    def test_pool_complex_products_before_magnitude_or_phase(self):
        for value in measure([1, 0, 1, 0], [1, 0, -1, 0]).bins:
            self.assertEqual((value.reference_density, value.measurement_density), (F(1, 2 * RATE),) * 2)
            self.assertEqual(value.magnitude_squared_coherence, 0)
            self.assertIsNone(value.phase_radians)
            self.assertEqual((value.status, value.energized_pairs), ("zero_cross_density", 2))

    def test_varying_positive_gain_reduces_coherence_without_changing_phase(self):
        for value in measure([1, 0, 1, 0], [1, 0, 3, 0]).bins:
            self.assertEqual(value.magnitude_squared_coherence, F(4, 5))
            self.assertEqual(value.phase_radians, 0)
            self.assertEqual(value.measurement_density, 5 * value.reference_density)
            self.assertEqual(value.cross_density_real, 2 * value.reference_density)

    def test_inversion_has_unit_coherence_and_cancels_in_mono(self):
        x = (1, 0, 1, 0)
        y = tuple(-sample for sample in x)
        self.assertEqual(tuple((a + b) / 2 for a, b in zip(x, y)), (0, 0, 0, 0))
        for value in measure(x, y).bins:
            self.assertEqual(value.magnitude_squared_coherence, 1)
            self.assertEqual(value.phase_radians, math.pi)
            self.assertEqual((value.cross_density_real, value.cross_density_imag), (-value.reference_density, 0))

    def test_even_one_sided_density_preserves_complex_interior_and_real_endpoints(self):
        result = measure([1, 0, 1, 0], [0, 1, 0, 1], WelchProfile((1, 1), 2, 4))
        low, middle, high = result.bins
        self.assertEqual(tuple(b.frequency_hz for b in result.bins), (0, F(RATE, 4), F(RATE, 2)))
        self.assertEqual(tuple(b.reference_density for b in result.bins), (F(1, 2 * RATE), F(1, RATE), F(1, 2 * RATE)))
        self.assertEqual((low.cross_density_real, low.cross_density_imag, low.phase_radians),
                         (F(1, 2 * RATE), 0, 0))
        self.assertEqual((middle.cross_density_real, middle.cross_density_imag, middle.phase_radians),
                         (0, -F(1, RATE), -math.pi / 2))
        self.assertEqual((high.cross_density_real, high.cross_density_imag, high.phase_radians),
                         (-F(1, 2 * RATE), 0, math.pi))

    def test_odd_last_bin_gets_the_interior_density_factor(self):
        result = measure([1, 0, 1, 0], [0, 1, 0, 1], WelchProfile((1, 1), 2, 5))
        self.assertEqual([b.reference_density for b in result.bins], [F(1, 2 * RATE), F(1, RATE), F(1, RATE)])
        highest = result.bins[-1]
        self.assertEqual(highest.frequency_hz, F(2 * RATE, 5))
        self.assertEqual(highest.magnitude_squared_coherence, 1)
        self.assertAlmostEqual(highest.phase_radians, -4 * math.pi / 5, delta=1e-15)
        self.assertLess(highest.cross_density_imag, 0)

    def test_detrend_is_per_segment_before_taper(self):
        samples = [5, 7, 11, 13]
        profile = WelchProfile((1, 2), 2, 2, "mean")
        dc, nyquist = measure(samples, samples, profile).bins
        self.assertEqual((dc.reference_density, nyquist.reference_density), (F(1, 5 * RATE), F(9, 5 * RATE)))
        retained = measure(samples, samples, replace(profile, detrend="none")).bins
        self.assertEqual(retained[0].reference_density, F(19**2 + 37**2, 10 * RATE))

    def test_window_with_zero_sum_and_positive_energy_is_valid_for_density(self):
        dc, nyquist = measure([1] * 4, [1] * 4, WelchProfile((1, -1), 2, 2)).bins
        self.assertEqual(dc.status, "zero_auto_power")
        self.assertEqual(nyquist.reference_density, F(2, RATE))
        self.assertEqual(nyquist.magnitude_squared_coherence, 1)

    def test_overlap_density_agrees_with_the_existing_psd_reference(self):
        profile = WelchProfile((0.25, 1, 0.75), 2, 5, "mean")
        x = [0.25, -1, 0.5, 1, 1.25, -0.25, 0.75, 99]
        y = [1, 0.5, -1.5, 1, 0.25, 0.5, -0.25, -87]
        result = measure(x, y, profile)
        for samples, field in ((x, "reference_density"), (y, "measurement_density")):
            frequencies, densities, count = welch_mean(
                samples, profile.window, RATE, hop=2, nfft=5, detrend_mean=True,
            )
            self.assertEqual(result.segment_starts, (0, 2, 4))
            self.assertEqual(result.segment_count, count)
            self.assertEqual([float(b.frequency_hz) for b in result.bins], frequencies)
            for b, density in zip(result.bins, densities):
                self.assertAlmostEqual(float(getattr(b, field)), density, delta=2e-20)


class PhaseAndRange(unittest.TestCase):
    def test_phase_wrap_uses_the_pooled_complex_direction(self):
        x = [1, 0, 0, 0] * 2
        slope = math.tan(math.pi / 180)
        y = [-1, -slope, 0, 0, -1, slope, 0, 0]
        value = measure(x, y, WelchProfile((1,) * 4, 4, 4)).bins[1]
        self.assertEqual(value.phase_radians, math.pi)
        self.assertEqual(value.cross_density_imag, 0)
        self.assertEqual(value.magnitude_squared_coherence, 1 / (1 + F(slope)**2))

    def test_delayed_measurement_phase_sign_and_channel_swap(self):
        wave = tuple(math.cos(math.tau * j / 16) for j in range(16))
        x = wave * 16
        profile = WelchProfile((1,) * 64, 64, 64)
        for delay in (4, -4):
            with self.subTest(delay=delay):
                y = [wave[(j - delay) % len(wave)] for j in range(len(x))]
                bin_ab = measure(x, y, profile).bins[4]
                bin_ba = measure(y, x, profile).bins[4]
                self.assertEqual(bin_ab.frequency_hz, 3000)
                self.assertEqual((bin_ab.magnitude_squared_coherence, bin_ba.magnitude_squared_coherence), (1, 1))
                self.assertAlmostEqual(bin_ab.phase_radians, -math.copysign(math.pi / 2, delay), delta=1e-15)
                self.assertEqual(bin_ab.cross_density_real, bin_ba.cross_density_real)
                self.assertEqual(bin_ab.cross_density_imag, -bin_ba.cross_density_imag)

    def test_delay_across_a_segment_boundary_changes_measured_coherence(self):
        x = [int(j == 3) for j in range(9)]
        y = [int(j == 4) for j in range(9)]
        profile = WelchProfile((1,) * 4, 4, 4)
        original = measure(x, y, profile)
        repaired = measure(x[:8], y[1:9], profile)
        for a, b in zip(original.bins, repaired.bins):
            self.assertGreater(a.reference_density, 0)
            self.assertGreater(a.measurement_density, 0)
            self.assertEqual((a.magnitude_squared_coherence, a.phase_radians, a.energized_pairs), (0, None, 0))
            self.assertEqual((b.magnitude_squared_coherence, b.phase_radians, b.energized_pairs), (1, 0, 1))

    def test_finite_maximum_pcm_does_not_overflow_before_or_after_dft(self):
        self.assertTrue(math.isinf(BIG + BIG))
        dc, nyquist = measure([BIG] * 4, [BIG] * 4).bins
        expected = 2 * F(BIG)**2 / RATE
        self.assertEqual((dc.reference_density, dc.measurement_density, dc.cross_density_real), (expected,) * 3)
        self.assertEqual((dc.magnitude_squared_coherence, dc.phase_radians), (1, 0))
        self.assertEqual(nyquist.status, "zero_auto_power")

    def test_smallest_pcm_power_stays_positive_through_normalization(self):
        dc = measure([TINY] * 4, [-TINY] * 4).bins[0]
        self.assertEqual(dc.reference_density, 2 * F(TINY)**2 / RATE)
        self.assertEqual(float(dc.reference_density), 0)
        self.assertEqual((dc.magnitude_squared_coherence, dc.phase_radians), (1, math.pi))

    def test_mixed_range_retains_the_nonzero_cross_term_and_ratio(self):
        dc = measure([BIG, BIG, TINY, TINY], [0, 0, BIG, BIG]).bins[0]
        expected = F(TINY)**2 / (F(BIG)**2 + F(TINY)**2)
        self.assertEqual(dc.cross_density_real, F(BIG) * F(TINY) / RATE)
        self.assertGreater(dc.magnitude_squared_coherence, 0)
        self.assertEqual(dc.magnitude_squared_coherence, expected)
        self.assertEqual(float(dc.magnitude_squared_coherence), 0)
        self.assertEqual((dc.phase_radians, dc.status), (0, "defined"))

    def test_phase_branch_is_canonical_when_extreme_ratio_rounds_to_negative_pi(self):
        x = [1, 0, 0, 0] * 2
        y = [-BIG, TINY, 0, 0] * 2
        value = measure(x, y, WelchProfile((1,) * 4, 4, 4)).bins[1]
        self.assertLess(value.cross_density_imag, 0)
        self.assertEqual(value.phase_radians, math.pi)

    def test_extreme_nonzero_window_gain_cancels_in_physical_density(self):
        x, y = [0.5, 1.5, -0.25, 0.125], [1, -1.5, 0.5, 1.5]
        expected = measure(x, y).bins
        for gain in (TINY, BIG):
            with self.subTest(gain=gain):
                self.assertEqual(measure(x, y, WelchProfile((gain, gain), 2, 2)).bins, expected)


class CaptureAndValidation(unittest.TestCase):
    def test_incomplete_tail_cannot_change_pooled_products(self):
        profile = WelchProfile((1, 1, 1), 2, 5)
        x, y = [1, 0, 1, 2, 3], [0, 1, -1, -2, 3]
        exact = measure(x, y, profile)
        with_tail = measure(x + [BIG], y + [-BIG], profile)
        self.assertEqual(exact.bins, with_tail.bins)
        self.assertEqual(with_tail.segment_starts, (0, 2))
        self.assertEqual((with_tail.used_end_sample_exclusive, with_tail.end_sample_exclusive), (5, 6))
        self.assertFalse(with_tail.warming_up)

    def test_channel_selection_and_support_use_exact_capture_provenance(self):
        origin = 2**130 + 17
        epoch = replace(EPOCH, origin_sample=origin, rate_hz=F(48_000_000, 1001),
                        channel_ids=("Y", "ignored", "X"), tap_id="post-fader", units="V")
        capture = CaptureWindow(epoch, origin + 5, ((0, 1, 0, 1), (90, 91, 92, 93), (1, 0, 1, 0)))
        result = analyze_phase_coherence(capture, WelchProfile((1, 1), 2, 4),
                                         reference_channel="X", measurement_channel="Y")
        self.assertIs(result.epoch, epoch)
        self.assertEqual((result.reference_channel, result.measurement_channel), ("X", "Y"))
        self.assertEqual(result.segment_starts, (origin + 5, origin + 7))
        self.assertEqual((result.start_sample, result.used_end_sample_exclusive), (origin + 5, origin + 9))
        self.assertEqual(result.bins[1].frequency_hz, epoch.rate_hz / 4)
        self.assertEqual(result.bins[1].cross_density_imag, -1 / epoch.rate_hz)

    def test_callback_partitions_leave_the_aligned_capture_and_bins_unchanged(self):
        x, y = (1, 0, 1, 2, 3, -1, 4, 0), (0, 1, -1, -2, 3, 0, -1, 1)
        start = 2**53 + 1
        epoch = replace(EPOCH, origin_sample=start)
        profile = WelchProfile((1, 2, 1), 2, 4)
        exact = analyze_phase_coherence(CaptureWindow(epoch, start, (x, y)), profile,
                                        reference_channel="X", measurement_channel="Y")
        for mask in range(1 << 7):
            cuts = [0] + [j for j in range(1, 8) if mask & (1 << (j - 1))] + [8]
            acquisition = ScopeAcquisition(epoch, window_frames=8, hop_frames=8, history_frames=8)
            complete = []
            for lo, hi in zip(cuts, cuts[1:]):
                complete.extend(acquisition.ingest(epoch=epoch, start_sample=start + lo, planes=(x[lo:hi], y[lo:hi])))
            (capture,) = complete
            actual = analyze_phase_coherence(capture, profile, reference_channel="X", measurement_channel="Y")
            self.assertEqual(actual, exact, f"partition mask={mask}")

    def test_gap_rejection_and_reset_account_for_fresh_epoch_only(self):
        acquisition = ScopeAcquisition(EPOCH, window_frames=4, hop_frames=4, history_frames=4)
        self.assertEqual(acquisition.ingest(epoch=EPOCH, start_sample=0, planes=((9, 9), (9, 9))), ())
        with self.assertRaisesRegex(ValueError, "gap"):
            acquisition.ingest(epoch=EPOCH, start_sample=3, planes=((1,), (1,)))
        fresh = replace(EPOCH, epoch_id="take-b", origin_sample=20)
        acquisition.reset_epoch(fresh)
        (capture,) = acquisition.ingest(epoch=fresh, start_sample=20, planes=((1,) * 4, (-1,) * 4))
        result = analyze_phase_coherence(capture, PAIR, reference_channel="X", measurement_channel="Y")
        self.assertIs(result.epoch, fresh)
        self.assertEqual(result.segment_starts, (20, 22))
        self.assertEqual(result.bins[0].phase_radians, math.pi)

    def test_invalid_profile_geometry_and_coefficients_are_rejected(self):
        cases = (
            {"window": (1,)}, {"window": (0, 0)}, {"window": (1, math.nan)},
            {"window": (1, math.inf)}, {"window": (1, True)}, {"window": (1, 1j)},
            {"window": (1, 10**400)}, {"window": (1,) * 1025}, {"hop": 0},
            {"hop": 3}, {"hop": True}, {"fft_length": 1}, {"fft_length": 1025},
            {"fft_length": 2.0}, {"detrend": "center"},
        )
        for params in cases:
            with self.subTest(params=str(params)[:80]), self.assertRaises(ValueError):
                replace(PAIR, **params)

    def test_profile_freezes_window_inputs(self):
        taper = [1, 2]
        profile = WelchProfile(taper, 2, 2)
        taper[0] = 99
        self.assertEqual(profile.window, (1.0, 2.0))

    def test_invalid_capture_and_channel_selectors_are_rejected(self):
        capture = CaptureWindow(EPOCH, 0, ((1,) * 4, (1,) * 4))
        for value, profile, x, y in ((capture, PAIR, "X", "X"), (capture, PAIR, "missing", "Y"),
                                     (capture, PAIR, "X", None), (capture.planes, PAIR, "X", "Y"),
                                     (capture, {}, "X", "Y")):
            with self.subTest(profile=profile, x=x, y=y), self.assertRaises(ValueError):
                analyze_phase_coherence(value, profile, reference_channel=x, measurement_channel=y)

    def test_oversized_transform_work_is_rejected(self):
        profile = WelchProfile((1,) * 256, 1, 1024)
        with self.assertRaisesRegex(ValueError, "work limit"):
            measure([0] * 1024, [0] * 1024, profile)


if __name__ == "__main__":
    unittest.main()
