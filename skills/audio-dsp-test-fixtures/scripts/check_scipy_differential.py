"""Optional dynamic differential tests against independent SciPy/NumPy backends.

Run from the KestrelGaming repo after installing the optional dependencies:
  python3 skills/audio-dsp-test-fixtures/scripts/check_scipy_differential.py --seed 20261103 --cases 12

This is not part of normal stdlib CI; never call it formal meter certification.
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "skills/audio-fft-spectrum/scripts"))
sys.path.insert(0, str(ROOT / "skills/audio-power-spectral-density/scripts"))
sys.path.insert(0, str(ROOT / "skills/audio-spectrogram-waterfall/scripts"))
sys.path.insert(0, str(ROOT / "skills/audio-rms-crest-factor/scripts"))
sys.path.insert(0, str(ROOT / "skills/audio-dsp-test-fixtures/scripts"))


def run(seed: int, cases: int) -> int:
    if not isinstance(seed, int) or not 0 <= seed < 2**32:
        raise ValueError("seed must be uint32")
    if not isinstance(cases, int) or not 1 <= cases <= 40:
        raise ValueError("cases must be 1..40")
    try:
        import numpy as np
        import scipy
        from scipy import signal
    except ImportError as exc:
        raise RuntimeError("Optional NumPy/SciPy are required for the differential run") from exc

    from reference_dft import one_sided_amplitude, periodic_hann
    from reference_psd import periodogram, welch_mean
    from reference_stft import stft_frames
    from reference_levels import sample_levels
    from fixture_bank import make_fixture

    rng = random.Random(seed)
    kinds = ("coherent_sine", "offbin_sine", "seeded_noise", "impulse", "dc")
    comparisons = 0

    def assert_equal_quantity(actual, expected, label):
        nonlocal comparisons
        got = np.asarray(actual, dtype=np.float64)
        want = np.asarray(expected, dtype=np.float64)
        if got.shape != want.shape or not np.all(np.isfinite(got)) or not np.all(np.isfinite(want)):
            raise AssertionError(f"{label}: nonfinite or shape mismatch {got.shape} != {want.shape}")
        if not np.allclose(got, want, rtol=2e-9, atol=3e-12):
            pos = np.unravel_index(int(np.argmax(abs(got - want))), got.shape)
            raise AssertionError(f"{label}: mismatch at {pos}: got={got[pos]}, expected={want[pos]}")
        comparisons += 1

    sizes = (32, 48, 63, 64, 65, 96)
    for case in range(cases):
        n = sizes[case % len(sizes)]
        kind = kinds[case % len(kinds)]
        bin_index = float(rng.randint(1, max(1, n//2-3)))
        fixture = make_fixture(
            kind, sample_count=n, amplitude=0.25 + 0.5*rng.random(),
            sample_rate_hz=(8000.0, 44100.0, 48000.0)[case % 3],
            bin_index=bin_index, phase_rad=rng.uniform(-math.pi, math.pi),
            impulse_index=rng.randrange(n), seed=rng.getrandbits(32))
        x = fixture["planar_samples"][0]
        fs = fixture["sample_rate_hz"]
        window = [1.0] * n if case % 2 else periodic_hann(n)
        nfft = n if case % 3 == 0 else 2*n
        w = np.asarray(window)
        data = np.asarray(x)

        frequencies, values = periodogram(x, window, fs, nfft=nfft)
        f2, psd2 = signal.periodogram(data, fs=fs, window=w, detrend=False,
                                      nfft=nfft, scaling="density")
        assert_equal_quantity(frequencies, f2, f"{case}/periodogram frequencies")
        assert_equal_quantity(values, psd2, f"{case}/periodogram PSD")

        factors = np.full(n//2 + 1, 2.0)
        factors[0] = 1.0
        if n % 2 == 0:
            factors[-1] = 1.0
        amp_expected = abs(np.fft.rfft(data*w))*factors/float(np.sum(w))
        assert_equal_quantity(one_sided_amplitude(x, window), amp_expected,
                              f"{case}/FFT amplitude")

        hop = n//2
        extended = x + [v*0.75 for v in x] + [-v*0.5 for v in x]
        stft = stft_frames(extended, window, fs, hop, nfft=nfft, scaling="psd")
        _, _, sp = signal.spectrogram(np.asarray(extended), fs=fs, window=w,
                                      nperseg=n, noverlap=n-hop, nfft=nfft,
                                      detrend=False, scaling="density", mode="psd")
        assert_equal_quantity([frame["values"] for frame in stft["frames"]],
                              sp.T, f"{case}/STFT PSD")
        if any(frame["start_sample"] != idx*hop or
               frame["center_sample"] != idx*hop + (n-1)/2
               for idx, frame in enumerate(stft["frames"])):
            raise AssertionError(f"{case}/STFT time coordinates")

        fw, psd_w, count = welch_mean(extended, window, fs, hop, nfft=nfft)
        fw2, psd_w2 = signal.welch(np.asarray(extended), fs=fs, window=w,
                                   nperseg=n, noverlap=n-hop, nfft=nfft,
                                   detrend=False, scaling="density", average="mean")
        if count != len(stft["frames"]):
            raise AssertionError(f"{case}/Welch count")
        assert_equal_quantity(fw, fw2, f"{case}/Welch frequencies")
        assert_equal_quantity(psd_w, psd_w2, f"{case}/Welch PSD")
        expected_rms = float(np.sqrt(np.mean(data*data)))
        assert_equal_quantity([sample_levels(x)["rms"]], [expected_rms], f"{case}/RMS")

    print(f"PASS optional SciPy differential: seed={seed}, cases={cases}, "
          f"comparisons={comparisons}, numpy={np.__version__}, scipy={scipy.__version__}; "
          "not an instrument-conformance test")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261103)
    parser.add_argument("--cases", type=int, default=12)
    options = parser.parse_args()
    try:
        return run(options.seed, options.cases)
    except (AssertionError, ValueError, RuntimeError) as exc:
        print(f"FAIL optional SciPy differential: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
