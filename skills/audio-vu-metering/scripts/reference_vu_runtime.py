"""Pure, bounded block renderer for a VU-inspired meter.

Input states are never mutated. The caller publishes the returned states only
if all channel data and floating-point operations were valid.
"""
from __future__ import annotations
import math
from reference_vu_ballistics import ToneCalibration


def render_block(data: list[list[float]],
                 prior_states: list[tuple[float,float]],
                 calibration: ToneCalibration,
                 a: float,b: float,c: float,d: float) -> tuple[list[tuple[float,float]],list[dict]]:
    states = []
    summaries = []
    for row, (y0, v0) in zip(data, prior_states):
        y, v = y0, v0
        max_deflection = 0.0
        max_abs_sample = 0.0
        for sample in row:
            max_abs_sample = max(max_abs_sample, abs(sample))
            # Normalize after magnitude, not by multiplying with
            # pi/(2*A_ref), which might overflow before multiplication.
            ratio = abs(sample)/calibration.reference_sine_peak
            if sample != 0.0 and ratio == 0.0:
                raise ValueError("nonzero detector input underflows binary64")
            input_level = ratio*(math.pi/2.0)
            if not math.isfinite(input_level):
                raise ValueError("rectifier ratio not representable")
            z = y-input_level
            # Exact held-input evolution (similar to scipy.signal.cont2discrete ZOH)
            ny = input_level + a*z + b*v
            nv = c*z + d*v
            if not math.isfinite(ny) or not math.isfinite(nv):
                raise ValueError("VU mechanical state not representable")
            y, v = ny, nv
            max_deflection = max(max_deflection, y)
        # Analogue stops are represented by display clipping to >=0 only;
        # the idealized internal differential state is unchanged.
        display = max(0.0, y)
        vu = None if display == 0.0 else 20.0*math.log10(display)
        if vu is not None and not math.isfinite(vu):
            raise ValueError("VU display logarithm unrepresentable")
        states.append((y, v))
        summaries.append({
            "deflection": display,
            "vu": vu,
            "above_0_vu": display > 1.0,
            "outside_plus_3_vu_scale": display > 10.0**(3.0/20.0),
            "max_block_deflection": max_deflection,
            "sample_peak_in_input_units": max_abs_sample,
            "sample_peak_above_input_unit_one": max_abs_sample > 1.0 if calibration.input_unit == "unit-normalized float PCM" else None,
            "display_clamped_to_zero": y < 0.0,
        })
    return states,summaries
