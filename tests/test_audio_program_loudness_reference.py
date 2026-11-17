"""Published loudness expectations plus independent and adversarial fixtures."""

import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] /
                       "skills/audio-program-loudness/scripts"))
from reference_program_loudness import LoudnessConfig, ProgramLoudnessStream, integrate_block_rms


STEREO = ("L", "R")
BED = ("L", "R", "C", "LS", "RS")
EBU_TOLERANCE = 0.1  # Tech 3341, Table 1. Fixed before running the reference.


def meter(labels=("MONO",), origin=0, hop=480):
    config = LoudnessConfig(48_000, labels, "test fixture PCM", hop)
    return ProgramLoudnessStream(config, epoch_id="test", start_sample=origin)


def push(stream, planes):
    return stream.push(stream.next_sample, planes, epoch_id=stream.epoch_id)


def reading(stream):
    return stream.integrated()["gating"]


def tone(frames, peak, frequency=1000):
    return [peak * math.sin(math.tau * ((n * frequency) % 48_000) / 48_000)
            for n in range(frames)]


def feed_segments(stream, segments):
    """Synthesize 1 kHz independently on integer-ms boundaries, no padding."""
    momentary, short_term = [], []
    for duration_ms, levels in segments:
        cycles = [tone(48, 0.0 if level is None else 10 ** (level / 20)) for level in levels]
        for start_ms in range(0, duration_ms, 400):
            length_ms = min(duration_ms - start_ms, 400)
            result = push(stream, [cycle * length_ms for cycle in cycles])
            momentary.extend(result["momentary"])
            short_term.extend(result["short_term"])
    return momentary, short_term


class PublishedToneTests(unittest.TestCase):
    def assert_ebu(self, observed, target):
        self.assertAlmostEqual(observed, target, delta=EBU_TOLERANCE)

    def test_ebu_cases_1_and_2_constant_tones(self):
        for level in (-23, -33):
            with self.subTest(level=level):
                stream = meter(STEREO)
                momentary, short_term = feed_segments(stream, [(20_000, (level, level))])
                self.assertEqual(len(momentary), 1961)
                self.assertEqual(len(short_term), 1701)
                for window in momentary + short_term:
                    self.assert_ebu(window.lufs, level)
                self.assert_ebu(reading(stream).integrated_lufs, level)

    def test_ebu_case_3_two_quiet_sections(self):
        stream = meter(STEREO)
        feed_segments(stream, [(10_000, (-36, -36)), (60_000, (-23, -23)), (10_000, (-36, -36))])
        result = reading(stream)
        self.assert_ebu(result.integrated_lufs, -23)
        self.assertEqual(result.absolute_survivor_count, result.complete_block_count)
        self.assertLess(result.final_survivor_count, result.absolute_survivor_count)

    def test_ebu_case_4_quiet_and_under_absolute_gate(self):
        stream = meter(STEREO)
        feed_segments(stream, [(10_000, (-72, -72)), (10_000, (-36, -36)),
                               (60_000, (-23, -23)), (10_000, (-36, -36)),
                               (10_000, (-72, -72))])
        result = reading(stream)
        self.assert_ebu(result.integrated_lufs, -23)
        self.assertLess(result.absolute_survivor_count, result.complete_block_count)
        self.assertLess(result.final_survivor_count, result.absolute_survivor_count)

    def test_ebu_case_5_energy_mean(self):
        stream = meter(STEREO)
        feed_segments(stream, [(20_000, (-26, -26)), (20_100, (-20, -20)), (20_000, (-26, -26))])
        result = reading(stream)
        self.assert_ebu(result.integrated_lufs, -23)
        self.assertEqual(result.final_survivor_count, result.complete_block_count)

    def test_ebu_case_6_surround_weights(self):
        stream = meter(BED)
        feed_segments(stream, [(20_000, (-28, -28, -24, -30, -30))])
        self.assert_ebu(reading(stream).integrated_lufs, -23)

    def test_ebu_case_9_short_term_varied_input(self):
        stream = meter(STEREO)
        _, short_term = feed_segments(stream, [(1340, (-20, -20)), (1660, (-30, -30))] * 5)
        self.assertEqual(short_term[0].end_sample_exclusive, 144_000)
        for window in short_term:
            self.assert_ebu(window.lufs, -23)

    def test_ebu_case_12_momentary_varied_input(self):
        stream = meter(STEREO)
        momentary, _ = feed_segments(stream, [(180, (-20, -20)), (220, (-30, -30))] * 25)
        checked = [window for window in momentary if window.end_sample_exclusive >= 48_000]
        self.assertTrue(checked)
        for window in checked:
            self.assert_ebu(window.lufs, -23)

    def test_offset_maxima_for_case_10_and_13(self):
        for prefix_ms, tone_ms in ((150, 3000), (20, 400)):
            with self.subTest(prefix_ms=prefix_ms, tone_ms=tone_ms):
                stream = meter(STEREO)
                momentary, short_term = feed_segments(
                    stream, [(prefix_ms, (None, None)), (tone_ms, (-23, -23)), (1000, (None, None))],
                )
                windows = short_term if tone_ms == 3000 else momentary
                self.assert_ebu(max(window.lufs for window in windows), -23)

    def test_itu_997_hz_single_front_channel_calibration(self):
        stream = meter(("C",))
        result = push(stream, [tone(48_000, 1.0, frequency=997)])
        self.assertAlmostEqual(result["momentary"][-1].lufs, -3.0103, delta=0.015)
        self.assertAlmostEqual(reading(stream).integrated_lufs, -3.0103, delta=0.015)

    def test_k_weighting_low_and_high_frequency_response(self):
        # Steady-state, one front channel at unit peak. Values from SciPy freqz
        # evaluation of the published ITU sections, rounded here to 1e-6 LU.
        for frequency, target in ((25, -14.094064), (100, -4.834798),
                                  (500, -3.658838), (2000, -0.630043),
                                  (10000, 0.340582), (16000, 0.341755)):
            with self.subTest(frequency=frequency):
                stream = meter(("C",))
                result = push(stream, [tone(48_000, 1.0, frequency=frequency)])
                self.assertAlmostEqual(result["momentary"][-1].lufs, target, delta=0.00001)


