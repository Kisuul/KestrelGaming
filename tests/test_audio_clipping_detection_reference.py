"""Rail and reference evidence from contiguous, interrupted, and encoded PCM."""

from dataclasses import replace
from fractions import Fraction as F
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
for skill in (
    "audio-clipping-detection", "audio-oscilloscope", "audio-timebase-sync", "audio-sample-formats",
    "audio-true-peak", "audio-thd-thdn", "audio-power-spectral-density",
):
    sys.path.insert(0, str(ROOT / "skills" / skill / "scripts"))

from reference_clipping_detection import ClippingDetector, FloatReferenceProfile, SignedPcmProfile
from reference_oscilloscope import CaptureWindow, MAX_BLOCK_FRAMES, MAX_SAMPLE_INDEX, ScopeEpoch
from reference_pcm import PCMFormat, encode_pcm
from reference_thd_thdn import ThdProfile, measure_thd_thdn
from reference_timebase import DiscontinuityError
from reference_true_peak import experimental_peak_estimate


ORIGIN = 2**60 + 37
EPOCH = ScopeEpoch("first", ORIGIN, F(48000), "sample-clock", "capture", "PCM", ("M",))
PCM16 = SignedPcmProfile(16)
LOW, HIGH = -32768, 32767
SOURCE = (0, HIGH, HIGH, HIGH, 0, LOW, LOW, 0, HIGH - 1, HIGH, HIGH - 1, 0)


def ingest(detector, values, *, epoch=EPOCH, start=None):
    return detector.ingest(
        epoch=epoch, start_sample=detector.next_sample if start is None else start, planes=(values,),
    )


def replay(planes, partitions, *, epoch=EPOCH, profile=PCM16):
    detector = ClippingDetector(epoch, profile)
    completed = []
    offset = 0
    for length in partitions:
        report = detector.ingest(
            epoch=epoch, start_sample=epoch.origin_sample + offset,
            planes=tuple(channel[offset:offset + length] for channel in planes),
        )
        completed.extend(report.completed_runs)
        offset += length
    final = detector.finish()
    return final.counts, tuple(completed) + final.completed_runs


def positions(run, origin=ORIGIN):
    return run.start_sample - origin, run.end_sample_exclusive - origin


