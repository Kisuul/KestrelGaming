"""Check Tech 3341 loudness against a separately obtained EBU v5.0 ZIP.

Python 3.12+ is needed for wave's WAVE_FORMAT_EXTENSIBLE support. This check
reads PCM without extraction, playback, resampling, or network access.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import math
from pathlib import Path
import sys
import wave
import zipfile

from reference_program_loudness import LoudnessConfig, ProgramLoudnessStream


_STEREO = ("L", "R")
_FIVE = ("L", "R", "C", "LS", "RS")
_SIX = ("L", "R", "C", "LFE", "LS", "RS")
_SIX_FIXTURE = "seq-3341-6-6channels-WAVEEX-16bit.wav"
_TOLERANCE_LU = 0.1  # Tech 3341 v4 Table 1
_OFFICIAL_SHA256 = "9cc500b4df83f7c21855c74dce795ef5209a752bf884253ae57d0ce512efb062"
# Deliberately generous bounds for the pinned v5.0 release, not general ZIP support.
_MAX_ARCHIVE_BYTES = 1 << 30
_MAX_ENTRIES = 256
_MAX_ENTRY_BYTES = 256 << 20
_MAX_EXPANDED_BYTES = 2 << 30
# Longest measured case is case 8: 246.357334 seconds; allow up to five minutes.
_MAX_PCM_FRAMES = 48_000 * 300


def _validate_entries(archive):
    entries = archive.infolist()
    if len(entries) > _MAX_ENTRIES:
        raise ValueError("too many ZIP entries")
    names = [entry.filename for entry in entries]
    if len(set(names)) != len(names):
        raise ValueError("duplicate ZIP entry")
    if sum(entry.file_size for entry in entries) > _MAX_EXPANDED_BYTES:
        raise ValueError("ZIP expanded size exceeds limit")
    for entry in entries:
        if entry.file_size > _MAX_ENTRY_BYTES:
            raise ValueError(f"ZIP entry exceeds size limit: {entry.filename}")
        if entry.flag_bits & 1:
            raise ValueError(f"encrypted ZIP entry: {entry.filename}")
    for _, name, _ in _fixtures():
        if name not in names or archive.getinfo(name).is_dir():
            raise ValueError(f"missing fixture entry: {name}")


@contextmanager
def _official_archive(path):
    # Hash and parse the same open file; reject unpinned bytes before ZIP parsing.
    print("Verification mode: official EBU v5.0 (pinned SHA-256)", flush=True)
    with path.open("rb") as source:
        digest = hashlib.sha256()
        size = 0
        while chunk := source.read(1 << 20):
            size += len(chunk)
            if size > _MAX_ARCHIVE_BYTES:
                raise ValueError("archive exceeds size limit")
            digest.update(chunk)
        observed = digest.hexdigest()
        print(f"Archive SHA-256: {observed}", flush=True)
        if observed != _OFFICIAL_SHA256:
            raise ValueError(f"official archive SHA-256 mismatch; expected {_OFFICIAL_SHA256}")
        source.seek(0)
        with zipfile.ZipFile(source) as archive:
            _validate_entries(archive)
            yield archive


def _fixtures():
    yield 1, "seq-3341-1-16bit.wav", _STEREO
    yield 2, "seq-3341-2-16bit.wav", _STEREO
    for case in (3, 4, 5):
        yield case, f"seq-3341-{case}-16bit-v02.wav", _STEREO
    # The v5.0 archive README specifies the orders of the two versions of case 6.
    yield 6, "seq-3341-6-5channels-16bit.wav", _FIVE
    yield 6, _SIX_FIXTURE, _SIX
    yield 7, "seq-3341-7_seq-3342-5-24bit.wav", _STEREO
    yield 8, "seq-3341-2011-8_seq-3342-6-24bit-v02.wav", _STEREO
    yield 9, "seq-3341-9-24bit.wav", _STEREO
    for number in range(1, 21):
        yield 10, f"seq-3341-10-{number}-24bit.wav", _STEREO
    yield 11, "seq-3341-11-24bit.wav", _STEREO
    yield 12, "seq-3341-12-24bit.wav", _STEREO
    for number in range(1, 21):
        extension = ".wav" if number <= 2 else ".wav.wav"
        yield 13, f"seq-3341-13-{number}-24bit{extension}", _STEREO
    yield 14, "seq-3341-14-24bit.wav.wav", _STEREO


def _decode_planes(data, width, channels):
    if len(data) % (width * channels):
        raise ValueError("incomplete PCM frame")
    scale = 1 << (8 * width - 1)
    interleaved = [int.from_bytes(data[start:start + width], "little", signed=True) / scale
                   for start in range(0, len(data), width)]
    return [interleaved[index::channels] for index in range(channels)]


def _pcm_chunks(pcm, source, name):
    frame_bytes = pcm.getnchannels() * pcm.getsampwidth()
    remaining = pcm.getnframes()
    while data := pcm.readframes(8192):
        remaining -= len(data) // frame_bytes
        yield data
    if remaining == 0:
        return

    # This v5.0 WAV has one data frame beyond the declared RIFF end. Read
    # the original frame from the ZIP stream rather than rewriting the WAV.
    if (name == _SIX_FIXTURE and remaining == 1 and frame_bytes == 12
            and pcm.getnframes() == 960_000 and source.tell() == 11_520_068):
        final_frame = source.read(frame_bytes + 1)
        if len(final_frame) == frame_bytes:
            yield final_frame
            return
    raise ValueError(f"truncated PCM: {name}")


def _measure(archive, name, labels):
    momentary, short_term = [], []
    with archive.open(name) as source, wave.open(source, "rb") as pcm:
        rate, channels, width = pcm.getframerate(), pcm.getnchannels(), pcm.getsampwidth()
        if rate != 48_000 or channels != len(labels) or width not in (2, 3):
            raise ValueError(f"unexpected PCM format: {name}")
        if not 0 < pcm.getnframes() <= _MAX_PCM_FRAMES:
            raise ValueError(f"PCM frame count exceeds limits: {name}")
        config = LoudnessConfig(rate, labels, "EBU v5.0 test PCM")
        meter = ProgramLoudnessStream(config, epoch_id=name, start_sample=0)
        for data in _pcm_chunks(pcm, source, name):
            planes = _decode_planes(data, width, channels)
            result = meter.push(meter.next_sample, planes, epoch_id=name)
            momentary.extend(result["momentary"])
            short_term.extend(result["short_term"])
    return meter.integrated()["gating"].integrated_lufs, momentary, short_term


def _segment_maxima(windows, length):
    for index in range(20):
        start, end = index * length, (index + 1) * length
        contained = (window.lufs for window in windows
                     if start <= window.start_sample and window.end_sample_exclusive <= end)
        yield max(contained), -38 + index


def _observations(case, integrated, momentary, short_term):
    if case in (1, 2):
        target = -23 if case == 1 else -33
        return [(integrated, target)] + [(window.lufs, target) for window in momentary + short_term]
    if case <= 8:
        return [(integrated, -23)]
    if case == 9:
        return [(window.lufs, -23) for window in short_term if window.end_sample_exclusive >= 144_000]
    if case == 10:
        return [(max(window.lufs for window in short_term), -23)]
    if case == 11:
        return list(_segment_maxima(short_term, 288_000))
    if case == 12:
        return [(window.lufs, -23) for window in momentary if window.end_sample_exclusive >= 48_000]
    if case == 13:
        return [(max(window.lufs for window in momentary), -23)]
    return list(_segment_maxima(momentary, 38_400))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="EBU Loudness Test Set v5.0 ZIP")
    args = parser.parse_args(argv)
    total = failed = 0
    worst = 0.0
    print("Test sequences © EBU. Offline M/S/I window and gate checks.", flush=True)
    try:
        with _official_archive(args.archive) as archive:
            for case, name, labels in _fixtures():
                observations = _observations(case, *_measure(archive, name, labels))
                errors = [abs(actual - expected) if actual is not None and math.isfinite(actual) else math.inf
                          for actual, expected in observations]
                largest = max(errors, default=math.inf)
                passed = largest <= _TOLERANCE_LU
                total += 1
                failed += not passed
                worst = max(worst, largest)
                print(f"{case:2d}  {name}: {'PASS' if passed else 'FAIL'}  max error {largest:.6f} LU",
                      flush=True)
    except (OSError, ValueError, EOFError, zipfile.BadZipFile, wave.Error) as exc:
        print(f"Fixture verification error: {exc}", file=sys.stderr)
        return 2
    print(f"{total - failed}/{total} files passed, worst difference {worst:.6f} LU")
    return int(failed != 0)


if __name__ == "__main__":
    raise SystemExit(main())
