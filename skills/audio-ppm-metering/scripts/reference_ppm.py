"""Bounded quasi-peak PPM study; NOT a compliant IEC/EBU instrument.

Independent EBU Tech 3205-E published burst/return tests are maintained in
fixtures. This two-timescale rectifier/ballistic model was fitted to burst data;
it currently FAILS the 31.5 Hz--16 kHz flatness requirement. Do not use for
broadcast compliance or inferred true-peak protection.

Per channel: weighted first-order lowpass of full-wave magnitude (two scales),
followed by monotonic peak indication with an exponential release.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math

MAX_CHANNELS = 8
MAX_BLOCK_FRAMES = 256
MIN_HZ, MAX_HZ = 44100, 192000  # Tested sample rates; do not infer arbitrary-rate validity.
PROFILE = "ebu-tech3205-1979-iib-normal-burst-fit-PARTIAL"

# These are FITTED to EBU Tech 3205 Table 2, not normative circuit component values.
# A two-pole positive response covers the published 0.5-100 ms calibration
# table, unlike a single time constant. External-band flatness is NOT met.
FAST_TAU_S = 0.00139366241
SLOW_TAU_S = 0.00923475167
FAST_WEIGHT = 0.389565905
FULL_WAVE_SINE_SCALE = math.pi / 2.0
RELEASE_TAU_S = 2.8 / (24.0 * math.log(10.0) / 20.0)


def _integer(value: int, name: str, minimum: int = 0) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{name} must be integer >= {minimum}")


def _float(value: int | float, name: str, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be finite numeric")
    try:
        f = float(value)
    except (ValueError, OverflowError) as exc:
        raise ValueError(f"{name} is not representable") from exc
    if not math.isfinite(f) or (positive and f <= 0):
        raise ValueError(f"{name} must be finite" + (" and >0" if positive else ""))
    return f


def amplitude_db(magnitude: float, reference: float) -> float:
    """DB of an amplitude; avoid overflow from magnitude/reference division."""
    m = _float(magnitude, "magnitude")
    r = _float(reference, "reference", positive=True)
    if m < 0:
        raise ValueError("magnitude must be nonnegative")
    return -math.inf if m == 0 else 20.0 * (math.log10(m) - math.log10(r))


@dataclass(frozen=True)
class PpmConfiguration:
    sample_rate_hz: Fraction
    channels: int
    test_tone_peak_amplitude: float  # V or PCM units at the EBU TEST alignment point.
    input_unit: str                 # Explicit: e.g., 'V' or 'normalized PCM'.
    profile: str = PROFILE

    def __post_init__(self):
        if (not isinstance(self.sample_rate_hz, Fraction)
                or not MIN_HZ <= self.sample_rate_hz <= MAX_HZ):
            raise ValueError("sample_rate_hz must be exact Fraction in [44100,192000]")
        _integer(self.channels, "channels", 1)
        if self.channels > MAX_CHANNELS:
            raise ValueError("at most eight channels in reference")
        _float(self.test_tone_peak_amplitude, "test_tone_peak_amplitude", positive=True)
        if not isinstance(self.input_unit, str) or not self.input_unit.strip():
            raise ValueError("input_unit must identify physical or digital sample units")
        if self.profile != PROFILE:
            raise ValueError("unsupported PPM profile; no BBC/Type I/slow-mode inference")


def test_tone_peak_voltage() -> float:
    """0 dBu, 1 kHz, 0.775 V RMS; peak for a mathematically ideal sine."""
    return math.sqrt(2.0) * 0.775


class PpmStream:
    """Logical per-channel state; neither realtime-safe nor thread-safe."""
    def __init__(self, config: PpmConfiguration, *, epoch_id: str, start_sample: int):
        if not isinstance(config, PpmConfiguration):
            raise ValueError("config must be PpmConfiguration")
        if not isinstance(epoch_id, str) or not epoch_id.strip():
            raise ValueError("epoch_id must be a nonempty string")
        _integer(start_sample, "start_sample")
        self.config = config
        self.epoch_id = epoch_id
        self._epochs = {epoch_id}
        self.next_sample = start_sample
        self.accepted_blocks = 0
        self._fast = [0.0] * config.channels
        self._slow = [0.0] * config.channels
        self._indicated = [0.0] * config.channels
        rate = float(config.sample_rate_hz)
        self._a_fast = -math.expm1(-1.0 / (rate * FAST_TAU_S))
        self._a_slow = -math.expm1(-1.0 / (rate * SLOW_TAU_S))
        self._release = math.exp(-1.0 / (rate * RELEASE_TAU_S))

    def push(self, start_sample: int, planes: list[list[float]]) -> dict:
        """Atomic block processing; report timeline of indication for verification.

        No inferred loss, true-peak, loudness or screen refresh semantics.
        """
        _integer(start_sample, "start_sample")
        if start_sample != self.next_sample:
            raise ValueError(f"noncontiguous block: expected {self.next_sample}, got {start_sample}; new epoch required")
        if not isinstance(planes, (list, tuple)) or len(planes) != self.config.channels:
            raise ValueError("one planar array per channel required")
        if any(not isinstance(p, (list, tuple)) for p in planes):
            raise ValueError("planes must be arrays")
        frames = len(planes[0])
        if not 1 <= frames <= MAX_BLOCK_FRAMES or any(len(p) != frames for p in planes):
            raise ValueError("nonempty, equal-size planes required, at most 256 frames")
        checked = []
        for p in planes:
            checked.append([_float(x, "audio sample") for x in p])

        fast, slow, indicated = self._fast.copy(), self._slow.copy(), self._indicated.copy()
        histories, per_channel_max = [], []
        ref = float(self.config.test_tone_peak_amplitude)
        for channel in range(self.config.channels):
            history = []
            mx = -math.inf
            for x in checked[channel]:
                # Explicitly guard overflow BEFORE changing persistent state.
                drive = abs(x) * FULL_WAVE_SINE_SCALE
                if not math.isfinite(drive):
                    raise ValueError("nonrepresentable rectified sample")
                nf = fast[channel] + self._a_fast * (drive - fast[channel])
                ns = slow[channel] + self._a_slow * (drive - slow[channel])
                if not (math.isfinite(nf) and math.isfinite(ns)):
                    raise ValueError("nonrepresentable detector state")
                candidate = FAST_WEIGHT * nf + (1.0 - FAST_WEIGHT) * ns
                if drive and candidate == 0 and indicated[channel] == 0:
                    raise ValueError("nonzero input underflows detector precision")
                ni = max(candidate, indicated[channel] * self._release)
                if not math.isfinite(ni):
                    raise ValueError("nonrepresentable meter indication")
                fast[channel], slow[channel], indicated[channel] = nf, ns, ni
                reading = amplitude_db(ni, ref)
                mx = max(mx, reading)
                history.append(reading)
            per_channel_max.append(mx)
            histories.append(history)

        # No partial commit if any channel or sample failed.
        self._fast, self._slow, self._indicated = fast, slow, indicated
        self.next_sample = start_sample + frames
        self.accepted_blocks += 1
        return {
            "profile": self.config.profile,
            "epoch_id": self.epoch_id,
            "start_sample": start_sample,
            "end_sample_exclusive": self.next_sample,
            "frames": frames,
            "sample_rate_hz": self.config.sample_rate_hz,
            "source_units": self.config.input_unit,
            "test_tone_peak_amplitude": ref,
            "indication_db_re_TEST": [amplitude_db(x, ref) for x in indicated],
            "max_db_re_TEST_in_block": per_channel_max,
            "indications_db_by_channel": histories,
            "standards_conformance": False,
            "known_failed_requirement": "31.5Hz-to-16kHz flatness is not met",
        }

    def reset_epoch(self, epoch_id: str, start_sample: int, config: PpmConfiguration | None = None) -> None:
        if not isinstance(epoch_id, str) or not epoch_id.strip() or epoch_id in self._epochs:
            raise ValueError("new epoch identifier required and cannot be reused")
        _integer(start_sample, "start_sample")
        config = self.config if config is None else config
        if not isinstance(config, PpmConfiguration):
            raise ValueError("config must be PpmConfiguration")
        next_epochs = self._epochs | {epoch_id}
        self.__init__(config, epoch_id=epoch_id, start_sample=start_sample)
        self._epochs = next_epochs


def synthetic_sine_burst(*, frequency_hz: float, sample_rate_hz: Fraction,
                         duration_ms: float, peak_amplitude: float,
                         phase_rad: float = 0.0) -> list[float]:
    """Synthetic burst at exact frame timestamps; first/last frame have no fades."""
    freq = _float(frequency_hz, "frequency", positive=True)
    dur = _float(duration_ms, "duration", positive=True)
    peak = _float(peak_amplitude, "peak", positive=True)
    phase = _float(phase_rad, "phase")
    if not isinstance(sample_rate_hz, Fraction) or not MIN_HZ <= sample_rate_hz <= MAX_HZ:
        raise ValueError("invalid exact sample_rate_hz")
    fs = float(sample_rate_hz)
    if freq >= fs / 2:
        raise ValueError("frequency must be below Nyquist")
    n = math.ceil(float(Fraction.from_float(dur) * sample_rate_hz / 1000))
    if n > 20000:
        raise ValueError("reference burst length limited")
    return [peak * math.sin(2.0 * math.pi * freq * (i / fs) + phase) for i in range(n)]