class SignedRailTests(unittest.TestCase):
    def test_rail_counts_and_partition_invariance_at_large_origin(self):
        whole = replay((SOURCE,), (12,))
        self.assertEqual(whole, replay((SOURCE,), (2, 3, 1, 6)))
        (count,), (positive, negative, isolated) = whole
        self.assertEqual((count.positive_contacts, count.negative_contacts), (4, 2))
        self.assertEqual((count.positive_exceedances, count.negative_exceedances), (0, 0))
        self.assertEqual([positions(run) for run in (positive, negative, isolated)], [(1, 4), (5, 7), (9, 10)])
        self.assertEqual([run.polarity for run in (positive, negative, isolated)], ["positive", "negative", "positive"])
        self.assertEqual([run.boundary for run in (positive, negative, isolated)], [HIGH, LOW, HIGH])
        self.assertEqual(positive.epoch_id, EPOCH.epoch_id)
        self.assertEqual(positive.kind, "rail_contact")
        self.assertEqual(positive.length, 3)
        self.assertEqual(negative.plateau_ready_sample_exclusive, ORIGIN + 7)
        self.assertIsNone(isolated.plateau_ready_sample_exclusive)

    def test_plateau_readiness_and_confirmed_end_use_distinct_support(self):
        detector = ClippingDetector(EPOCH, PCM16)
        before = ingest(detector, SOURCE[:2])
        self.assertIsNone(before.open_runs[0].plateau_ready_sample_exclusive)
        plateau = ingest(detector, SOURCE[2:3])
        (open_run,) = plateau.open_runs
        self.assertEqual(plateau.completed_runs, ())
        self.assertEqual(open_run.plateau_ready_sample_exclusive, ORIGIN + 3)
        self.assertIsNone(open_run.end_confirmed_sample_exclusive)
        self.assertIsNone(open_run.close_reason)
        done = ingest(detector, SOURCE[3:5])
        (run,) = done.completed_runs
        self.assertEqual(positions(run), (1, 4))
        self.assertEqual(run.plateau_ready_sample_exclusive, ORIGIN + 3)
        self.assertEqual(run.end_confirmed_sample_exclusive, ORIGIN + 5)
        self.assertEqual(run.close_reason, "observed_break")
        self.assertEqual(done.open_runs, ())
        self.assertEqual(positions(open_run), (1, 3))

    def test_long_plateau_qualifies_across_blocks_and_keeps_first_frontier(self):
        detector = ClippingDetector(EPOCH, SignedPcmProfile(16, minimum_plateau_samples=300))
        self.assertIsNone(ingest(detector, (HIGH,) * 256).open_runs[0].plateau_ready_sample_exclusive)
        past = ingest(detector, (HIGH,) * 100).open_runs[0]
        self.assertEqual(past.plateau_ready_sample_exclusive, ORIGIN + 300)
        closed = ingest(detector, (HIGH, 0)).completed_runs[0]
        self.assertEqual(closed.plateau_ready_sample_exclusive, ORIGIN + 300)
        self.assertEqual(positions(closed), (0, 357))
        self.assertEqual(closed.end_confirmed_sample_exclusive, ORIGIN + 358)

    def test_adjacent_opposite_rails_close_and_start_at_the_same_index(self):
        (_, runs) = replay(((HIGH, HIGH, LOW, LOW, 0),), (1, 2, 2))
        positive, negative = runs
        self.assertEqual(positions(positive), (0, 2))
        self.assertEqual(positions(negative), (2, 4))
        self.assertEqual(positive.end_confirmed_sample_exclusive, ORIGIN + 3)
        self.assertTrue(positive.starts_at_epoch_origin)
        self.assertFalse(negative.starts_at_epoch_origin)

    def test_near_rail_repetitions_are_not_contacts(self):
        counts, runs = replay(((HIGH - 1, HIGH - 1, LOW + 1, LOW + 1),), (4,))
        self.assertEqual(runs, ())
        self.assertEqual((counts[0].positive_contacts, counts[0].negative_contacts), (0, 0))

    def test_valid_bits_set_both_rails_including_signed_32(self):
        for bits in (2, 16, 20, 24, 32):
            with self.subTest(bits=bits):
                profile = SignedPcmProfile(bits)
                low = -(1 << (bits - 1))
                high = -low - 1
                counts, runs = replay(((low, high, 0),), (3,), profile=profile)
                self.assertEqual([run.boundary for run in runs], [low, high])
                self.assertEqual((counts[0].negative_contacts, counts[0].positive_contacts), (1, 1))

    def test_channels_and_completion_order_survive_partition(self):
        epoch = replace(EPOCH, channel_ids=("Z", "A"))
        data = ((0, HIGH, HIGH, HIGH, 0, LOW, 0), (LOW, 0, 0, LOW, 0, HIGH, 0))
        whole = replay(data, (7,), epoch=epoch)
        self.assertEqual(whole, replay(data, (1, 2, 2, 2), epoch=epoch))
        self.assertEqual([run.channel_id for run in whole[1]], ["A", "Z", "A", "Z", "A"])
        self.assertEqual([positions(run) for run in whole[1]], [(0, 1), (1, 4), (3, 4), (5, 6), (5, 6)])


