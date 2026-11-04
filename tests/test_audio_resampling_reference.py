"""Analytic, metamorphic, streaming and independent SciPy golden SRC vectors."""
from fractions import Fraction
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/audio-resampling/scripts"))
from reference_resampling import (
    RatePlan, StreamResampler, resample_offline, MAX_INPUT_FRAMES, _fir,
)

FS48 = Fraction(48000)
FS44 = Fraction(44100)
FIXTURE = [0.0, 0.5, -0.25, 0.75, -1.0, 0.25, 0.125, 0.0,
           -0.5, 0.125, 0.375, 0.0]

# Generated OUTSIDE Kestrel by scipy.signal.resample_poly with
# NumPy 2.3.5 / SciPy 1.17.0, window=('kaiser',5.0), padtype='constant'.
# Expected samples are frozen, not recomputed using the implementation.
EXTERNAL_GOLDENS = {
    (2, 3): [0.1124327730614971, 0.23935957768978264,
             0.08976924774882472, -0.4006064044028096,
             0.3363991016518905, -0.3867256005748094,
             0.09205504112490565, 0.23072469040994972],
    (3, 2): [8.552184780013322e-17, 0.6164526639527842,
             0.08998889004164395, -0.2501515433884442,
             0.6674279994236061, 0.2680975260139356,
             -1.0006061735537772, -0.3669687925142025,
             0.5336985792620831, 0.12507577169422227,
             -0.048739060745331415, None, None, None, None, None,
             0.067962739222241, -0.015055152427177004],
    (147, 160): [0.16412129500217526, 0.2357355554821369,
                0.11233605732158873, 0.2562937848310793,
                -0.7864927976026487, 0.45347517047645847,
                -0.02629295183723203, -0.2771577884938048,
                -0.20590638992140523, 0.4735792056794883,
                -0.005312311402064077],
    (160, 147): [8.552774022508605e-17, 0.5640365252272107,
                -0.3212005408966079, 0.7440541706166092,
                -0.5076496309964155, -0.5112927844992433,
                0.5090873604614006, -0.06868262256009358,
                -0.08892122816928746, -0.5145861535958742,
                0.3017882209886384, None, -0.0025962283112636875,
                -0.0010988117876555466],
}


