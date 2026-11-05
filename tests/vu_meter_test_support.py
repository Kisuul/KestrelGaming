"""Shared independent test fixtures for the VU model; not implementation oracles."""
from fractions import Fraction
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1] / 'skills/audio-vu-metering/scripts'))
from reference_vu_meter import ToneCalibration,VUMeter

RATE=Fraction(48000)
REF=ToneCalibration.digital_tone_dbfs_peak(-20)


def meter(labels=('FL',),start=0,ref=REF,rate=RATE):
    return VUMeter(rate, labels, ref, origin_sample=start)


def run(m,planes,chunk=8192):
    offset=0
    last=None
    while offset < len(planes[0]):
        n=min(chunk,len(planes[0])-offset)
        last=m.push(m.next_sample,[p[offset:offset+n] for p in planes])
        offset+=n
    return last


def constant_step_input(ref=REF):
    # Independent from the meter's own detector normalization code.
    return (2.0/3.141592653589793)*ref.reference_sine_peak
