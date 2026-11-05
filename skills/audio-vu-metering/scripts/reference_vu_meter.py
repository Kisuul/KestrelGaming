"""Bounded VU-style detector and moving-coil state machine.

The detector and ballistic math live in reference_vu_ballistics.py so that
the scientific assumptions are separately reviewable and testable.
Not a hardware or IEC-conforming production audio meter.
"""
from __future__ import annotations

from fractions import Fraction
import math
from reference_vu_runtime import render_block
from reference_vu_ballistics import (
    MAX_CHANNELS, MAX_BLOCK_FRAMES, VU_RISE_SECONDS,
    VU_OVERSHOOT_FRACTION, ToneCalibration, _finite, _index,
    damping_ratio_for_overshoot, _omega_n_for_rise, expected_unit_step,
)


class VUMeter:
    """Per-channel, sample-driven, causal VU-inspired needle with strict epochs.

    The normalized detector drives a 2nd-order spring model. One held input
    sample per interval is mathematically integrated via an *exact* ZOH state
    transition (not forward Euler). The 1 kHz tone is only approximately
    calibrated at finite sampling rates, and IEC compliance is unverified.
    """
    def __init__(self, rate_hz: Fraction, channel_labels: tuple[str, ...],
                 calibration: ToneCalibration, *, epoch_id: str = "epoch-0",
                 origin_sample: int = 0):
        if not isinstance(rate_hz, Fraction) or not 8000 <= rate_hz <= 384000:
            raise ValueError("sample rate must be Fraction in 8..384 kHz")
        if not isinstance(channel_labels, tuple) or not 1 <= len(channel_labels) <= MAX_CHANNELS:
            raise ValueError("1..8 explicit channel labels required")
        if any(not isinstance(label, str) or not label.strip() for label in channel_labels):
            raise ValueError("channel labels must be nonempty strings")
        if len(set(channel_labels)) != len(channel_labels):
            raise ValueError("channel labels must be unique")
        if not isinstance(calibration, ToneCalibration):
            raise ValueError("explicit ToneCalibration required")
        if not isinstance(epoch_id, str) or not epoch_id.strip():
            raise ValueError("nonempty epoch_id required")
        _index(origin_sample, "origin_sample")
        self.rate_hz = rate_hz
        self.channel_labels = channel_labels
        self.calibration = calibration
        self.epoch_id = epoch_id
        self._used_epochs = {epoch_id}
        self.next_sample = origin_sample
        self.accepted_blocks = 0
        zeta = damping_ratio_for_overshoot()
        w = _omega_n_for_rise(zeta, VU_RISE_SECONDS)
        dt = float(Fraction(1, 1) / rate_hz)
        alpha = zeta*w
        beta = w*math.sqrt(1-zeta*zeta)
        e = math.exp(-alpha*dt)
        c, sn = math.cos(beta*dt), math.sin(beta*dt)
        self._a = e*(c+(alpha/beta)*sn)
        self._b = e*sn/beta
        self._c = -e*(w*w/beta)*sn
        self._d = e*(c-(alpha/beta)*sn)
        self._states = [(0.0, 0.0) for _ in channel_labels]

    def _validate(self, planes: list[list[float]]) -> tuple[list[list[float]], int]:
        if not isinstance(planes, (tuple, list)) or len(planes) != len(self.channel_labels):
            raise ValueError("one input plane per declared channel required")
        if any(not isinstance(p, (tuple, list)) for p in planes):
            raise ValueError("planes must be nonempty lists or tuples")
        frames = len(planes[0])
        if not 1 <= frames <= MAX_BLOCK_FRAMES or any(len(p) != frames for p in planes):
            raise ValueError("require 1..32768 equal-length frames per channel")
        return [[_finite(x, "sample") for x in p] for p in planes], frames

    def push(self, start_sample: int, planes: list[list[float]]) -> dict:
        _index(start_sample, "start_sample")
        if start_sample != self.next_sample:
            raise ValueError("sample gap or overlap: start a distinct epoch")
        data, frames = self._validate(planes)
        # Always calculate into local state before publishing results or state.
        # Compute results transactionally; reject errors before state commit.
        states, summaries = render_block(data, self._states, self.calibration,
                                         self._a, self._b, self._c, self._d)
        self._states = states
        self.next_sample += frames
        self.accepted_blocks += 1
        return {
            "epoch_id": self.epoch_id,
            "start_sample": start_sample,
            "end_sample_exclusive": self.next_sample,
            "rate_hz": self.rate_hz,
            "channel_labels": self.channel_labels,
            "calibration_label": self.calibration.reference_label,
            "input_unit": self.calibration.input_unit,
            "frames": frames,
            "channels": summaries,
            "detector": "mean full-wave rectified + idealized second-order needle",
            "standards_conformance": False,
            "clipped_audio": False,
        }

    def reset_epoch(self, epoch_id: str, origin_sample: int,
                    calibration: ToneCalibration | None = None) -> None:
        if not isinstance(epoch_id, str) or not epoch_id.strip() or epoch_id in self._used_epochs:
            raise ValueError("new unique nonempty epoch ID required")
        _index(origin_sample, "origin_sample")
        next_cal = self.calibration if calibration is None else calibration
        if not isinstance(next_cal, ToneCalibration):
            raise ValueError("calibration must be ToneCalibration")
        self.epoch_id = epoch_id
        self._used_epochs.add(epoch_id)
        self.next_sample = origin_sample
        self.calibration = next_cal
        self._states = [(0.0, 0.0) for _ in self.channel_labels]
        self.accepted_blocks = 0


def calibration_ratio_db(deflection: float) -> float | None:
    """0 deflection -> unknown/negative infinite indication (None in UI)."""
    value = _finite(deflection, "deflection")
    if value < 0:
        raise ValueError("deflection cannot be negative")
    return None if value == 0 else 20.0*math.log10(value)