class ResamplingReferenceTests(unittest.TestCase):
    def test_exact_rational_44100_to_48000_factor_and_time(self):
        p = RatePlan(FS44, FS48)
        self.assertEqual((p.up, p.down), (160, 147))
        self.assertEqual(p.output_frames(12), 14)
        self.assertEqual(p.input_offset_at_output(160), Fraction(147))
        self.assertEqual(p.output_time_from_origin(160), Fraction(147, 44100))
        self.assertEqual(p.intermediate_hz, FS44 * 160)

    def test_exact_48000_to_44100_phase_and_ceil_length(self):
        p = RatePlan(FS48, FS44)
        self.assertEqual((p.up, p.down), (147, 160))
        self.assertEqual(p.output_frames(256), 236)
        self.assertEqual(p.input_offset_at_output(147), Fraction(160))
        self.assertEqual(p.output_time_from_origin(147), Fraction(160, 48000))
        self.assertEqual(p.output_frames(0), 0)

    def test_identity_is_bitwise_float_preservation(self):
        x = [-0.0, 0., 0.25, -0.125, 1.5, -1.5, 1e-300]
        o = resample_offline([x], FS48, FS48)
        self.assertEqual(o["planar_samples"], [x])
        self.assertEqual(math.copysign(1., o["planar_samples"][0][0]), -1.)
        self.assertEqual(o["filter_half_length_upsampled"], 0)
        self.assertEqual(o["compensated_group_delay_source_samples"], Fraction(0))
        self.assertFalse(any(o["boundary_affected"]))

    def test_zero_signal_cannot_create_energy(self):
        r = resample_offline([[0.] * 64], FS48, FS44)
        self.assertTrue(all(y == 0. for y in r["planar_samples"][0]))
        self.assertEqual(r["output_frames"], 59)

    def test_impulse_center_time_and_no_peak_time_shift(self):
        x = [0.] * 128
        x[60] = 1.
        result = resample_offline([x], Fraction(24000), FS48)
        # Normalized FIR has slight passband ripple: NOT an ideal +1 impulse.
        self.assertAlmostEqual(result["planar_samples"][0][120],
                               1.0005174705960602, delta=3e-12)
        self.assertEqual(result["output_last_source_offset"], Fraction(255, 2))
        self.assertFalse(result["boundary_affected"][120])

    def test_filter_is_symmetric_and_normalized_for_constant_gain(self):
        for up, down in [(2, 3), (160, 147), (147, 160), (1, 2)]:
            with self.subTest(up=up, down=down):
                coefficients = _fir(up, down)
                self.assertEqual(len(coefficients) % 2, 1)
                self.assertAlmostEqual(math.fsum(coefficients), up, delta=2e-12)
                for i in (0, 1, 5, len(coefficients) // 2):
                    self.assertAlmostEqual(coefficients[i], coefficients[-i-1],
                                           delta=2e-15)

    def test_interior_dc_preservation_under_declared_passband_ripple(self):
        for rates in [(FS48, FS44), (FS44, FS48), (FS48, Fraction(24000))]:
            with self.subTest(rates=rates):
                z = resample_offline([[0.375] * 256], *rates)
                interior = [v for v, edge in zip(
                    z["planar_samples"][0], z["boundary_affected"]) if not edge]
                self.assertTrue(interior)
                self.assertLess(max(abs(v - 0.375) for v in interior), 0.001)

    def test_alias_suppression_and_in_band_gain_48_to_24(self):
        n = 256
        def sine(f):
            return [math.sin(math.tau * f * k / 48000) for k in range(n)]
        low = resample_offline([sine(2000)], FS48, Fraction(24000))["planar_samples"][0][25:-25]
        high = resample_offline([sine(18000)], FS48, Fraction(24000))["planar_samples"][0][25:-25]
        rms = lambda z: math.sqrt(math.fsum(v * v for v in z) / len(z))
        self.assertAlmostEqual(rms(low), 2 ** -0.5, delta=0.01)
        self.assertLess(rms(high), 0.001)  # more than 55 dB rejection vs 0.707

    def test_resampling_does_not_silently_clamp_over_reference_signal(self):
        x = [0.] * 128
        x[63] = x[64] = 1.
        r = resample_offline([x], FS48, Fraction(96000))
        self.assertGreater(max(r["planar_samples"][0]), 1.2)

    def test_antiphase_channel_preservation(self):
        x = [math.sin(2 * math.pi * 3 * n / 128) for n in range(128)]
        r = resample_offline([x, [-v for v in x]], FS48, FS44)
        self.assertEqual(len(r["planar_samples"]), 2)
        for left, right in zip(*r["planar_samples"]):
            self.assertAlmostEqual(left, -right, delta=2e-15)

    def test_full_vs_arbitrary_chunk_schedule_matches_bitwise(self):
        x = [math.sin(math.tau * 7 * i / 97) +
             0.1 * math.cos(math.tau * 13 * i / 97) for i in range(97)]
        origin = 2 ** 54 + 99
        ref = resample_offline([x, [-v for v in x]], FS44, FS48,
                               input_origin_sample=origin, epoch_id="epoch",
                               output_origin_sample=1000001)
        for pattern in [(1,), (3, 7, 11), (13, 64), (97,)]:
            with self.subTest(pattern=pattern):
                stream = StreamResampler("epoch", origin, FS44, FS48, 2, 1000001)
                channels = [[], []]
                flags = []
                offset = 0
                k = 0
                while offset < len(x):
                    count = min(pattern[k % len(pattern)], len(x) - offset)
                    part = x[offset:offset + count]
                    block = stream.push(origin + offset,
                                        [part, [-v for v in part]])
                    for ch in range(2):
                        channels[ch].extend(block["planar_samples"][ch])
                    flags.extend(block["boundary_affected"])
                    self.assertEqual(
                        block["first_source_offset"],
                        Fraction((block["output_start_sample"] - 1000001) * 147, 160))
                    offset += count
                    k += 1
                tail = stream.finalize()
                for ch in range(2):
                    channels[ch].extend(tail["planar_samples"][ch])
                flags.extend(tail["boundary_affected"])
                self.assertEqual(channels, ref["planar_samples"])
                self.assertEqual(flags, ref["boundary_affected"])
                self.assertEqual(stream.next_input_sample, origin + len(x))
                self.assertEqual(stream.next_output_offset, ref["output_frames"])

    def test_noncausal_lookahead_prevents_partial_block_edge_padding(self):
        stream = StreamResampler("e", 0, FS48, Fraction(24000), 1)
        first = stream.push(0, [[0.0] * 8])
        self.assertEqual(first["output_frames"], 0)
        nextblock = stream.push(8, [[1.0] * 56])
        self.assertGreater(nextblock["output_frames"], 0)
        self.assertTrue(nextblock["boundary_affected"][0])
        self.assertFalse(nextblock["finalized_tail"])
        self.assertEqual(stream.finalize()["output_frames"] +
                         nextblock["output_frames"], 32)

    def test_gap_and_overlap_fail_atomically(self):
        base = 2 ** 54
        s = StreamResampler("a", base, FS48, FS44, 1)
        s.push(base, [[0.25] * 32])
        before = (s.next_input_sample, s.next_output_offset)
        for start in (base + 33, base + 30):
            with self.subTest(start=start):
                with self.assertRaises(ValueError):
                    s.push(start, [[0.5]])
                self.assertEqual((s.next_input_sample, s.next_output_offset), before)

    def test_nan_inf_and_channel_shape_fail_atomically(self):
        s = StreamResampler("a", 0, FS48, FS44, 2)
        s.push(0, [[0.0] * 16, [0.0] * 16])
        before = (s.next_input_sample, s.next_output_offset)
        for inp in ([[0.0]], [[], []], [[0.], [0., 0.]],
                    [[math.nan], [0.]], [[math.inf], [0.]],
                    [[True], [0.]], [[complex(1)], [0.]]):
            with self.subTest(inp=repr(inp)):
                with self.assertRaises(ValueError):
                    s.push(16, inp)
                self.assertEqual((s.next_input_sample, s.next_output_offset), before)

    def test_output_overflow_fails_without_consuming_input(self):
        s = StreamResampler("a", 0, FS48, Fraction(96000), 1)
        x = [0.] * 128
        x[63] = x[64] = 1.7e308
        with self.assertRaises(ValueError):
            s.push(0, [x])
        self.assertEqual((s.next_input_sample, s.next_output_offset), (0, 0))

    def test_unrepresentable_rational_ratios_and_rate_types_rejected(self):
        for source, dest in [(FS44, Fraction(192000)),
                             (FS48, Fraction(48001)),
                             (Fraction(-1), FS48), (FS48, Fraction(0)),
                             (48000, FS44), (FS44, 48000)]:
            with self.subTest(rates=(source, dest)):
                with self.assertRaises(ValueError):
                    RatePlan(source, dest)

    def test_bad_stream_configurations_rejected(self):
        for args in [("e", 0, FS48, FS44, 0), ("e", 0, FS48, FS44, 9),
                     ("", 0, FS48, FS44, 1), ("e", -1, FS48, FS44, 1),
                     ("e", 0, FS48, FS44, True)]:
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    StreamResampler(*args)
        with self.assertRaises(ValueError):
            resample_offline([], FS48, FS44)
        with self.assertRaises(ValueError):
            resample_offline([[0.0] * (MAX_INPUT_FRAMES + 1)], FS48, FS44)

    def test_finalize_once_no_additional_input_without_epoch_reset(self):
        s = StreamResampler("a", 0, FS48, FS44, 1)
        s.push(0, [[.25] * 16])
        final = s.finalize()
        self.assertTrue(final["finalized_tail"])
        with self.assertRaises(ValueError):
            s.finalize()
        with self.assertRaises(ValueError):
            s.push(16, [[0.]])

    def test_reset_epoch_unique_and_reconfigure_is_atomic(self):
        s = StreamResampler("old", 0, FS48, FS44, 1)
        s.push(0, [[0.0] * 32])
        with self.assertRaises(ValueError):
            s.reset_epoch("old", 100)
        with self.assertRaises(ValueError):
            s.reset_epoch("new", 100, Fraction(48001), FS44)
        self.assertEqual((s.epoch_id, s.next_input_sample), ("old", 32))
        s.reset_epoch("middle", 100, FS44, FS48, 2, 200)
        self.assertEqual((s.epoch_id, s.next_input_sample, s.channels,
                          s.output_origin_sample), ("middle", 100, 2, 200))
        with self.assertRaises(ValueError):
            s.reset_epoch("old", 500)
        s.reset_epoch("new", 300)
        self.assertEqual(s.push(300, [[0.], [1.]])["output_start_sample"], 0)

    def test_exact_output_origin_at_large_sample_coordinate(self):
        origin = 2 ** 54 + 29
        s = StreamResampler("big", origin, FS44, FS48, 1,
                            output_origin_sample=2 ** 54 + 31)
        a = s.push(origin, [[0.] * 64])
        b = s.finalize()
        self.assertEqual(a["output_start_sample"], 2 ** 54 + 31)
        self.assertEqual(b["output_start_sample"],
                         2 ** 54 + 31 + a["output_frames"])
        self.assertEqual(a["first_source_offset"], Fraction(0))
        self.assertEqual(a["source_origin_sample"], origin)

    def test_boundary_flags_do_not_claim_interior_at_edges(self):
        x = [0.] * 128
        r = resample_offline([x], FS48, FS44)
        self.assertTrue(r["boundary_affected"][0])
        self.assertTrue(r["boundary_affected"][-1])
        self.assertTrue(any(not flag for flag in r["boundary_affected"]))

    def test_scipy_117_independent_golden_vectors(self):
        for (up, down), expected in EXTERNAL_GOLDENS.items():
            with self.subTest(up=up, down=down):
                y = resample_offline([FIXTURE], Fraction(down), Fraction(up))["planar_samples"][0]
                self.assertEqual(len(y),
                                 (len(FIXTURE) * up + down - 1) // down)
                for i, value in enumerate(expected):
                    if value is not None:
                        self.assertAlmostEqual(y[i], value, delta=3e-12,
                                               msg=f"{up}/{down}: sample={i}")


if __name__ == "__main__":
    unittest.main()
