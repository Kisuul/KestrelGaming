"""Analytic, numeric, and acquisition fixtures for Mid/Side analysis."""

from dataclasses import replace
from fractions import Fraction as F
from itertools import product
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/audio-oscilloscope/scripts"))
sys.path.insert(0, str(ROOT / "skills/audio-mid-side-analysis/scripts"))
from reference_oscilloscope import CaptureWindow, ScopeAcquisition, ScopeEpoch
from reference_mid_side_analysis import _rms_binary64, analyze_mid_side


EPOCH = ScopeEpoch("take-a", 0, F(48_000), "input-clock", "pre-gain", "FS", ("L", "R"))
TINY = float.fromhex("0x0.0000000000001p-1022")
BIG = sys.float_info.max
GRID = tuple(F(i, 4) for i in range(-5, 6))


def analyze(left, right):
    return analyze_mid_side(CaptureWindow(EPOCH, 0, (left, right)),
                            left_channel="L", right_channel="R")


class MatrixTests(unittest.TestCase):
    def test_half_gain_basis_and_polarity(self):
        result = analyze([1, 1, 1, 0, 0], [1, -1, 0, 1, 0])
        self.assertEqual(result.mid.samples, (1, 0, F(1, 2), F(1, 2), 0))
        self.assertEqual(result.side.samples, (0, 1, F(1, 2), -F(1, 2), 0))
        self.assertEqual((result.mid.mean_square, result.side.mean_square), (F(3, 10), F(3, 10)))
        self.assertEqual(result.side_power_fraction, F(1, 2))

    def test_exact_inverse_energy_and_mid_side_cross_product_on_grid(self):
        pairs = list(product(GRID, repeat=2))
        left, right = zip(*[(float(x), float(y)) for x, y in pairs])
        frame = analyze(left, right)
        for (l, r), m, s in zip(pairs, frame.mid.samples, frame.side.samples):
            self.assertEqual((m + s, m - s), (l, r))
            self.assertEqual(m*m + s*s, (l*l + r*r) / 2)
            self.assertEqual(m*s, (l*l - r*r) / 4)
        self.assertEqual(frame.frame_count, 121)

    def test_swap_reverses_side_and_preserves_mid_and_powers(self):
        l, r = [1, -0.75, 0.25, -1], [0, -0.5, 1, 0]
        frame, swapped = analyze(l, r), analyze(r, l)
        self.assertEqual(swapped.mid, frame.mid)
        self.assertEqual(swapped.side.samples, tuple(-s for s in frame.side.samples))
        self.assertEqual(swapped.side.mean_square, frame.side.mean_square)
        self.assertEqual(swapped.side_power_fraction, frame.side_power_fraction)

    def test_common_and_differential_dc_shift_the_correct_component(self):
        l, r = [1, -1], [0.25, -0.25]
        origin = analyze(l, r)
        common = analyze([x + 0.5 for x in l], [y + 0.5 for y in r])
        differential = analyze([x + 0.5 for x in l], [y - 0.5 for y in r])
        self.assertEqual(common.mid.samples, tuple(v + F(1, 2) for v in origin.mid.samples))
        self.assertEqual(common.side, origin.side)
        self.assertEqual(differential.mid, origin.mid)
        self.assertEqual(differential.side.samples, tuple(v + F(1, 2) for v in origin.side.samples))

    def test_silence_uses_exact_zero_and_unavailable_fraction(self):
        frame = analyze([0.0, -0.0], [-0.0, 0])
        for component in (frame.mid, frame.side):
            self.assertEqual((component.samples, component.mean_square, component.rms,
                              component.rms_status), ((0, 0), 0, 0, "exact_zero"))
        self.assertIsNone(frame.side_power_fraction)

    def test_hard_panned_and_orthogonal_inputs_share_a_side_fraction(self):
        panned = analyze([1, -1, 1, -1], [0, 0, 0, 0])
        orthogonal = analyze([1, -1, 1, -1], [1, 1, -1, -1])
        self.assertEqual(panned.side_power_fraction, F(1, 2))
        self.assertEqual(orthogonal.side_power_fraction, F(1, 2))
        self.assertEqual(panned.mid.mean_square, F(1, 4))
        self.assertEqual(orthogonal.mid.mean_square, F(1, 2))

    def test_selectors_preserve_original_exact_capture_provenance(self):
        origin = 2**130 + 27
        epoch = replace(
            EPOCH, origin_sample=origin, channel_ids=("in-R", "ignored", "in-L"),
            rate_hz=F(48_000_000, 1001), tap_id="post-gain", units="V",
        )
        capture = CaptureWindow(epoch, origin + 5, ((1, 0), (90, 91), (0, 1)))
        result = analyze_mid_side(capture, left_channel="in-L", right_channel="in-R")
        self.assertIs(result.epoch, epoch)
        self.assertEqual((result.left_channel, result.right_channel), ("in-L", "in-R"))
        self.assertEqual((result.start_sample, result.end_sample_exclusive), (origin + 5, origin + 7))
        self.assertEqual((result.frame_count, result.center_sample_twice), (2, 2 * origin + 11))
        self.assertEqual((result.mid.samples, result.side.samples),
                         ((F(1, 2), F(1, 2)), (-F(1, 2), F(1, 2))))

    def test_input_requires_a_complete_capture_and_distinct_named_channels(self):
        frame = CaptureWindow(EPOCH, 0, ((1,), (1,)))
        for left, right in (("L", "L"), ("X", "R"), ("L", None)):
            with self.subTest(left=left, right=right), self.assertRaises(ValueError):
                analyze_mid_side(frame, left_channel=left, right_channel=right)
        with self.assertRaisesRegex(ValueError, "CaptureWindow"):
            analyze_mid_side(((1,), (1,)), left_channel="L", right_channel="R")

    def test_full_length_pcm32_capture_preserves_half_sample_and_large_side(self):
        left = [2**31 - 1, -2**31] * 512
        right = [-2**31, 2**31 - 1] * 512
        result = analyze(left, right)
        self.assertEqual(result.frame_count, 1024)
        self.assertEqual(result.mid.samples, (-F(1, 2),) * 1024)
        side_peak = F(2**32 - 1, 2)
        self.assertEqual(result.side.samples, (side_peak, -side_peak) * 512)
        self.assertEqual((result.mid.mean_square, result.side.mean_square), (F(1, 4), side_peak**2))


