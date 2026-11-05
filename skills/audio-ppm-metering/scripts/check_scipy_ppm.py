"""Optional independent SciPy differential of a bounded PPM arithmetic model.

Tests calculation agreement, NOT standards conformance. Requires NumPy/SciPy.
Run from the Kestrel repository root or directly. No dependencies in normal CI.
"""
from __future__ import annotations
import argparse
from fractions import Fraction
import math
from pathlib import Path
import random
import sys

from reference_ppm import (PpmStream, PpmConfiguration, FAST_TAU_S, SLOW_TAU_S,
    FAST_WEIGHT, RELEASE_TAU_S)


def check(seed: int = 20261105, cases: int = 24) -> dict:
    try:
        import numpy as np
        from scipy.signal import lfilter
        import scipy
    except ImportError as exc:
        raise RuntimeError("Optional differential needs NumPy and SciPy") from exc
    rng = random.Random(seed)
    comparisons = 0
    largest_error = 0.0
    for case in range(cases):
        fs = rng.choice((44100,48000,96000,192000))
        count = rng.randrange(45,501)
        channels = rng.randint(1,3)
        ref = 10**rng.uniform(-1.,1.)
        x = [np.array([rng.uniform(-ref*1.4,ref*1.4) for _ in range(count)],dtype=float)
             for _ in range(channels)]
        obj = PpmStream(PpmConfiguration(Fraction(fs),channels,ref,"PCM"),
                        epoch_id=f"case-{case}",start_sample=2**54+case*997)
        actual=[[] for _ in range(channels)]
        at=obj.next_sample
        j=0
        while j<count:
            k=min(rng.choice((1,3,5,17,64,251)),count-j)
            block=obj.push(at,[channel[j:j+k].tolist() for channel in x])
            for ch in range(channels):
                actual[ch].extend(block["indications_db_by_channel"][ch])
            j+=k;at+=k
        # Independent LTI difference-equation execution via SciPy lfilter,
        # not via the reference implementation's per-sample recurrence.
        af=-np.expm1(-1/(fs*FAST_TAU_S))
        as_=-np.expm1(-1/(fs*SLOW_TAU_S))
        release=np.exp(-1/(fs*RELEASE_TAU_S))
        # Closed-form vectorization for slow falling ceiling:
        # v[n] = r**n * max_{i<=n}(c[i] * r**(-i)).
        n=np.arange(count,dtype=float)
        fall=release**n
        for ch in range(channels):
            drive=np.abs(x[ch])*(np.pi/2)
            fast=lfilter([af],[1,-(1-af)],drive)
            slow=lfilter([as_],[1,-(1-as_)],drive)
            candidate=FAST_WEIGHT*fast+(1-FAST_WEIGHT)*slow
            expected=fall*np.maximum.accumulate(candidate/fall)
            db=np.where(expected>0,20*np.log10(expected/ref),-np.inf)
            a=np.asarray(actual[ch]);delta=np.max(np.abs(a-db))
            if not math.isfinite(float(delta)) or delta>2e-10:
                raise AssertionError(f"independent differential failed: {case=} {ch=} {delta=}")
            largest_error=max(largest_error,float(delta))
            comparisons+=count
    return {"seed":seed,"cases":cases,"samples_compared":comparisons,
            "max_db_error":largest_error,"numpy_version":np.__version__,
            "scipy_version":scipy.__version__,"status":"PASS",
            "conformance_claim":False}


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--seed",type=int,default=20261105)
    parser.add_argument("--cases",type=int,default=24)
    args=parser.parse_args()
    print(check(args.seed,args.cases))
