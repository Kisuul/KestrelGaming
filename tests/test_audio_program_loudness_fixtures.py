"""Fixture identity/error checks with synthetic bytes, never EBU compliance evidence.

Tests patch the official digest only inside individual synthetic-archive checks;
there is no runtime nonofficial mode or digest override.
"""
import contextlib
import hashlib
import io
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
import warnings
import wave
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] /
                       "skills/audio-program-loudness/scripts"))
import check_ebu_loudness as checker


FIXTURES = tuple(checker._fixtures())


def synthetic_zip(path, *, omit=None, duplicate=False):
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for _, name, _ in FIXTURES:
            if name != omit:
                archive.writestr(name, b"synthetic parser fixture, not EBU audio")
        if duplicate:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                archive.writestr(FIXTURES[0][1], b"duplicate")


def waveex_case6(*, truncate=0, extra=b""):
    """20 s, six-channel PCM with the original case-6 RIFF/data discrepancy."""
    frames = 960_000
    pcm_guid = bytes.fromhex("0100000000001000800000aa00389b71")
    fmt = struct.pack("<HHIIHHHHI", 0xFFFE, 6, 48_000, 576_000, 12, 16, 22, 16, 0x3F)
    fmt += pcm_guid
    data = bytes((frames - 1) * 12) + bytes(range(12))
    body = (b"WAVEfmt " + struct.pack("<I", len(fmt)) + fmt +
            b"fact" + struct.pack("<II", 4, frames) +
            b"data" + struct.pack("<I", len(data)) + data)
    result = b"RIFF" + struct.pack("<I", len(body) - 12) + body
    return (result[:-truncate] if truncate else result) + extra


class OfficialArchiveIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "synthetic.zip"

    def matching_test_digest(self):
        return patch.object(checker, "_OFFICIAL_SHA256",
                            hashlib.sha256(self.path.read_bytes()).hexdigest())

    def test_wrong_hash_rejected_before_zip_parse_or_measurement(self):
        synthetic_zip(self.path)
        output, errors = io.StringIO(), io.StringIO()
        with patch.object(checker.zipfile, "ZipFile") as parser, \
                patch.object(checker, "_measure") as measure, \
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            self.assertEqual(checker.main([str(self.path)]), 2)
        parser.assert_not_called()
        measure.assert_not_called()
        self.assertIn("Verification mode: official EBU v5.0", output.getvalue())
        self.assertIn(hashlib.sha256(self.path.read_bytes()).hexdigest(), output.getvalue())
        self.assertIn("SHA-256 mismatch", errors.getvalue())
        self.assertNotIn("files passed", output.getvalue())

    def test_matching_test_hash_and_all_expected_entries(self):
        synthetic_zip(self.path)
        with self.matching_test_digest(), contextlib.redirect_stdout(io.StringIO()):
            with checker._official_archive(self.path) as archive:
                self.assertEqual(len(archive.namelist()), 53)
                self.assertEqual(archive.read(FIXTURES[-1][1]),
                                 b"synthetic parser fixture, not EBU audio")

    def test_matching_digest_does_not_excuse_missing_entry(self):
        name = FIXTURES[-1][1]
        synthetic_zip(self.path, omit=name)
        with self.matching_test_digest(), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(ValueError, "missing fixture entry: " + name):
                with checker._official_archive(self.path):
                    self.fail("missing fixture admitted")

    def test_duplicate_entry_rejected(self):
        synthetic_zip(self.path, duplicate=True)
        with self.matching_test_digest(), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(ValueError, "duplicate ZIP entry"):
                with checker._official_archive(self.path):
                    self.fail("duplicate fixture admitted")

    def test_encrypted_entry_rejected_before_measurement(self):
        synthetic_zip(self.path)
        data = bytearray(self.path.read_bytes())
        central = data.index(b"PK\x01\x02")
        # ZIP central directory general-purpose flags are at offset 8.
        flags = struct.unpack_from("<H", data, central + 8)[0]
        struct.pack_into("<H", data, central + 8, flags | 1)
        self.path.write_bytes(data)
        with self.matching_test_digest(), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(ValueError, "encrypted ZIP entry"):
                with checker._official_archive(self.path):
                    self.fail("encrypted entry admitted")

    def test_malformed_archive_reports_clear_error(self):
        self.path.write_bytes(b"not a ZIP")
        errors = io.StringIO()
        with self.matching_test_digest(), contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(errors):
            self.assertEqual(checker.main([str(self.path)]), 2)
        self.assertIn("Fixture verification error:", errors.getvalue())
        self.assertIn("not a zip file", errors.getvalue())

    def test_missing_file_reports_clear_error(self):
        errors = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(errors):
            self.assertEqual(checker.main([str(self.path)]), 2)
        self.assertIn("Fixture verification error:", errors.getvalue())

    def test_archive_entry_and_expanded_size_bounds(self):
        synthetic_zip(self.path)
        for bound, limit, message in (
            ("_MAX_ARCHIVE_BYTES", 4, "archive exceeds size limit"),
            ("_MAX_ENTRIES", 52, "too many ZIP entries"),
            ("_MAX_ENTRY_BYTES", 4, "entry exceeds size limit"),
            ("_MAX_EXPANDED_BYTES", 4, "expanded size exceeds limit"),
        ):
            with self.subTest(bound=bound), self.matching_test_digest(), \
                    patch.object(checker, bound, limit), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(ValueError, message):
                    with checker._official_archive(self.path):
                        self.fail("resource limit bypassed")

    def test_bogus_wave_reports_clear_error(self):
        synthetic_zip(self.path)
        errors = io.StringIO()
        with self.matching_test_digest(), contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(errors):
            self.assertEqual(checker.main([str(self.path)]), 2)
        self.assertIn("Fixture verification error:", errors.getvalue())

    def test_excessive_declared_pcm_frames_rejected_before_processing(self):
        # Tiny RIFF declares a data length beyond the PCM work budget.
        header = (b"RIFF" + struct.pack("<I", 36) + b"WAVEfmt " +
                  struct.pack("<IHHIIHH", 16, 1, 2, 48_000, 192_000, 4, 16) +
                  b"data" + struct.pack("<I", 48_000 * 301 * 4))
        with zipfile.ZipFile(self.path, "w") as archive:
            archive.writestr(FIXTURES[0][1], header)
        with zipfile.ZipFile(self.path) as archive, patch.object(checker, "ProgramLoudnessStream") as meter:
            with self.assertRaisesRegex(ValueError, "PCM frame count exceeds limits"):
                checker._measure(archive, FIXTURES[0][1], ("L", "R"))
        meter.assert_not_called()


class Case6WaveexTests(unittest.TestCase):
    def test_last_frame_beyond_riff_end_is_preserved(self):
        source = io.BytesIO(waveex_case6())
        with wave.open(source, "rb") as pcm:
            self.assertEqual((pcm.getnchannels(), pcm.getsampwidth(), pcm.getnframes()),
                             (6, 2, 960_000))
            chunks = list(checker._pcm_chunks(pcm, source, checker._SIX_FIXTURE))
        self.assertEqual(sum(map(len, chunks)), 960_000 * 12)
        self.assertEqual(chunks[-1], bytes(range(12)))

    def test_truncated_or_extra_trailer_is_not_silently_repaired(self):
        for data in (waveex_case6(truncate=1), waveex_case6(extra=b"x")):
            with self.subTest(size=len(data)):
                source = io.BytesIO(data)
                with wave.open(source, "rb") as pcm:
                    with self.assertRaisesRegex(ValueError, "truncated PCM"):
                        list(checker._pcm_chunks(pcm, source, checker._SIX_FIXTURE))

    def test_workaround_is_restricted_to_named_fixture(self):
        source = io.BytesIO(waveex_case6())
        with wave.open(source, "rb") as pcm:
            with self.assertRaisesRegex(ValueError, "truncated PCM"):
                list(checker._pcm_chunks(pcm, source, "unrelated.wav"))

    def test_incomplete_interleaved_frame_rejected(self):
        with self.assertRaisesRegex(ValueError, "incomplete PCM frame"):
            checker._decode_planes(b"\x00", 2, 6)


if __name__ == "__main__":
    unittest.main()