class PrecisionTests(unittest.TestCase):
    def test_tiny_side_residual_survives_direct_pairwise_subtraction(self):
        gain = 1 - 2**-40
        frame = analyze([1, -1], [gain, -gain])
        self.assertEqual(frame.side.mean_square, F(1, 2**82))
        self.assertEqual(frame.side.rms, 2**-41)
        self.assertEqual((1 + gain * gain - 2 * gain) / 4, 0.0)

    def test_equal_and_opposite_maximum_amplitudes_produce_finite_rms(self):
        same = analyze([BIG, -BIG], [BIG, -BIG])
        opposite = analyze([BIG, -BIG], [-BIG, BIG])
        self.assertTrue(math.isinf(BIG + BIG))
        for active, quiet in ((same.mid, same.side), (opposite.side, opposite.mid)):
            self.assertEqual(active.samples, (BIG, -BIG))
            self.assertEqual(active.mean_square, F(BIG)**2)
            self.assertEqual(active.rms, BIG)
            self.assertEqual(quiet.rms_status, "exact_zero")

    def test_smallest_subnormals_survive_the_full_sum_or_difference(self):
        same = analyze([TINY], [TINY])
        opposite = analyze([TINY], [-TINY])
        self.assertEqual(same.mid.samples, (TINY,))
        self.assertEqual(opposite.side.samples, (TINY,))
        self.assertEqual((same.mid.rms, opposite.side.rms), (TINY, TINY))
        self.assertEqual((same.side_power_fraction, opposite.side_power_fraction), (0, 1))

    def test_rounded_component_silence_can_have_positive_power_and_half_fraction(self):
        frame = analyze([TINY], [0])
        half = F(TINY) / 2
        for component in (frame.mid, frame.side):
            self.assertEqual(component.samples, (half,))
            self.assertEqual(float(component.samples[0]), 0.0)
            self.assertEqual(component.mean_square, half**2)
            self.assertEqual((component.rms, component.rms_status), (0.0, "rounded_to_zero"))
        self.assertEqual(frame.side_power_fraction, F(1, 2))

    def test_exact_side_fraction_can_be_smaller_than_the_smallest_positive_float(self):
        frame = analyze([BIG, TINY], [BIG, -TINY])
        expected = F(TINY)**2 / (F(BIG)**2 + F(TINY)**2)
        self.assertEqual(frame.side_power_fraction, expected)
        self.assertGreater(frame.side_power_fraction, 0)
        self.assertEqual(float(frame.side_power_fraction), 0)
        self.assertEqual(frame.side.rms, TINY)

    def test_reconstruction_after_individual_component_rounding_loses_the_quiet_channel(self):
        frame = analyze([1], [2**-60])
        (m,), (s,) = frame.mid.samples, frame.side.samples
        self.assertEqual((m + s, m - s), (1, F(1, 2**60)))
        self.assertEqual((float(m), float(s)), (0.5, 0.5))
        self.assertEqual(float(m) - float(s), 0.0)

    def test_subnormal_rms_halfway_and_adjacent_sides(self):
        for count, expected in ((3, TINY), (4, 0.0), (5, 0.0)):
            with self.subTest(count=count):
                pcm = [TINY] + [0] * (count - 1)
                frame = analyze(pcm, pcm)
                self.assertEqual(frame.mid.mean_square, F(TINY)**2 / count)
                self.assertEqual(frame.mid.rms, expected)
                self.assertEqual(frame.mid.rms_status, "finite" if expected else "rounded_to_zero")
                self.assertEqual(frame.side_power_fraction, 0)

    def test_rms_rounding_at_exact_grid_midpoints(self):
        for lo in (0.0, TINY, 2 * TINY, math.nextafter(1.0, 0.0),
                   1.0, math.nextafter(1.0, 2.0), math.nextafter(BIG, 0.0)):
            with self.subTest(lo=lo):
                hi = math.nextafter(lo, math.inf)
                a, b = F(lo), F(hi)
                midpoint = (a + b) / 2
                quarter = (b - a) / 4
                self.assertEqual(_rms_binary64((midpoint - quarter)**2), lo)
                self.assertEqual(_rms_binary64(midpoint**2), float(midpoint))
                self.assertEqual(_rms_binary64((midpoint + quarter)**2), hi)