class BoundaryStateTests(unittest.TestCase):
    def test_gap_rejects_atomically_then_yields_separate_epoch_evidence(self):
        first = replace(EPOCH, origin_sample=10)
        detector = ClippingDetector(first, PCM16)
        ingest(detector, (HIGH,), epoch=first)
        with self.assertRaises(DiscontinuityError) as gap:
            ingest(detector, (HIGH,), epoch=first, start=12)
        self.assertEqual((gap.exception.kind, gap.exception.delta_samples), ("gap", 1))
        self.assertEqual(detector.next_sample, 11)
        second = replace(first, epoch_id="second", origin_sample=12)
        ended = detector.reset_epoch(second, reason="gap")
        self.assertEqual(ended.epoch, first)
        self.assertEqual(ended.observed_end_sample_exclusive, 11)
        (old,) = ended.completed_runs
        ingest(detector, (HIGH,), epoch=second)
        (new,) = detector.finish().completed_runs
        self.assertEqual((old.epoch_id, old.start_sample, old.end_sample_exclusive), ("first", 10, 11))
        self.assertEqual((new.epoch_id, new.start_sample, new.end_sample_exclusive), ("second", 12, 13))
        self.assertEqual((old.close_reason, new.close_reason), ("gap", "end_of_input"))
        for run in (old, new):
            self.assertIsNone(run.plateau_ready_sample_exclusive)
            self.assertIsNone(run.end_confirmed_sample_exclusive)

    def test_finalize_emits_a_boundary_once(self):
        detector = ClippingDetector(EPOCH, PCM16)
        ingest(detector, (HIGH, HIGH))
        first = detector.finish()
        second = detector.finish()
        (run,) = first.completed_runs
        self.assertEqual(run.close_reason, "end_of_input")
        self.assertEqual(positions(run), (0, 2))
        self.assertIsNone(run.end_confirmed_sample_exclusive)
        self.assertEqual(second.completed_runs, ())
        self.assertEqual(first.counts, second.counts)
        self.assertTrue(first.finalized and second.finalized)
        with self.assertRaisesRegex(ValueError, "finalizing"):
            ingest(detector, (HIGH,))

    def test_new_epoch_can_change_format_clock_and_channels(self):
        detector = ClippingDetector(EPOCH, PCM16)
        ingest(detector, (HIGH, HIGH))
        new = ScopeEpoch("new", 100, F(48000000, 1001), "new-clock", "new-tap", "FS", ("L", "R"))
        final = detector.reset_epoch(new, profile=FloatReferenceProfile())
        self.assertEqual(final.profile, PCM16)
        self.assertEqual(final.completed_runs[0].close_reason, "epoch_change")
        self.assertIsNone(final.completed_runs[0].end_confirmed_sample_exclusive)
        report = detector.ingest(epoch=new, start_sample=100, planes=((1.2,), (-.9,)))
        self.assertEqual(report.epoch, new)
        self.assertEqual([count.positive_exceedances for count in report.counts], [1, 0])
        self.assertEqual(report.open_runs[0].kind, "reference_exceedance")

    def test_overlap_and_reused_epoch_leave_the_existing_run_intact(self):
        detector = ClippingDetector(EPOCH, PCM16)
        ingest(detector, (HIGH,))
        with self.assertRaises(DiscontinuityError) as overlap:
            ingest(detector, (0,), start=ORIGIN)
        self.assertEqual(overlap.exception.kind, "overlap")
        with self.assertRaisesRegex(ValueError, "already been used"):
            detector.reset_epoch(replace(EPOCH, origin_sample=ORIGIN + 10))
        self.assertEqual(detector.next_sample, ORIGIN + 1)
        self.assertEqual(ingest(detector, (HIGH,)).open_runs[0].length, 2)
        detector.reset_epoch(replace(EPOCH, epoch_id="second"))
        with self.assertRaisesRegex(ValueError, "already been used"):
            detector.reset_epoch(EPOCH)

    def test_invalid_second_plane_does_not_commit_first_plane_evidence(self):
        epoch = replace(EPOCH, channel_ids=("L", "R"))
        detector = ClippingDetector(epoch, PCM16)
        detector.ingest(epoch=epoch, start_sample=ORIGIN, planes=((HIGH,), (LOW,)))
        for invalid in (32768, -32769, float(LOW), math.nan, True):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                detector.ingest(epoch=epoch, start_sample=ORIGIN + 1, planes=((HIGH, 0), (LOW, invalid)))
            self.assertEqual(detector.next_sample, ORIGIN + 1)
        update = detector.ingest(epoch=epoch, start_sample=ORIGIN + 1, planes=((HIGH, 0), (LOW, 0)))
        self.assertEqual([run.length for run in update.completed_runs], [2, 2])
        self.assertEqual([count.positive_contacts for count in update.counts], [2, 0])
        self.assertEqual([count.negative_contacts for count in update.counts], [0, 2])

    def test_epoch_and_block_geometry_validation(self):
        detector = ClippingDetector(EPOCH, PCM16)
        with self.assertRaisesRegex(ValueError, "current epoch"):
            ingest(detector, (HIGH,), epoch=replace(EPOCH, tap_id="wrong"))
        for planes in ((), ((),), ((0,) * (MAX_BLOCK_FRAMES + 1),), ((1,), (1,))):
            with self.subTest(planes=len(planes)), self.assertRaises(ValueError):
                detector.ingest(epoch=EPOCH, start_sample=ORIGIN, planes=planes)
        self.assertEqual(detector.next_sample, ORIGIN)

    def test_supported_exclusive_end_at_exact_sample_limit(self):
        epoch = replace(EPOCH, origin_sample=MAX_SAMPLE_INDEX - 2)
        detector = ClippingDetector(epoch, PCM16)
        ingest(detector, (HIGH, HIGH), epoch=epoch)
        with self.assertRaises(ValueError):
            ingest(detector, (0,), epoch=epoch)
        (run,) = detector.finish().completed_runs
        self.assertEqual(run.end_sample_exclusive, MAX_SAMPLE_INDEX)
        self.assertEqual(run.plateau_ready_sample_exclusive, MAX_SAMPLE_INDEX)
        self.assertIsNone(run.end_confirmed_sample_exclusive)


