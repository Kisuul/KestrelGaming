#!/usr/bin/env python3
"""Optional SciPy independent state-space check for bounded VU model.

Not run in repository CI: requires numpy/scipy. Separately constructs a
continuous state-space ODE, discretizes via scipy.signal.cont2discrete(ZOH),
and independently solves tuning with scipy.optimize.brentq. Agreement
checks one chosen idealized detector/needle, NOT IEC compliance.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import math
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reference_vu_meter import ToneCalibration, VUMeter


def run(seed: int = 20261105, cases: int = 24) -> dict:
    import numpy as np
    import scipy
    from scipy import optimize, signal

    if cases < 1 or cases > 128:
        raise ValueError("cases must be in 1..128")
    rng = random.Random(seed)
    matched = 0
    total_samples = 0
    # Derive from analytic overshoot and step condition, without invoking
    # reference_meter's tuning/coefficients or continuous-step helper.
    overshoot = .0125
    z = -math.log(overshoot) / math.sqrt(math.pi**2 + math.log(overshoot)**2)
    d = math.sqrt(1-z*z)

    def step_unit(x):
        return 1-math.exp(-z*x)*(math.cos(d*x)+(z/d)*math.sin(d*x))

    wn = optimize.brentq(lambda x: step_unit(x)-.99,
                         0.01, math.pi/d, xtol=1e-13)/.3
    rates=[Fraction(44100),Fraction(48000),Fraction(96000),
           Fraction(48000*1000,1001),Fraction(32000)]
    for case in range(cases):
        rate=rates[case % len(rates)]
        ref=ToneCalibration.digital_tone_dbfs_peak(-20 if case % 2 else -18)
        meter=VUMeter(rate, ('CH0',), ref, epoch_id=f'case-{case}')
        dt=float(1/rate)
        A=np.array([[0.,1.],[-wn*wn,-2*z*wn]],dtype=float)
        B=np.array([[0.],[wn*wn]])
        C=np.array([[1.,0.]])
        D=np.array([[0.]])
        ad,bd,_,_,_=signal.cont2discrete((A,B,C,D),dt,method='zoh')
        state=np.array([0.,0.]); n=rng.randint(48,1200)
        frequency=rng.choice([31.,440.,1000.,4000.,10000.])
        if frequency*2 >= float(rate): frequency=1000.
        kind=case % 4
        if kind==0:
            raw=[ref.reference_sine_peak*math.sin(2*math.pi*frequency*i/float(rate)) for i in range(n)]
        elif kind==1:
            raw=[ref.reference_sine_peak if i < n//3 else 0. for i in range(n)]
        elif kind==2:
            raw=[rng.uniform(-ref.reference_sine_peak,ref.reference_sine_peak) for _ in range(n)]
        else:
            raw=[ref.reference_sine_peak if i==0 else 0. for i in range(n)]
        # Validate at irregular callback boundaries, not just at end.
        pos=0
        while pos < n:
            take=min(rng.randint(1,73),n-pos)
            block=raw[pos:pos+take]
            result=meter.push(pos,[block])
            for sample in block:
                input_level=(math.pi/(2*ref.reference_sine_peak))*abs(sample)
                state=ad@state+bd[:,0]*input_level
            observed=result['channels'][0]['deflection']
            reference=max(0.,float(state[0]))
            tol=2e-8*max(1,reference)
            if not math.isclose(observed,reference,rel_tol=0,abs_tol=tol):
                raise AssertionError(f'case {case} frame {pos+take}: {observed} != {reference} (tol {tol})')
            matched+=1
            pos+=take
        total_samples+=n
    return {"seed":seed,"cases":cases,"sample_updates":total_samples,
            "callback_state_comparisons":matched,"numpy":np.__version__,
            "scipy":scipy.__version__}


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--seed',type=int,default=20261105)
    ap.add_argument('--cases',type=int,default=24)
    args=ap.parse_args()
    print(run(args.seed,args.cases))