class DeliveryTests(unittest.TestCase):
    def test_gain_matrix_fold_down_and_sharp_bound_for_all_5929_cases(self):
        pairs = list(product(GRID, repeat=2))
        left, right = zip(*[(float(x), float(y)) for x, y in pairs])
        frame = analyze(left, right)
        gains = [F(x) for x in (-2, -1, -0.5, 0, 0.5, 1, 2)]
        for gm, gs in product(gains, repeat=2):
            diag = (gm + gs) / 2
            off_diag = (gm - gs) / 2
            bound = max(abs(gm), abs(gs))
            self.assertEqual(abs(diag) + abs(off_diag), bound)
            measured_peak = 0
            for (l, r), m, s in zip(pairs, frame.mid.samples, frame.side.samples):
                out_l, out_r = gm * m + gs * s, gm * m - gs * s
                self.assertEqual((out_l, out_r), (diag * l + off_diag * r, off_diag * l + diag * r))
                self.assertEqual((out_l + out_r) / 2, gm * m)
                self.assertEqual((2 * out_l + out_r) / 3, gm * m + gs * s / 3)
                peak = max(abs(out_l), abs(out_r))
                self.assertLessEqual(peak, bound * max(abs(l), abs(r)))
                measured_peak = max(peak, measured_peak)
            self.assertEqual(measured_peak, bound * F(5, 4))

    def test_clipping_after_side_gain_changes_the_actual_mono_output(self):
        frame = analyze([1], [0])
        (m,), (s,) = frame.mid.samples, frame.side.samples
        l, r = m + 2 * s, m - 2 * s
        self.assertEqual((l, r), (F(3, 2), -F(1, 2)))
        self.assertEqual((l + r) / 2, F(1, 2))
        clipped = tuple(max(-1, min(1, value)) for value in (l, r))
        self.assertEqual(sum(clipped) / 2, F(1, 4))

    def test_shared_side_delay_and_single_output_delay_have_different_folds(self):
        frame = analyze([1, 0, 0], [-1, 0, 0])
        m, s = frame.mid.samples, frame.side.samples
        delayed_side = (F(0),) + s[:-1]
        l_pre = tuple(a + b for a, b in zip(m, delayed_side))
        r_pre = tuple(a - b for a, b in zip(m, delayed_side))
        self.assertEqual(tuple((a + b) / 2 for a, b in zip(l_pre, r_pre)), (0, 0, 0))

        l = tuple(a + b for a, b in zip(m, s))
        r = tuple(a - b for a, b in zip(m, s))
        delayed_right = (F(0),) + r[:-1]
        self.assertEqual(tuple((a + b) / 2 for a, b in zip(l, delayed_right)), (F(1, 2), -F(1, 2), 0))

    def test_same_lr_magnitudes_can_put_a_tone_in_different_components(self):
        angles = tuple(math.tau * index / 480 for index in range(480))
        a = tuple(0.75 * math.cos(10 * angle) for angle in angles)
        b = tuple(0.25 * math.cos(20 * angle) for angle in angles)
        left = [x + y for x, y in zip(a, b)]

        def peak_bin(samples, k):
            real = math.fsum(float(x) * math.cos(k * angle) for x, angle in zip(samples, angles))
            imag = -math.fsum(float(x) * math.sin(k * angle) for x, angle in zip(samples, angles))
            return (2 / 480) * complex(real, imag)

        for sign, expected in ((1, 0), (-1, 1)):
            with self.subTest(sign=sign):
                right = [x + sign * y for x, y in zip(a, b)]
                frame = analyze(left, right)
                self.assertAlmostEqual(float(frame.side_power_fraction), 0.1 * expected, delta=2e-15)
                for k, peak in ((10, 0.75), (20, 0.25)):
                    l_bin, r_bin = peak_bin(left, k), peak_bin(right, k)
                    m_bin, s_bin = peak_bin(frame.mid.samples, k), peak_bin(frame.side.samples, k)
                    self.assertAlmostEqual(abs(l_bin), peak, delta=2e-15)
                    self.assertAlmostEqual(abs(r_bin), peak, delta=2e-15)
                    channel_power = abs(l_bin)**2 + abs(r_bin)**2
                    cross_power = (l_bin.conjugate() * r_bin).real
                    self.assertAlmostEqual(abs(m_bin)**2, (channel_power + 2 * cross_power) / 4, delta=2e-15)
                    self.assertAlmostEqual(abs(s_bin)**2, (channel_power - 2 * cross_power) / 4, delta=2e-15)
                    if k == 20:
                        band_fraction = abs(s_bin)**2 / (abs(m_bin)**2 + abs(s_bin)**2)
                        self.assertAlmostEqual(band_fraction, expected, delta=2e-15)

    def test_flac_integer_parity_fixture_uses_a_different_matrix_convention(self):
        for left, right, encoded in ((1, 0, (0, 1)), (-32768, 32767, (-1, -65535))):
            with self.subTest(left=left, right=right):
                flac_mid = (left + right) >> 1
                flac_side = left - right
                self.assertEqual((flac_mid, flac_side), encoded)
                doubled_mid = (flac_mid << 1) | (flac_side & 1)
                self.assertEqual(((doubled_mid + flac_side) >> 1, (doubled_mid - flac_side) >> 1),
                                 (left, right))
                frame = analyze([left], [right])
                self.assertEqual((frame.mid.samples[0], frame.side.samples[0]),
                                 (F(left + right, 2), F(left - right, 2)))