class FloatEvidenceTests(unittest.TestCase):
    def test_counts_equality_separately_and_tracks_excess_extremes(self):
        data = ((.8, 1, 1.125, 1.25, 1, -1.25, -1, 0),)
        whole = replay(data, (8,), profile=FloatReferenceProfile())
        self.assertEqual(whole, replay(data, (3, 2, 3), profile=FloatReferenceProfile()))
        (count,), (positive, negative) = whole
        self.assertEqual((count.positive_contacts, count.negative_contacts), (2, 1))
        self.assertEqual((count.positive_exceedances, count.negative_exceedances), (2, 1))
        self.assertEqual((positions(positive), positions(negative)), ((2, 4), (5, 6)))
        self.assertEqual((positive.extreme, negative.extreme), (1.25, -1.25))
        for run in (positive, negative):
            self.assertEqual(run.kind, "reference_exceedance")
            self.assertIsNone(run.plateau_ready_sample_exclusive)

    def test_asymmetric_references_and_signed_float_steps(self):
        profile = FloatReferenceProfile(-.5, .75)
        lower = math.nextafter(-.5, -math.inf)
        upper = math.nextafter(.75, math.inf)
        data = ((-.5, lower, -.875, lower, .75, upper, .75),)
        whole = replay(data, (7,), profile=profile)
        self.assertEqual(whole, replay(data, (2, 1, 4), profile=profile))
        (counts,), runs = whole
        self.assertEqual((counts.negative_contacts, counts.positive_contacts), (1, 2))
        self.assertEqual((counts.negative_exceedances, counts.positive_exceedances), (3, 1))
        self.assertEqual([run.boundary for run in runs], [-.5, .75])
        self.assertEqual([positions(run) for run in runs], [(1, 4), (5, 6)])
        self.assertEqual([run.extreme for run in runs], [-.875, upper])

    def test_repeated_exact_reference_values_register_contacts_only(self):
        counts, runs = replay(((1.0, 1.0, -1.0, -1.0, 0.0),), (5,), profile=FloatReferenceProfile())
        self.assertEqual(runs, ())
        self.assertEqual((counts[0].positive_contacts, counts[0].negative_contacts), (2, 2))

    def test_rejects_invalid_profiles(self):
        for valid, length in ((1, 2), (33, 2), (True, 2), (16, 1)):
            with self.subTest(valid=valid, length=length), self.assertRaises(ValueError):
                SignedPcmProfile(valid, length)
        for lower, upper in ((0, 1), (-1, 0), (-1, math.inf), (math.nan, 1), (-1, True), (-1, 2**2048)):
            with self.subTest(lower=lower, upper=upper), self.assertRaises(ValueError):
                FloatReferenceProfile(lower, upper)


