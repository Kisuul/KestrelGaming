"""Adversarial raw PCM containers, calibration, layout and quantization fixtures."""
import io
import math
from pathlib import Path
import struct
import sys
import unittest
import wave

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/audio-sample-formats/scripts"))
sys.path.insert(0, str(ROOT / "skills/audio-rms-crest-factor/scripts"))
from reference_pcm import PCMFormat, decode_pcm, encode_pcm, MAX_REFERENCE_FRAMES
from reference_levels import sample_levels


class PCMReferenceTests(unittest.TestCase):
    def test_unsigned_u8_silence_negative_full_scale_positive_endpoint(self):
        f = PCMFormat("u8", 1)
        r = decode_pcm(bytes([0, 128, 255]), f)
        self.assertEqual(r["planar_samples"], [[-1.0, 0.0, 127/128]])
        self.assertEqual(encode_pcm(r["planar_samples"], f)["payload"], bytes([0, 128, 255]))

    def test_signed_s16_asymmetric_endpoints_and_zero(self):
        f = PCMFormat("s16", 1)
        b = bytes.fromhex("0080ff7f0000")
        r = decode_pcm(b, f)
        self.assertEqual(r["planar_samples"], [[-1.0, 32767/32768, 0.0]])
        self.assertEqual(encode_pcm(r["planar_samples"], f)["payload"], b)
        self.assertLess(r["planar_samples"][0][1], 1.0)

    def test_endianness_and_unambiguous_s24_sign_extension(self):
        for byte_order, minimum, maximum in (
            ("little", bytes.fromhex("000080"), bytes.fromhex("ffff7f")),
            ("big", bytes.fromhex("800000"), bytes.fromhex("7fffff")),
        ):
            with self.subTest(byte_order=byte_order):
                f = PCMFormat("s24", 1, byte_order=byte_order)
                r = decode_pcm(minimum + maximum, f)
                self.assertEqual(r["planar_samples"], [[-1.0, 8388607/8388608]])
                self.assertEqual(encode_pcm(r["planar_samples"], f)["payload"],
                                 minimum + maximum)

    def test_20_valid_bits_in_24_container_are_left_aligned(self):
        f = PCMFormat("s24", 1, valid_bits=20)
        raw = bytes.fromhex("f0ffffff7f000080")  # -1, +524287, -524288, shifted 4
        r = decode_pcm(raw, f)["planar_samples"][0]
        self.assertEqual(r, [-1/(2**19), (2**19-1)/(2**19), -1.0])
        self.assertEqual(encode_pcm([r], f)["payload"], raw)

    def test_20_valid_bit_nonzero_padding_is_rejected(self):
        f = PCMFormat("s24", 1, valid_bits=20)
        with self.assertRaises(ValueError):
            decode_pcm(bytes.fromhex("f1ffff"), f)
        with self.assertRaises(ValueError):
            decode_pcm(bytes.fromhex("010000"), f)

    def test_24_valid_bits_in_32_container(self):
        f = PCMFormat("s32", 1, valid_bits=24)
        raw = bytes.fromhex("00ffff7f00000080")  # left-aligned max24 and min24
        out = decode_pcm(raw, f)["planar_samples"][0]
        self.assertEqual(out, [(2**23-1)/2**23, -1.0])
        self.assertEqual(encode_pcm([out], f)["payload"], raw)

    def test_explicit_interleaved_stereo_frame_order(self):
        fmt = PCMFormat("s16", 2, channel_labels=("L", "R"))
        left = [0.5, -0.5]
        right = [-0.5, 0.5]
        raw = encode_pcm([left, right], fmt)
        self.assertEqual(raw["payload"], bytes.fromhex("004000c000c00040"))
        decoded = decode_pcm(raw["payload"], fmt)
        self.assertEqual(decoded["planar_samples"], [left, right])
        self.assertEqual(decoded["channel_labels"], ("L", "R"))
        self.assertAlmostEqual(sample_levels(decoded["planar_samples"][0])["rms"], 0.5)
        self.assertAlmostEqual(sample_levels(decoded["planar_samples"][1])["rms"], 0.5)

    def test_planar_payloads_are_not_interleaved(self):
        fmt = PCMFormat("s16", 2, layout="planar", channel_labels=("L", "R"))
        result = encode_pcm([[0.5, -0.5], [-0.5, 0.5]], fmt)
        self.assertEqual(result["payload"], [bytes.fromhex("004000c0"),
                                              bytes.fromhex("00c00040")])
        self.assertEqual(decode_pcm(result["payload"], fmt)["planar_samples"],
                         [[0.5, -0.5], [-0.5, 0.5]])

    def test_integer_ties_to_even_and_saturation_accounting(self):
        fmt = PCMFormat("s16", 1)
        x = [0.5/32768, 1.5/32768, -0.5/32768, -1.5/32768, 1., -1., 1.5, -1.5]
        encoded = encode_pcm([x], fmt)
        self.assertEqual(encoded["payload"],
                         b"".join(struct.pack("<h", k) for k in
                                  [0, 2, 0, -2, 32767, -32768, 32767, -32768]))
        self.assertEqual(encoded["saturated_samples_by_channel"], [3])
        self.assertEqual(encoded["over_reference_samples_by_channel"], [2])
        with self.assertRaises(ValueError):
            encode_pcm([[1.0]], fmt, integer_overflow="error")
        self.assertEqual(encode_pcm([[-1.0]], fmt, integer_overflow="error")
                         ["saturated_samples_by_channel"], [0])

    def test_u8_biased_quantization_rounds_ties_to_even(self):
        fmt = PCMFormat("u8", 1)
        self.assertEqual(encode_pcm([[0., 1/256, 3/256, 1.]], fmt)["payload"],
                         bytes([128, 128, 130, 255]))
        self.assertEqual(encode_pcm([[1.]], fmt)["saturated_samples_by_channel"], [1])

    def test_f32_preserves_finite_float_headroom_not_automatically_clipped(self):
        fmt = PCMFormat("f32", 2, byte_order="big", layout="interleaved")
        raw = struct.pack(">ffff", 1.25, -1.5, 0.0, 0.125)
        r = decode_pcm(raw, fmt)
        self.assertEqual(r["planar_samples"], [[1.25, 0.0], [-1.5, 0.125]])
        encoded = encode_pcm(r["planar_samples"], fmt)
        self.assertEqual(encoded["payload"], raw)
        self.assertEqual(encoded["saturated_samples_by_channel"], [0, 0])
        self.assertEqual(encoded["over_reference_samples_by_channel"], [1, 1])

    def test_f64_preserves_over_reference_and_negative_zero(self):
        fmt = PCMFormat("f64", 1)
        raw = struct.pack("<ddd", -0.0, 3.25, -4.5)
        dec = decode_pcm(raw, fmt)["planar_samples"][0]
        self.assertEqual(dec[1:], [3.25, -4.5])
        self.assertEqual(math.copysign(1.0, dec[0]), -1)
        self.assertEqual(encode_pcm([dec], fmt)["payload"], raw)

    def test_float32_underflow_is_flagged_not_misreported_as_input_silence(self):
        fmt = PCMFormat("f32", 1)
        result = encode_pcm([[-1e-50, 0., 1e-50]], fmt)
        self.assertEqual(result["float_underflow_to_zero_by_channel"], [2])
        v = decode_pcm(result["payload"], fmt)["planar_samples"][0]
        self.assertEqual(v, [0., 0., 0.])
        self.assertEqual(math.copysign(1., v[0]), -1.0)

    def test_nonfinite_float_payload_and_unrepresentable_f32_rejected(self):
        f = PCMFormat("f32", 1)
        for v in (math.inf, -math.inf, math.nan):
            with self.subTest(v=v):
                with self.assertRaises(ValueError):
                    decode_pcm(struct.pack("<f", v), f)
                with self.assertRaises(ValueError):
                    encode_pcm([[v]], f)
        with self.assertRaises(ValueError):
            encode_pcm([[1e100]], f)

    def test_byte_order_mismatch_is_not_a_valid_automatic_guess(self):
        little = PCMFormat("s16", 1, byte_order="little")
        big = PCMFormat("s16", 1, byte_order="big")
        raw = bytes.fromhex("0100")
        self.assertEqual(decode_pcm(raw, little)["planar_samples"], [[1/32768]])
        self.assertEqual(decode_pcm(raw, big)["planar_samples"], [[256/32768]])

    def test_full_width_integer_roundtrip_for_both_byte_orders(self):
        for kind, bits in (("u8", 8), ("s16", 16), ("s24", 24), ("s32", 32)):
            for order in ("little", "big"):
                with self.subTest(kind=kind, endian=order):
                    f = PCMFormat(kind, 1, byte_order=order)
                    s = 1 << (bits-1)
                    values = [0, 1, s-1, -s] if kind != "u8" else [0, 1, 127, -128]
                    x = [v/s for v in values]
                    result = encode_pcm([x], f)
                    self.assertEqual(decode_pcm(result["payload"], f)["planar_samples"], [x])

    def test_stdlib_wave_interoperability_on_pcm_bytes(self):
        for kind in ("u8", "s16"):
            fmt = PCMFormat(kind, 2)
            samples = [[-1.0, 0.5], [0.0, -0.5]]
            result = encode_pcm(samples, fmt)
            bio = io.BytesIO()
            with wave.open(bio, "wb") as out:
                out.setnchannels(2)
                out.setsampwidth(fmt.bytes_per_sample)
                out.setframerate(48000)
                out.writeframes(result["payload"])
            with wave.open(io.BytesIO(bio.getvalue()), "rb") as inp:
                self.assertEqual(inp.getnframes(), 2)
                self.assertEqual(inp.getsampwidth(), fmt.bytes_per_sample)
                self.assertEqual(inp.readframes(2), result["payload"])

    def test_invalid_format_metadata_fails_before_encoding(self):
        inputs = [
            dict(kind="s8", channels=1), dict(kind="s16", channels=0),
            dict(kind="s16", channels=True), dict(kind="s16", channels=9),
            dict(kind="f32", channels=1, valid_bits=24),
            dict(kind="u8", channels=1, valid_bits=7),
            dict(kind="s24", channels=1, valid_bits=25),
            dict(kind="s24", channels=1, valid_bits=True),
            dict(kind="s16", channels=1, byte_order="native"),
            dict(kind="s16", channels=1, layout="unknown"),
            dict(kind="s16", channels=2, channel_labels=("L",)),
            dict(kind="s16", channels=2, channel_labels=("L", "L")),
        ]
        for args in inputs:
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    PCMFormat(**args)

    def test_reject_malformed_buffers_or_mismatched_channel_count(self):
        a = PCMFormat("s16", 2)
        bad_interleaved = [b"", b"\x00", b"\x00\x00", b"\x00"* (a.bytes_per_frame*(MAX_REFERENCE_FRAMES+1))]
        for p in bad_interleaved:
            with self.subTest(length=len(p)):
                with self.assertRaises(ValueError):
                    decode_pcm(p, a)
        b = PCMFormat("s16", 2, layout="planar")
        for p in ([b"\x00\x00"], [b"\x00\x00", b"\x00"], [b"", b""],
                  [b"\x00\x00", "not bytes"]):
            with self.assertRaises(ValueError):
                decode_pcm(p, b)
        with self.assertRaises(ValueError):
            encode_pcm([[0.]], a)
        with self.assertRaises(ValueError):
            encode_pcm([[0.], [0., 1.]], a)
        with self.assertRaises(ValueError):
            encode_pcm([[0.], [0.]], a, integer_overflow="unbounded")
        with self.assertRaises(ValueError):
            encode_pcm([[True], [0.]], a)
        with self.assertRaises(ValueError):
            encode_pcm([[0.], [0.]], "not a format")


if __name__ == "__main__":
    unittest.main()
