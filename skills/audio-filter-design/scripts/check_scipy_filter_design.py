"""Optional independent SciPy FIR/IIR differential (not standard CI).

Run from repository root:
  python3 skills/audio-filter-design/scripts/check_scipy_filter_design.py --seed 20261104 --cases 24

External numerical comparison *shares* window-method and cookbook design
choices, so it checks implementation differences, not ideal filter suitability.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reference_filter_design import (design_fir, design_biquad, frequency_response,
                                     group_delay_samples, FilterStream)


def run(seed: int, cases: int) -> int:
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed < 2**32:
        raise ValueError("seed must be uint32")
    if isinstance(cases, bool) or not isinstance(cases, int) or not 1 <= cases <= 48:
        raise ValueError("cases must be 1..48")
    try:
        import scipy
        import numpy as np
        from scipy import signal
    except ImportError as exc:
        raise RuntimeError("optional NumPy/SciPy installation required") from exc
    rng = random.Random(seed)
    coefficients = response = time_samples = group_delays = 0
    for case in range(cases):
        fs = 48000 if case % 2 == 0 else 44100
        freq = [2100, 3100, 5200, 6800][case % 4]
        kind = ("lowpass", "highpass", "bandpass", "bandstop")[case % 4]
        window = ("hamming", "hann", "blackman")[case % 3]
        taps = (31, 65, 129)[case % 3]
        edges = (Fraction(freq),) if kind in ("lowpass", "highpass") else (Fraction(1800),Fraction(6400))
        p = design_fir(kind, Fraction(fs), edges, taps, window)
        scipy_taps = signal.firwin(taps, [float(x) for x in edges] if len(edges)==2 else float(edges[0]),
                                   window=window, pass_zero=kind, fs=fs, scale=True)
        if not np.allclose(np.asarray(p.taps), scipy_taps, atol=3e-13, rtol=2e-11):
            raise AssertionError(f"FIR coefficient mismatch case={case} kind={kind}")
        coefficients += taps
        w = np.array([0., fs*0.04, fs*0.1, fs*0.23, fs*0.40, fs*0.495], dtype=float)
        _, expected = signal.freqz(scipy_taps, worN=w, fs=fs)
        actual = np.asarray([frequency_response(p, Fraction(float(v))) for v in w])
        if not np.allclose(expected, actual, atol=5e-12, rtol=5e-10):
            raise AssertionError(f"FIR response mismatch case={case} kind={kind}")
        response += len(w)
        n = (13, 64, 97, 131)[case % 4]
        source = np.asarray([rng.uniform(-0.8, 0.8) for _ in range(n)], dtype=float)
        ours = FilterStream(p,"e",100,1).push(100,[list(source)])["planar_samples"][0]
        reference = signal.lfilter(scipy_taps, [1.0], source)
        if not np.allclose(ours, reference, atol=5e-12, rtol=5e-10):
            raise AssertionError(f"FIR signal mismatch case={case}")
        time_samples += n
        if kind == "lowpass":
            gd = group_delay_samples(p, Fraction(500))
            _, refgd = signal.group_delay((scipy_taps,[1.]),w=[2*math.pi*500/fs])
            if abs(gd-refgd[0]) > 5e-7:
                raise AssertionError(f"FIR group delay mismatch case={case}")
            group_delays += 1

        # Independent SciPy Butterworth 2-pole for the 1/sqrt(2)-Q cookbook
        kind_iir = "lowpass" if case % 2 == 0 else "highpass"
        q = 1/math.sqrt(2)
        bplan = design_biquad(kind_iir, Fraction(fs), Fraction(freq), q=q)
        ss = bplan.sections[0]
        expected_sos = signal.butter(2, freq, btype="lowpass" if kind_iir=="lowpass" else "highpass",
                                     fs=fs, output="sos")
        ours_sos = np.array([[ss.b0, ss.b1, ss.b2,1.,ss.a1,ss.a2]],dtype=float)
        if not np.allclose(ours_sos, expected_sos, atol=5e-13, rtol=2e-10):
            raise AssertionError(f"Butterworth coefficient mismatch case={case}")
        coefficients += 5
        _, expected_h = signal.freqz_sos(expected_sos, worN=w, fs=fs)
        actual_h = np.asarray([frequency_response(bplan,Fraction(float(v))) for v in w])
        if not np.allclose(expected_h, actual_h, atol=1e-11, rtol=2e-9):
            raise AssertionError(f"SOS frequency response mismatch case={case}")
        response += len(w)
        actual_samples = FilterStream(bplan,"e",100,1).push(100,[list(source)])["planar_samples"][0]
        expected_samples = signal.sosfilt(expected_sos,source)
        if not np.allclose(actual_samples,expected_samples,atol=2e-11,rtol=3e-9):
            raise AssertionError(f"SOS output mismatch case={case}")
        time_samples += n
        if kind_iir == "lowpass":
            gd = group_delay_samples(bplan,Fraction(500))
            _, refgd = signal.group_delay((expected_sos[0,:3],expected_sos[0,3:]),
                                           w=[2*math.pi*500/fs])
            if abs(gd-refgd[0])> 1e-6:
                raise AssertionError(f"SOS group delay mismatch case={case}")
            group_delays += 1
    print(f"PASS audio filter differential: seed={seed}, cases={cases}; "
          f"coefficients={coefficients}, complex_response_points={response}, "
          f"signal_samples={time_samples}, group_delay_points={group_delays}; "
          f"NumPy={np.__version__}, SciPy={scipy.__version__}; "
          "no realtime/device/normative conformance claim")
    return 0


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed",type=int,default=20261104)
    parser.add_argument("--cases",type=int,default=24)
    args=parser.parse_args()
    try:
        return run(args.seed,args.cases)
    except (ValueError,RuntimeError,AssertionError) as exc:
        print(f"FAIL audio filter differential: {exc}",file=sys.stderr)
        return 1


if __name__=="__main__":
    raise SystemExit(main())
