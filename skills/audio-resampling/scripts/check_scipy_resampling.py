"""Optional dynamic differential check of bounded FIR SRC vs independent SciPy.

Run: python3 skills/audio-resampling/scripts/check_scipy_resampling.py --seed 20261104 --cases 24
SciPy/NumPy must be installed separately; standard Kestrel CI stays stdlib.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reference_resampling import resample_offline


def run(seed: int, cases: int) -> int:
    if not isinstance(seed, int) or not 0 <= seed < 2**32:
        raise ValueError("seed must be uint32")
    if not isinstance(cases, int) or not 1 <= cases <= 40:
        raise ValueError("cases must be 1..40")
    try:
        import scipy
        import numpy as np
        from scipy import signal
    except ImportError as exc:
        raise RuntimeError("optional NumPy and SciPy installation required") from exc
    r = random.Random(seed)
    ratios = ((2, 3), (3, 2), (147, 160), (160, 147), (1, 2), (4, 1), (1, 1))
    sizes = (13, 32, 63, 64, 97, 128, 255)
    comparisons = 0
    for case in range(cases):
        up, down = ratios[case % len(ratios)]
        n = sizes[(case * 3) % len(sizes)]
        gain = r.uniform(0.1, 0.9)
        offset = r.uniform(-0.05, 0.05)
        samples = [gain * (r.random() * 2 - 1) + offset for _ in range(n)]
        planes = [samples, [-x for x in samples]] if case % 2 else [samples]
        expected = signal.resample_poly(np.asarray(planes, dtype=np.float64), up, down,
                                        axis=1, window=('kaiser', 5.0),
                                        padtype='constant')
        actual = resample_offline(planes, Fraction(down), Fraction(up))["planar_samples"]
        got = np.asarray(actual, dtype=np.float64)
        if got.shape != expected.shape or not np.all(np.isfinite(got)):
            raise AssertionError(f"case={case}, rates={up}/{down}: shape/finite mismatch")
        if not np.allclose(got, expected, atol=3e-12, rtol=2e-10):
            at = np.unravel_index(int(np.argmax(np.abs(got-expected))), got.shape)
            raise AssertionError(f"case={case}, rates={up}/{down}, index={at}: "
                                 f"got={got[at]}, SciPy={expected[at]}")
        comparisons += got.size
    print(f"PASS SRC live differential; seed={seed}, cases={cases}, "
          f"sample_comparisons={comparisons}, NumPy={np.__version__}, "
          f"SciPy={scipy.__version__}; no device/standard conformance claims")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261104)
    parser.add_argument("--cases", type=int, default=24)
    opts = parser.parse_args()
    try:
        return run(opts.seed, opts.cases)
    except (ValueError, RuntimeError, AssertionError) as exc:
        print(f"FAIL SRC differential: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
