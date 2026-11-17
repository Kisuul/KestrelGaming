"""Verify Tech 3342 Table 1 using the original EBU Loudness Test Set v5.0 ZIP."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import wave
import zipfile

from reference_loudness_range import LoudnessConfig, LoudnessRangeStream, SAMPLE_RATE_HZ
from check_ebu_loudness import _official_archive, open_fixture_planes


# Tech 3342 v4 Table 1, mapped to the names in the original v5.0 archive.
_CASES = (
    ("seq-3342-1-16bit.wav", 10),
    ("seq-3342-2-16bit.wav", 5),
    ("seq-3342-3-16bit.wav", 20),
    ("seq-3342-4-16bit.wav", 15),
    ("seq-3341-7_seq-3342-5-24bit.wav", 5),
    ("seq-3341-2011-8_seq-3342-6-24bit-v02.wav", 15),
)
_TOLERANCE_LU = 1
_STEREO = ("L", "R")


def _measure(archive, name, copies):
    config = LoudnessConfig(SAMPLE_RATE_HZ, _STEREO, "EBU v5.0 test PCM")
    meter = LoudnessRangeStream(config, epoch_id=name, start_sample=0)
    for _ in range(copies):
        with open_fixture_planes(archive, name, len(_STEREO)) as chunks:
            for planes in chunks:
                meter.push(meter.next_sample, planes, epoch_id=name)
    return meter.finish().result.lra_lu


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="EBU Loudness Test Set v5.0 ZIP")
    args = parser.parse_args(argv)
    total = passed = 0
    worst = 0.0
    print("Test sequences © EBU. Offline LRA checks (one and two copies).", flush=True)
    try:
        names = (name for name, _ in _CASES)
        with _official_archive(args.archive, required_entries=names) as archive:
            for case, (name, expected) in enumerate(_CASES, start=1):
                for copies in (1, 2):
                    actual = _measure(archive, name, copies)
                    error = float("inf") if actual is None else abs(actual - expected)
                    ok = error <= _TOLERANCE_LU
                    total += 1
                    passed += ok
                    worst = max(worst, error)
                    result = "undefined" if actual is None else f"{actual:.6f} LU"
                    print(f"{case}  {name}  ×{copies}  {'PASS' if ok else 'FAIL'}  "
                          f"{result}  target {expected} ±{_TOLERANCE_LU} LU", flush=True)
    except (ArithmeticError, EOFError, OSError, ValueError, wave.Error, zipfile.BadZipFile) as exc:
        print(f"Fixture verification error: {exc}", file=sys.stderr)
        return 2
    print(f"{passed}/{total} measurements passed, largest absolute error {worst:.6f} LU")
    return int(passed != total)


if __name__ == "__main__":
    raise SystemExit(main())