class GateTests(unittest.TestCase):
    def test_independent_two_pass_fixture(self):
        roots = [10 ** ((level + 0.691) / 20) for level in (-23, -40, -23, -40)]
        result = integrate_block_rms(roots)
        self.assertAlmostEqual(result.absolute_gated_lufs, -25.9244999643, places=9)
        self.assertAlmostEqual(result.relative_gate_lufs, -35.9244999643, places=9)
        self.assertAlmostEqual(result.integrated_lufs, -23.0, places=12)
        self.assertEqual((result.absolute_survivor_count, result.final_survivor_count), (4, 2))

    def test_absolute_gate_is_strict_even_when_relative_gate_is_lower(self):
        gate = 0.0003424128070885051  # 10^((-70 + 0.691)/20), in binary64
        just_under = math.nextafter(gate, 0)
        just_over = math.nextafter(gate, math.inf)
        result = integrate_block_rms([just_under, gate, just_over])
        self.assertEqual((result.absolute_survivor_count, result.final_survivor_count), (1, 1))
        self.assertLess(result.relative_gate_lufs, -70)
        self.assertEqual(integrate_block_rms([gate]).status, "below_absolute_gate")

    def test_relative_gate_is_strict(self):
        # Mean of {1, 4, 25} is 10. A power of 1 falls exactly on the second gate.
        for boundary, survivors in ((math.nextafter(1.0, 0), 2), (1.0, 2),
                                    (math.nextafter(1.0, 2), 3)):
            with self.subTest(boundary=boundary):
                result = integrate_block_rms([boundary, 2.0, 5.0])
                self.assertEqual(result.absolute_survivor_count, 3)
                self.assertEqual(result.final_survivor_count, survivors)
                self.assertAlmostEqual(result.relative_gate_lufs, -0.691, places=12)

    def test_live_query_reclassifies_previous_blocks(self):
        stream = meter(STEREO)
        feed_segments(stream, [(1000, (-43, -43))])
        before = reading(stream)
        self.assertEqual(before.final_survivor_count, 7)
        self.assertAlmostEqual(before.integrated_lufs, -43, delta=0.1)
        feed_segments(stream, [(2000, (-23, -23))])
        after = reading(stream)
        self.assertGreater(after.relative_gate_lufs, before.integrated_lufs)
        self.assertEqual(after.absolute_survivor_count, 27)
        self.assertEqual(after.final_survivor_count, 20)
        self.assertEqual(before.final_survivor_count, 7)

    def test_unavailable_and_gated_out_have_distinct_states(self):
        for peak, expected in ((0.0, "silence"), (1e-4, "below_absolute_gate")):
            with self.subTest(peak=peak):
                stream = meter()
                self.assertEqual(reading(stream).status, "insufficient_data")
                self.assertIsNone(stream.integrated()["gate_end_sample_exclusive"])
                result = push(stream, [tone(19_200, peak)])
                gating = reading(stream)
                self.assertEqual(gating.status, expected)
                self.assertIsNone(gating.integrated_lufs)
                self.assertIsNone(gating.relative_gate_lufs)
                self.assertEqual(gating.complete_block_count, 1)
                self.assertEqual(math.isfinite(result["momentary"][0].lufs), peak != 0)

    def test_gate_rejects_invalid_roots(self):
        for bad in (-1.0, math.inf, math.nan, True, "1", 10**400):
            with self.subTest(bad=str(bad)[:20]), self.assertRaises(ValueError):
                integrate_block_rms([1.0, bad])