class CaptureTests(unittest.TestCase):
    def test_callback_partitions_preserve_the_exact_aligned_samples(self):
        origin = 2**53 + 1
        epoch = replace(EPOCH, origin_sample=origin, channel_ids=("R", "L"))
        left = (1, 0, -1, 0, 0.25, -0.25, 1.25, -1.25)
        right = (1, 1, 0, -1, -0.25, 0.25, -1.25, 1.25)
        starts = (0, 2, 4)
        expected = [(origin + k, origin + k + 4,
                     tuple(F(x + y) / 2 for x, y in zip(left[k:k + 4], right[k:k + 4])),
                     tuple(F(x - y) / 2 for x, y in zip(left[k:k + 4], right[k:k + 4])))
                    for k in starts]
        for mask in range(1 << 7):
            cuts = [0] + [i for i in range(1, 8) if mask & (1 << (i - 1))] + [8]
            acquisition = ScopeAcquisition(epoch, window_frames=4, hop_frames=2, history_frames=4)
            windows = []
            for lo, hi in zip(cuts, cuts[1:]):
                windows.extend(acquisition.ingest(epoch=epoch, start_sample=origin + lo,
                                                  planes=(right[lo:hi], left[lo:hi])))
            results = [analyze_mid_side(w, left_channel="L", right_channel="R") for w in windows]
            self.assertEqual([(r.start_sample, r.end_sample_exclusive, r.mid.samples, r.side.samples)
                              for r in results], expected, f"partition mask={mask}")
            self.assertTrue(all(r.epoch is epoch for r in results))

    def test_invalid_block_and_explicit_epoch_reset_keep_support_coherent(self):
        start = 2**53 + 1
        epoch = replace(EPOCH, origin_sample=start)
        acquisition = ScopeAcquisition(epoch, window_frames=2, hop_frames=1, history_frames=2)
        self.assertEqual(acquisition.ingest(epoch=epoch, start_sample=start, planes=([1], [-1])), ())
        with self.assertRaises(ValueError):
            acquisition.ingest(epoch=epoch, start_sample=start + 1, planes=([2, 3], [1, math.nan]))
        with self.assertRaisesRegex(ValueError, "gap"):
            acquisition.ingest(epoch=epoch, start_sample=start + 2, planes=([1], [1]))
        (old,) = acquisition.ingest(epoch=epoch, start_sample=start + 1, planes=([-1], [1]))
        original = analyze_mid_side(old, left_channel="L", right_channel="R")
        self.assertEqual(original.side.samples, (1, -1))

        new_epoch = replace(epoch, epoch_id="take-b")
        acquisition.reset_epoch(new_epoch)
        (fresh,) = acquisition.ingest(epoch=new_epoch, start_sample=start, planes=([1, -1], [1, -1]))
        subsequent = analyze_mid_side(fresh, left_channel="L", right_channel="R")
        self.assertEqual((subsequent.mid.samples, subsequent.side.samples), ((1, -1), (0, 0)))
        self.assertEqual(subsequent.start_sample, original.start_sample)
        self.assertEqual((original.epoch.epoch_id, subsequent.epoch.epoch_id), ("take-a", "take-b"))


if __name__ == "__main__":
    unittest.main()
