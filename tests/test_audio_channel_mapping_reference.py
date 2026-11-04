"""Independent byte, matrix, headroom, metadata and time-continuity cases."""
import math
from fractions import Fraction
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/audio-channel-mapping/scripts"))
sys.path.insert(0, str(ROOT / "skills/audio-sample-formats/scripts"))
from reference_channel_mapping import (
    ChannelLayout, ChannelMatrix, ChannelMapStream, from_wave_mask,
    unassigned_layout, identity_matrix, reorder_matrix,
    mid_side_encode, mid_side_decode, apply_channel_matrix, MAX_FRAMES,
)
from reference_pcm import PCMFormat, encode_pcm, decode_pcm

STEREO = ChannelLayout(("FL", "FR"))
SURROUND_BACK = ChannelLayout(("FL", "FR", "FC", "LFE", "BL", "BR"))


class ChannelMappingTests(unittest.TestCase):
    def test_wave_mask_speaker_position_order(self):
        self.assertEqual(from_wave_mask(0x3, 2), STEREO)
        self.assertEqual(from_wave_mask(0x4, 1), ChannelLayout(("FC",)))
        self.assertEqual(from_wave_mask(0x3F, 6), SURROUND_BACK)
        self.assertEqual(from_wave_mask(0x60F, 6).labels,
                         ("FL", "FR", "FC", "LFE", "SL", "SR"))
        self.assertNotEqual(from_wave_mask(0x60F, 6), SURROUND_BACK)

    def test_wave_channel_count_only_is_not_assumed_stereo(self):
        for mask, channels in [(0, 2), (0, 1)]:
            with self.subTest(mask=mask, channels=channels):
                with self.assertRaises(ValueError):
                    from_wave_mask(mask, channels)
        unknown = from_wave_mask(0, 2, allow_unassigned=True)
        self.assertEqual(unknown, unassigned_layout(2))
        self.assertEqual(unknown.labels, ("CH0", "CH1"))
        self.assertNotEqual(unknown, STEREO)

    def test_wave_mask_invalid_or_ambiguous_rejected(self):
        for mask, channels in [(0x3F, 2), (0x3, 1), (0x40000, 1),
                               (1, 0), (-1, 1), (True, 1),
                               (0x3, 9), (0x3, True), (0, 9)]:
            with self.subTest(mask=mask, channels=channels):
                with self.assertRaises(ValueError):
                    from_wave_mask(mask, channels, allow_unassigned=True)

    def test_layout_kind_and_labels_enforced(self):
        for labels, kind in [
            (("FL", "FL"), "speaker"), (("FL", "CH1"), "speaker"),
            (("FL", ""), "speaker"), ((), "speaker"),
            (("M", "S"), "speaker"), (("CH0", "CH0"), "discrete"),
            (("FL", "FR"), "mid_side"), (("S", "M"), "mid_side"),
            (("CH0",), "unrecognized"), (("CH0",), "speaker"),
            (["FL", "FR"], "speaker"),
            (("FL",) * 9, "speaker"),
        ]:
            with self.subTest(labels=labels, kind=kind):
                with self.assertRaises(ValueError):
                    ChannelLayout(labels, kind)

    def test_identity_preserves_exact_values_signed_zero_and_headroom(self):
        x = [[-0.0, 0.25, 1.75], [0.0, -0.5, -1.25]]
        r = apply_channel_matrix(x, identity_matrix(STEREO),
                                 epoch_id="one", start_sample=2**54 + 5)
        self.assertEqual(r["planar_samples"], x)
        self.assertEqual(math.copysign(1, r["planar_samples"][0][0]), -1)
        self.assertEqual(r["over_reference_by_output"], [1, 1])
        self.assertEqual(r["coherent_gain_bounds"], (Fraction(1), Fraction(1)))
        self.assertEqual(r["end_sample_exclusive"], 2**54 + 8)
        self.assertEqual(r["matrix_rank"], 2)
        self.assertFalse(r["loses_linear_information"])
        self.assertFalse(r["clipped"])

    def test_explicit_stereo_swap_is_a_permutation_not_a_downmix(self):
        swapped = ChannelLayout(("FR", "FL"))
        p = reorder_matrix(STEREO, swapped)
        self.assertEqual(p.coefficients, ((Fraction(0), Fraction(1)),
                                          (Fraction(1), Fraction(0))))
        o = apply_channel_matrix([[1, 2], [3, 4]], p,
                                 epoch_id="e", start_sample=0)
        self.assertEqual(o["planar_samples"], [[3., 4.], [1., 2.]])
        self.assertEqual(o["output_labels"], ("FR", "FL"))
        self.assertFalse(o["loses_linear_information"])
        with self.assertRaises(ValueError):
            reorder_matrix(STEREO, ChannelLayout(("FL", "FC")))

    def test_stereo_to_mono_anti_phase_cancellation_is_information_loss(self):
        center = ChannelLayout(("FC",))
        p = ChannelMatrix(STEREO, center, ((Fraction(1, 2), Fraction(1, 2)),),
                          "equal-gain average; not a standard downmix preset")
        x = [[1, -1, 0.25, 0.5], [-1, 1, -0.25, 0.5]]
        out = apply_channel_matrix(x, p, epoch_id="e", start_sample=0)
        self.assertEqual(out["planar_samples"], [[0., 0., 0., 0.5]])
        self.assertEqual(p.rank, 1)
        self.assertTrue(p.loses_linear_information)
        self.assertEqual(p.dropped_source_labels, ())
        self.assertEqual(p.coherent_gain_bounds, (Fraction(1),))

    def test_mid_side_encode_decode_analytic_vectors(self):
        x = [[1., -1., 0.5, 0.125], [1., 1., -0.5, -0.125]]
        encoded = apply_channel_matrix(x, mid_side_encode(),
                                       epoch_id="e", start_sample=11)
        self.assertEqual(encoded["planar_samples"],
                         [[1.0, 0.0, 0.0, 0.0], [0.0, -1.0, 0.5, 0.125]])
        restored = apply_channel_matrix(encoded["planar_samples"], mid_side_decode(),
                                        epoch_id="e", start_sample=11)
        self.assertEqual(restored["planar_samples"], x)
        self.assertFalse(restored["loses_linear_information"])
        self.assertEqual(restored["coherent_gain_bounds"],
                         (Fraction(2), Fraction(2)))
        self.assertEqual(restored["end_sample_exclusive"], 15)

    def test_mid_side_cancellation_and_polarity_are_not_spatial_panning(self):
        encoded = apply_channel_matrix([[0.5], [-0.5]], mid_side_encode(),
                                       epoch_id="e", start_sample=0)
        self.assertEqual(encoded["planar_samples"], [[0.], [0.5]])
        self.assertEqual(encoded["output_kind"], "mid_side")

    def test_manual_5point1_downmix_is_not_claimed_normative(self):
        p = ChannelMatrix(SURROUND_BACK, STEREO,
                          ((1, 0, Fraction(1, 2), 0, Fraction(1, 2), 0),
                           (0, 1, Fraction(1, 2), 0, 0, Fraction(1, 2))),
                          "test-only nonnormative 5.1 rear to stereo coefficient example",
                          allow_drop=True, allow_possible_peak_gain=True)
        self.assertEqual(p.dropped_source_labels, ("LFE",))
        self.assertEqual(p.coherent_gain_bounds, (Fraction(2), Fraction(2)))
        channels = [
            [1, 0, 0, 0],  # FL
            [0, 1, 0, 0],  # FR
            [0, 0, 1, 0],  # FC
            [0, 0, 0, 0],  # LFE
            [0, 0, 0, 1],  # BL
            [0, 0, 0, 1],  # BR
        ]
        o = apply_channel_matrix(channels, p, epoch_id="a", start_sample=0)
        self.assertEqual(o["planar_samples"],
                         [[1., 0., 0.5, 0.5], [0., 1., 0.5, 0.5]])
        self.assertEqual(o["matrix_rank"], 2)
        self.assertTrue(o["loses_linear_information"])

    def test_lfe_not_automatically_redirected_or_dropped(self):
        p = ChannelMatrix(SURROUND_BACK, STEREO,
                          ((1, 0, 0, 0, 0, 0),
                           (0, 1, 0, 0, 0, 0)),
                          "front-only test routing with explicit discard",
                          allow_drop=True)
        source = [[0], [0], [0], [0.75], [0], [0]]
        o = apply_channel_matrix(source, p, epoch_id="e", start_sample=0)
        self.assertEqual(o["planar_samples"], [[0.], [0.]])
        self.assertIn("LFE", o["dropped_source_labels"])
        with self.assertRaises(ValueError):
            ChannelMatrix(SURROUND_BACK, STEREO, p.coefficients,
                          "same mapping with no discard acknowledgement")

    def test_no_automatic_surround_upmix(self):
        p = ChannelMatrix(STEREO, SURROUND_BACK,
                          ((1, 0), (0, 1), (0, 0), (0, 0), (0, 0), (0, 0)),
                          "front-only zero-filled extra channels",
                          allow_silent_outputs=True)
        r = apply_channel_matrix([[0.25], [-0.25]], p,
                                 epoch_id="e", start_sample=1)
        self.assertEqual(r["planar_samples"],
                         [[0.25], [-0.25], [0.], [0.], [0.], [0.]])
        self.assertEqual(r["silent_target_labels"], ("FC", "LFE", "BL", "BR"))
        with self.assertRaises(ValueError):
            ChannelMatrix(STEREO, SURROUND_BACK, p.coefficients,
                          "undeclared silence")

    def test_mixing_more_than_unity_requires_acknowledged_headroom(self):
        with self.assertRaises(ValueError):
            ChannelMatrix(STEREO, ChannelLayout(("FC",)), ((1, 1),),
                          "coherent sum without a headroom warning")
        p = ChannelMatrix(STEREO, ChannelLayout(("FC",)), ((1, 1),),
                          "intentional coherent sum", allow_possible_peak_gain=True)
        r = apply_channel_matrix([[0.8], [0.7]], p, epoch_id="e", start_sample=0)
        self.assertAlmostEqual(r["planar_samples"][0][0], 1.5, delta=1e-15)
        self.assertEqual(r["over_reference_by_output"], [1])
        self.assertFalse(r["clipped"])
        self.assertEqual(p.coherent_gain_bounds, (Fraction(2),))

    def test_discrete_channels_require_explicit_association(self):
        discrete = unassigned_layout(2)
        with self.assertRaises(ValueError):
            ChannelMatrix(discrete, STEREO, ((1, 0), (0, 1)),
                          "silent assumption that CH0/CH1 are L/R")
        p = ChannelMatrix(discrete, STEREO, ((1, 0), (0, 1)),
                          "human-provided CH0->FL CH1->FR",
                          acknowledge_discrete_to_speaker=True)
        r = apply_channel_matrix([[0.75], [-0.5]], p,
                                 epoch_id="e", start_sample=0)
        self.assertEqual(r["planar_samples"], [[0.75], [-0.5]])
        self.assertEqual(r["input_kind"], "discrete")

    def test_require_exact_nonfloating_coefficients(self):
        for coefficient in (0.5, float("nan"), float("inf"), True, "1/2", 17):
            with self.subTest(coefficient=coefficient):
                with self.assertRaises(ValueError):
                    ChannelMatrix(STEREO, ChannelLayout(("FC",)),
                                  ((coefficient, 0),), "invalid coefficient",
                                  allow_drop=True, allow_possible_peak_gain=True)
        self.assertEqual(ChannelMatrix(STEREO, ChannelLayout(("FC",)),
                                       ((Fraction(1, 2), Fraction(1, 2)),),
                                       "exact half").coefficients[0][0],
                         Fraction(1, 2))

    def test_matrix_shape_and_purpose_are_rejected_early(self):
        errors = [
            ((1, 0),), ((1,), (0,)), ((), ()),
            ((1, 0), (0, 1), (0, 0)), "bad matrix",
        ]
        for mat in errors:
            with self.subTest(mat=mat):
                with self.assertRaises(ValueError):
                    ChannelMatrix(STEREO, STEREO, mat, "shape check")
        with self.assertRaises(ValueError):
            ChannelMatrix(STEREO, STEREO, ((1, 0), (0, 1)), "")
        with self.assertRaises(ValueError):
            ChannelMatrix(STEREO, STEREO, ((1, 0), (0, 1)),
                          "bool opt-in", allow_drop=1)

    def test_wave_5point1_lfe_and_surround_order_is_exact(self):
        back = from_wave_mask(0x3F, 6)
        side = from_wave_mask(0x60F, 6)
        with self.assertRaises(ValueError):
            reorder_matrix(back, side)
        self.assertEqual(back.labels[4:], ("BL", "BR"))
        self.assertEqual(side.labels[4:], ("SL", "SR"))

    def test_streaming_arbitrary_partitions_match_offline(self):
        start = 2**54 + 123
        x = [[((i % 7) - 3) / 8 for i in range(97)],
             [((i % 11) - 5) / 8 for i in range(97)]]
        p = mid_side_encode()
        whole = apply_channel_matrix(x, p, epoch_id="z", start_sample=start)
        for schedule in ((97,), (1,), (2, 9, 11), (7, 3)):
            with self.subTest(schedule=schedule):
                stream = ChannelMapStream(p, "z", start)
                output = [[], []]
                index = 0
                count = 0
                while index < 97:
                    n = min(schedule[count % len(schedule)], 97 - index)
                    part = [c[index:index+n] for c in x]
                    block = stream.push(start + index, part)
                    self.assertEqual(block["start_sample"], start + index)
                    self.assertEqual(block["end_sample_exclusive"], start + index + n)
                    for j in range(2):
                        output[j].extend(block["planar_samples"][j])
                    index += n
                    count += 1
                self.assertEqual(output, whole["planar_samples"])
                self.assertEqual(stream.next_sample, start + 97)
                self.assertEqual(stream.accepted_blocks, count)

    def test_bad_stream_blocks_do_not_advance_state(self):
        s = ChannelMapStream(identity_matrix(STEREO), "a", 100)
        s.push(100, [[0.5], [-0.5]])
        before = (s.next_sample, s.accepted_blocks)
        bad = [(99, [[0], [0]]), (102, [[0], [0]]),
               (101, [[0.0]]), (101, [[], []]),
               (101, [[1.0], [1.0, 1.0]]), (101, [[True], [0.]]),
               (101, [[math.nan], [0.]]), (101, [[math.inf], [0.]])]
        for at, data in bad:
            with self.subTest(start=at, data=repr(data)):
                with self.assertRaises(ValueError):
                    s.push(at, data)
                self.assertEqual((s.next_sample, s.accepted_blocks), before)

    def test_arithmetic_overflow_is_atomic(self):
        p = ChannelMatrix(STEREO, ChannelLayout(("FC",)), ((1, 1),),
                          "intentional extreme sum", allow_possible_peak_gain=True)
        stream = ChannelMapStream(p, "e", 0)
        with self.assertRaises(ValueError):
            stream.push(0, [[1e308], [1e308]])
        self.assertEqual(stream.next_sample, 0)
        self.assertEqual(stream.accepted_blocks, 0)

    def test_stream_epoch_reassignment_requires_explicit_unique_id(self):
        stream = ChannelMapStream(identity_matrix(STEREO), "old", 400)
        stream.push(400, [[1.], [0.]])
        other = ChannelLayout(("FC",))
        newplan = ChannelMatrix(STEREO, other,
                                ((Fraction(1, 2), Fraction(1, 2)),),
                                "mono test")
        for epoch, origin, plan in [("old", 100, newplan),
                                    ("second", -1, newplan),
                                    ("second", 100, "not a plan")]:
            with self.subTest(epoch=epoch, origin=origin):
                with self.assertRaises(ValueError):
                    stream.reset_epoch(epoch, origin, plan)
                self.assertEqual((stream.epoch_id, stream.next_sample,
                                  stream.accepted_blocks), ("old", 401, 1))
        stream.reset_epoch("second", 900, newplan)
        out = stream.push(900, [[1.], [1.]])
        self.assertEqual((out["output_labels"], out["start_sample"]),
                         (("FC",), 900))
        with self.assertRaises(ValueError):
            stream.reset_epoch("old", 0)
        stream.reset_epoch("third", 10)
        self.assertEqual(stream.epoch_id, "third")

    def test_frame_limit_and_nan_rejection(self):
        p = identity_matrix(STEREO)
        for data in ([[], []], [[0] * (MAX_FRAMES+1), [0] * (MAX_FRAMES+1)],
                     [[0], [complex(0)]], [[0], [None]], [[0], [10**400]]):
            with self.subTest(length=repr(data)[:40]):
                with self.assertRaises(ValueError):
                    apply_channel_matrix(data, p, epoch_id="e", start_sample=0)
        for start in (-1, True):
            with self.assertRaises(ValueError):
                apply_channel_matrix([[0], [0]], p, epoch_id="e", start_sample=start)

    def test_input_buffers_remain_unchanged(self):
        left = [0., 1., -1.]
        right = [0.5, 0.25, -0.25]
        r = apply_channel_matrix([left, right], mid_side_encode(),
                                 epoch_id="e", start_sample=3)
        self.assertEqual((left, right), ([0., 1., -1.], [0.5, 0.25, -0.25]))
        self.assertIsNot(r["planar_samples"][0], left)

    def test_cross_skill_pcm_bytes_preserve_channels(self):
        pcm = PCMFormat("s16", 2, byte_order="little", channel_labels=("L", "R"))
        raw = encode_pcm([[0.5, -0.5], [-0.5, 0.5]], pcm)["payload"]
        self.assertEqual(raw, bytes.fromhex("004000c000c00040"))
        decoded = decode_pcm(raw, pcm)["planar_samples"]
        mapped = apply_channel_matrix(decoded, reorder_matrix(STEREO, ChannelLayout(("FR", "FL"))),
                                      epoch_id="e", start_sample=2**54)
        self.assertEqual(mapped["planar_samples"], [[-0.5, 0.5], [0.5, -0.5]])
        self.assertEqual(mapped["frames"], 2)


if __name__ == "__main__":
    unittest.main()