class SignalAndEpochTests(unittest.TestCase):
    def test_stereo_phase_and_mono_power(self):
        sine = tone(19_200, 0.125)
        mono, in_phase, opposite = meter(), meter(STEREO), meter(STEREO)
        push(mono, [sine])
        push(in_phase, [sine, sine])
        push(opposite, [sine, [-sample for sample in sine]])
        self.assertEqual(reading(in_phase), reading(opposite))
        gain = reading(in_phase).integrated_lufs - reading(mono).integrated_lufs
        self.assertAlmostEqual(gain, 10 * math.log10(2), places=12)

    def test_lfe_exclusion_and_reordered_planes(self):
        sine, lfe = tone(24_000, 0.125), tone(24_000, 2.0, frequency=60)
        zero = [0.0] * len(sine)
        five = meter(BED)
        push(five, [sine, zero, zero, zero, sine])
        six = meter(("RS", "LFE", "C", "R", "LS", "L"))
        push(six, [sine, lfe, zero, zero, zero, sine])
        self.assertEqual(five.gate_block_rms, six.gate_block_rms)
        six.reset_epoch("lfe-only", 0)
        result = push(six, [zero, lfe, zero, zero, zero, zero])
        self.assertEqual(reading(six).status, "silence")
        self.assertEqual(result["momentary"][-1].lufs, -math.inf)

    def test_channel_role_weight_is_power_not_amplitude(self):
        sine = tone(19_200, 0.1)
        zero = [0.0] * len(sine)
        front, surround = meter(BED), meter(BED)
        push(front, [sine, zero, zero, zero, zero])
        push(surround, [zero, zero, zero, sine, zero])
        delta = reading(surround).integrated_lufs - reading(front).integrated_lufs
        self.assertAlmostEqual(delta, 10 * math.log10(1.41), places=12)

    def test_gain_shift_for_fixed_gate_membership(self):
        baseline, louder = meter(), meter()
        signal = tone(148_800, 0.1)
        first = push(baseline, [signal])
        second = push(louder, [[sample * 10 ** (6 / 20) for sample in signal]])
        for series in ("momentary", "short_term"):
            self.assertTrue(first[series])
            for a, b in zip(first[series], second[series]):
                self.assertAlmostEqual(b.lufs - a.lufs, 6, places=9)
        before, after = reading(baseline), reading(louder)
        self.assertEqual(before.final_survivor_count, after.final_survivor_count)
        self.assertAlmostEqual(after.integrated_lufs - before.integrated_lufs, 6, places=9)

    def test_exact_full_window_boundaries_at_large_origin(self):
        origin = 2**60 + 17
        stream = meter(origin=origin)
        almost = push(stream, [[0] * 19_199])
        self.assertEqual(almost["momentary"], ())
        self.assertEqual(reading(stream).complete_block_count, 0)
        first = push(stream, [[0]])["momentary"][0]
        self.assertEqual((first.start_sample, first.end_sample_exclusive), (origin, origin + 19_200))
        before = stream.integrated()
        push(stream, [[0] * 4799])
        self.assertEqual(stream.integrated()["gating"], before["gating"])
        self.assertEqual(stream.integrated()["gate_end_sample_exclusive"], origin + 19_200)
        push(stream, [[0]])
        self.assertEqual(reading(stream).complete_block_count, 2)
        self.assertEqual(stream.integrated()["gate_end_sample_exclusive"], origin + 24_000)
        nearly_s = push(stream, [[0] * (144_000 - 24_001)])
        self.assertFalse(nearly_s["short_term"])
        first_s = push(stream, [[0]])["short_term"][0]
        self.assertEqual((first_s.start_sample, first_s.end_sample_exclusive), (origin, origin + 144_000))

    def test_gate_grid_is_independent_of_window_readout_cadence(self):
        signal = tone(32_000, 0.1)
        fast, slow = meter(), meter(hop=960)
        one = push(fast, [signal])["momentary"]
        two = push(slow, [signal])["momentary"]
        self.assertEqual(one[::2], two)
        self.assertEqual(fast.gate_block_rms, slow.gate_block_rms)
        self.assertEqual(reading(fast), reading(slow))

    def test_loud_tail_changes_momentary_before_integrated(self):
        stream = meter()
        push(stream, [tone(19_200, 0.01)])
        original = reading(stream)
        loud = tone(4_800, 1.0)
        tail = push(stream, [loud[:-1]])
        self.assertGreater(tail["momentary"][-1].lufs, original.integrated_lufs + 20)
        self.assertEqual(reading(stream), original)
        push(stream, [loud[-1:]])
        self.assertEqual(reading(stream).complete_block_count, 2)
        self.assertGreater(reading(stream).integrated_lufs, original.integrated_lufs + 20)

    def test_partition_invariance_for_filter_and_all_window_state(self):
        size = 148_867
        left = tone(size, 0.1, frequency=997)
        right = [sample * (0.03 if n < 70_013 else 0.2)
                 for n, sample in enumerate(tone(size, 1.0, frequency=63))]
        origin = 2**53 + 13
        uncut, cut = meter(STEREO, origin), meter(STEREO, origin)
        expected = push(uncut, [left, right])
        momentary, short_term = [], []
        offset = 0
        for width in (1, 478, 3, 4097, 19_826, 7, 83_333, size):
            end = min(size, offset + width)
            result = push(cut, [left[offset:end], right[offset:end]])
            momentary.extend(result["momentary"])
            short_term.extend(result["short_term"])
            offset = end
        self.assertEqual(tuple(momentary), expected["momentary"])
        self.assertEqual(tuple(short_term), expected["short_term"])
        self.assertEqual(cut.gate_block_rms, uncut.gate_block_rms)
        self.assertEqual(cut.integrated(), uncut.integrated())

    def test_reset_clears_pending_samples_filters_and_gate_history(self):
        stream = meter()
        push(stream, [tone(20_001, 0.8)])
        with self.assertRaises(ValueError):
            stream.reset_epoch("test", 0)
        with self.assertRaises(ValueError):
            stream.reset_epoch("next", True)
        self.assertEqual(stream.next_sample, 20_001)
        stereo = LoudnessConfig(48_000, STEREO, "new stereo tap")
        stream.reset_epoch("next", 9, stereo)
        self.assertEqual(stream.gate_block_rms, ())
        zeros = [0.0] * 19_200
        result = push(stream, [zeros, zeros])
        self.assertEqual(result["config"], stereo)
        self.assertEqual(result["momentary"][0].start_sample, 9)
        self.assertEqual(reading(stream).status, "silence")
        with self.assertRaises(ValueError):
            stream.reset_epoch("test", 0)

    def test_no_partial_state_after_late_nonfinite_or_overflow(self):
        stream, control = meter(STEREO), meter(STEREO)
        prefix = tone(19_199, 0.3)
        push(stream, [prefix, prefix])
        push(control, [prefix, prefix])
        before = stream.integrated()
        for invalid in (math.nan, math.inf, sys.float_info.max, 10**400, True):
            with self.subTest(invalid=str(invalid)[:20]):
                signal = tone(6000, 0.2)
                corrupt = signal[:-1] + [invalid]
                with self.assertRaises(ValueError):
                    push(stream, [signal, corrupt])
                self.assertEqual(stream.integrated(), before)
                self.assertEqual(stream.gate_block_rms, ())
        signal = tone(6000, 0.22)
        self.assertEqual(push(stream, [signal, signal]), push(control, [signal, signal]))
        self.assertEqual(stream.integrated(), control.integrated())

    def test_reject_bad_shape_wrong_epoch_gap_overlap_and_false_integer(self):
        stream = meter(STEREO, origin=20)
        for offset, epoch, planes in ((21, "test", [[0], [0]]), (19, "test", [[0], [0]]),
                                      (20, "old", [[0], [0]]), (True, "test", [[0], [0]]),
                                      (20, "test", [[0]]), (20, "test", [0, 0]),
                                      (20, "test", [[], []]), (20, "test", [[0, 1], [0]])):
            with self.subTest(offset=offset, epoch=epoch, planes=planes), self.assertRaises(ValueError):
                stream.push(offset, planes, epoch_id=epoch)
        self.assertEqual(stream.next_sample, 20)

    def test_reject_unsupported_rate_labels_tap_and_cadence(self):
        for args in ((44100, STEREO, "tap", 480), (48000.0, STEREO, "tap", 480),
                     (48000, ("L", "L"), "tap", 480), (48000, ("LFE",), "tap", 480),
                     (48000, ("L", "R", "C"), "tap", 480), (48000, ("CH1", "CH2"), "tap", 480),
                     (48000, ("L", "R", "C", "LS", "RS", "LFE", "TOP"), "tap", 480),
                     (48000, STEREO, " ", 480), (48000, STEREO, "tap", 481),
                     (48000, STEREO, "tap", False)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                LoudnessConfig(*args)

    def test_lfe_input_validation_still_applies(self):
        stream = meter(BED + ("LFE",))
        with self.assertRaisesRegex(ValueError, "LFE"):
            push(stream, [[0.0]] * 5 + [[math.nan]])
        self.assertEqual(stream.next_sample, 0)

    def test_representable_loudness_with_extreme_power(self):
        for peak in (1e-200, 1e200):
            with self.subTest(peak=peak):
                stream = meter(STEREO)
                sine = tone(19_200, peak)
                result = push(stream, [sine, sine])["momentary"][0]
                self.assertAlmostEqual(result.lufs, 20 * math.log10(peak), delta=0.02)
                self.assertEqual(reading(stream).status, "ok" if peak > 1 else "below_absolute_gate")

    def test_quiet_window_after_large_signal_retains_its_energy(self):
        stream = meter(STEREO)
        loud, quiet = tone(19_200, 1e70), tone(192_000, 1e-60)
        push(stream, [loud, loud])
        final = push(stream, [quiet, quiet])["momentary"][-1]
        self.assertAlmostEqual(final.lufs, -1200, delta=0.02)


if __name__ == "__main__":
    unittest.main()