class EncodedEvidenceTests(unittest.TestCase):
    def test_left_aligned_codes_use_the_valid_bit_rails(self):
        fmt = PCMFormat("s24", 1, valid_bits=20)
        detector = ClippingDetector(EPOCH, SignedPcmProfile(20))
        report = detector.ingest_pcm(
            epoch=EPOCH, start_sample=ORIGIN, payload=bytes.fromhex("00 00 80 F0 FF 7F"), fmt=fmt,
        )
        self.assertEqual(report.pcm_format, fmt)
        self.assertEqual(report.completed_runs[0].boundary, -524288)
        self.assertEqual(report.open_runs[0].boundary, 524287)

    def test_unsigned8_is_centered_before_rail_checks(self):
        detector = ClippingDetector(EPOCH, SignedPcmProfile(8))
        report = detector.ingest_pcm(epoch=EPOCH, start_sample=ORIGIN, payload=bytes((0, 128, 255)),
                                     fmt=PCMFormat("u8", 1))
        self.assertEqual(report.completed_runs[0].boundary, -128)
        self.assertEqual(report.open_runs[0].boundary, 127)

    def test_planar_and_byte_order_use_the_declared_format(self):
        epoch = replace(EPOCH, channel_ids=("L", "R"))
        fmt = PCMFormat("s16", 2, byte_order="big", layout="planar", channel_labels=("L", "R"))
        payload = [bytes.fromhex("80 00 00 00"), bytes.fromhex("7F FF 00 00")]
        report = ClippingDetector(epoch, PCM16).ingest_pcm(epoch=epoch, start_sample=ORIGIN, payload=payload, fmt=fmt)
        self.assertEqual([run.boundary for run in report.completed_runs], [LOW, HIGH])

    def test_decode_failure_or_mismatched_format_leaves_the_epoch_unchanged(self):
        detector = ClippingDetector(EPOCH, SignedPcmProfile(20))
        with self.assertRaisesRegex(ValueError, "unused low bits"):
            detector.ingest_pcm(epoch=EPOCH, start_sample=ORIGIN, payload=bytes.fromhex("F1 FF 7F"),
                                fmt=PCMFormat("s24", 1, valid_bits=20))
        for fmt in (PCMFormat("f32", 1), PCMFormat("s24", 1), PCMFormat("s24", 1, valid_bits=20, channel_labels=("R",))):
            with self.subTest(fmt=fmt), self.assertRaises(ValueError):
                detector.ingest_pcm(epoch=EPOCH, start_sample=ORIGIN, payload=b"", fmt=fmt)
        self.assertEqual(detector.next_sample, ORIGIN)

    def test_identical_codes_preserve_evidence_with_different_saturation_histories(self):
        fmt = PCMFormat("s16", 1)
        authored = encode_pcm([[0, HIGH/32768, HIGH/32768, 0]], fmt)
        over = encode_pcm([[0, 1.125, 1.125, 0]], fmt)
        self.assertEqual(authored["payload"], over["payload"])
        self.assertEqual((authored["saturated_samples_by_channel"], over["saturated_samples_by_channel"]), ([0], [2]))
        observed = tuple(ClippingDetector(EPOCH, PCM16).ingest_pcm(
            epoch=EPOCH, start_sample=ORIGIN, payload=encoded["payload"], fmt=fmt,
        ) for encoded in (authored, over))
        self.assertEqual(*observed)
        self.assertEqual(positions(observed[0].completed_runs[0]), (1, 3))

    def test_encoder_policy_differs_from_nominal_reference_evidence(self):
        fmt = PCMFormat("s16", 1)
        for value, code, clipped, excess in (
            (HIGH/32768, HIGH, 0, 0), (1-2**-17, HIGH, 1, 0), (1, HIGH, 1, 0),
            (-1, LOW, 0, 0), (-(1-2**-17), LOW, 0, 0), (-(1+2**-17), LOW, 1, 1),
        ):
            with self.subTest(value=value):
                encoded = encode_pcm([[value]], fmt)
                self.assertEqual(int.from_bytes(encoded["payload"], "little", signed=True), code)
                self.assertEqual(encoded["saturated_samples_by_channel"], [clipped])
                self.assertEqual(encoded["over_reference_samples_by_channel"], [excess])


class WaveformEvidenceTests(unittest.TestCase):
    def test_soft_saturation_adds_harmonics_below_the_reference(self):
        values = tuple(.8 * math.tanh(2 * math.sin(math.tau * (n % 48) / 48)) for n in range(480))
        counts, runs = replay((values,), (256, 224), profile=FloatReferenceProfile())
        self.assertEqual(runs, ())
        self.assertEqual((counts[0].negative_contacts, counts[0].positive_contacts), (0, 0))
        self.assertAlmostEqual(max(map(abs, values)), .7712220640606535, places=13)
        profile = ThdProfile(10)
        report = measure_thd_thdn(CaptureWindow(EPOCH, ORIGIN, (values,)), profile)
        self.assertAlmostEqual(math.sqrt(2 * float(report.bins[30].power)), .1509938598164597, places=12)

    def test_intersample_exceedance_can_coexist_with_no_sample_exceedance(self):
        sample_peak = 1.1/math.sqrt(2)
        values = (sample_peak, sample_peak, -sample_peak, -sample_peak) * 64
        counts, runs = replay((values,), (256,), profile=FloatReferenceProfile())
        self.assertEqual(runs, ())
        self.assertEqual((counts[0].negative_exceedances, counts[0].positive_exceedances), (0, 0))
        peak = experimental_peak_estimate(list(values), oversample_factor=8, radius=32, origin_sample=ORIGIN)
        self.assertLess(peak["sample_peak_amplitude"], 1)
        self.assertAlmostEqual(peak["supported_interior_estimate"]["peak_amplitude"], 1.100022630568014, places=12)
        self.assertAlmostEqual(peak["estimated"]["peak_amplitude"], 1.111405025195615, places=12)
        self.assertTrue(peak["peak_in_boundary_region"])


if __name__ == "__main__":
    unittest.main()
