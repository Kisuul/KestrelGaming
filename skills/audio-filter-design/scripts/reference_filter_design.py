"""Bounded audio FIR/biquad design and streaming reference, stdlib only.

Not a production DSP engine, realtime callback, whole-band guarantee, IEC/ITU
instrument, adaptive time-varying processor or replacement for design review.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import cmath
import math

MAX_TAPS = 129
MAX_CHANNELS = 8
MAX_FRAMES = 256
MAX_SOS = 4


def _integer(x: int, name: str, minimum: int = 0) -> None:
    if not isinstance(x, int) or isinstance(x, bool) or x < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")


def _rate(hz: Fraction) -> Fraction:
    if not isinstance(hz, Fraction) or not Fraction(2000) <= hz <= Fraction(384000):
        raise ValueError("sample rate must be an exact Fraction in [2000,384000] Hz")
    return hz


def _cutoffs(hz: Fraction, edges: tuple[Fraction, ...], n: int) -> tuple[Fraction, ...]:
    if not isinstance(edges, tuple) or len(edges) != n:
        raise ValueError(f"expected {n} exact cutoff frequencies")
    if any(not isinstance(v, Fraction) or not 0 < v < hz / 2 for v in edges):
        raise ValueError("cutoffs must be exact positive Fraction Hz below Nyquist")
    if any(edges[i] >= edges[i+1] for i in range(len(edges)-1)):
        raise ValueError("cutoffs must strictly ascend")
    return edges


def _sinc(x: float) -> float:
    return 1.0 if x == 0.0 else math.sin(math.pi * x) / (math.pi * x)


def _window(n: int, length: int, kind: str) -> float:
    phase = (2.0 * math.pi * n) / (length - 1)
    if kind == "hann":
        return 0.5 - 0.5 * math.cos(phase)
    if kind == "hamming":
        return 0.54 - 0.46 * math.cos(phase)
    if kind == "blackman":
        return 0.42 - 0.5 * math.cos(phase) + 0.08 * math.cos(2.0 * phase)
    raise ValueError("supported windows: hann, hamming, blackman")


@dataclass(frozen=True)
class FIRDesign:
    sample_rate_hz: Fraction
    kind: str
    cutoff_hz: tuple[Fraction, ...]
    window: str
    taps: tuple[float, ...]

    def __post_init__(self) -> None:
        _rate(self.sample_rate_hz)
        if self.kind not in ("lowpass", "highpass", "bandpass", "bandstop"):
            raise ValueError("unknown FIR kind")
        _cutoffs(self.sample_rate_hz, self.cutoff_hz, 2 if self.kind.startswith("band") else 1)
        if self.window not in ("hann", "hamming", "blackman"):
            raise ValueError("unknown FIR window")
        if not isinstance(self.taps, tuple) or not 5 <= len(self.taps) <= MAX_TAPS or len(self.taps) % 2 != 1:
            raise ValueError("FIR reference requires odd 5..129 taps")
        if any(not isinstance(v, float) or not math.isfinite(v) for v in self.taps):
            raise ValueError("FIR taps must be finite floats")
        if any(abs(self.taps[i] - self.taps[-1-i]) > 5e-13 for i in range(len(self.taps)//2)):
            raise ValueError("FIR linear-phase symmetry check failed")

    @property
    def delay_samples(self) -> Fraction:
        return Fraction(len(self.taps) - 1, 2)

    @property
    def delay_seconds(self) -> Fraction:
        return self.delay_samples / self.sample_rate_hz


def design_fir(kind: str, sample_rate_hz: Fraction, cutoff_hz: tuple[Fraction, ...],
               taps: int, window: str = "hamming") -> FIRDesign:
    """Type-I linear-phase windowed-sinc FIR, normalized at a passband reference.

    Window-method cutoff is the *ideal* -6.0206 dB (half amplitude) edge,
    not a claimed -3 dB crossover or guaranteed transition width.
    """
    fs = _rate(sample_rate_hz)
    if kind not in ("lowpass", "highpass", "bandpass", "bandstop"):
        raise ValueError("unknown FIR kind")
    edges = _cutoffs(fs, cutoff_hz, 2 if kind.startswith("band") else 1)
    _integer(taps, "taps", 5)
    if taps > MAX_TAPS or taps % 2 == 0:
        raise ValueError("Type-I FIR reference requires odd 5..129 taps")
    if window not in ("hann", "hamming", "blackman"):
        raise ValueError("unsupported window")
    fs_f = float(fs)
    edge_float = tuple(float(x) for x in edges)
    mid = (taps - 1) // 2
    w = tuple(_window(i, taps, window) for i in range(taps))

    def lo(f: float, k: int) -> float:
        normalized = f / fs_f
        return 2.0 * normalized * _sinc(2.0 * normalized * k)

    coefficients: list[float] = []
    for i in range(mid + 1):
        k = i - mid
        delta = 1.0 if k == 0 else 0.0
        if kind == "lowpass":
            ideal = lo(edge_float[0], k)
        elif kind == "highpass":
            ideal = delta - lo(edge_float[0], k)
        elif kind == "bandpass":
            ideal = lo(edge_float[1], k) - lo(edge_float[0], k)
        else:
            ideal = delta - lo(edge_float[1], k) + lo(edge_float[0], k)
        coefficients.append(ideal * w[i])
    coefficients = coefficients + coefficients[-2::-1]  # exact Type-I symmetry
    if kind in ("lowpass", "bandstop"):
        gain = math.fsum(coefficients)  # DC gain
    elif kind == "highpass":
        gain = math.fsum(v * (1.0 if (j - mid) % 2 == 0 else -1.0)
                         for j, v in enumerate(coefficients))  # Nyquist gain with centered phase
    else:
        midpoint_hz = float((edges[0] + edges[1]) / 2)
        omega = 2.0 * math.pi * midpoint_hz / fs_f
        # symmetry means the phase factor e^(-j*w*mid) is isolated
        gain = math.fsum(v * math.cos(omega * (j - mid))
                         for j, v in enumerate(coefficients))
    if not math.isfinite(gain) or abs(gain) < 1e-10:
        raise ValueError("passband normalization is ill-conditioned for chosen taps/edges")
    result = tuple(v / gain for v in coefficients)
    if any(not math.isfinite(x) or abs(x) > 32 for x in result):
        raise ValueError("FIR coefficients exceed reference numeric bounds")
    return FIRDesign(fs, kind, edges, window, result)


@dataclass(frozen=True)
class Biquad:
    """Normalized denominator 1 + a1*z^-1 + a2*z^-2."""
    b0: float
    b1: float
    b2: float
    a1: float
    a2: float

    def __post_init__(self) -> None:
        if any(not isinstance(x, (int, float)) or isinstance(x, bool) or not math.isfinite(x)
               for x in (self.b0, self.b1, self.b2, self.a1, self.a2)):
            raise ValueError("biquad coefficients must be finite real numbers")
        if self.max_pole_radius >= 1.0 - 1e-10:
            raise ValueError("biquad poles must lie strictly inside unit circle with margin")

    @property
    def poles(self) -> tuple[complex, complex]:
        discriminant = cmath.sqrt(self.a1 * self.a1 - 4.0 * self.a2)
        return ((-self.a1 + discriminant) / 2.0,
                (-self.a1 - discriminant) / 2.0)

    @property
    def max_pole_radius(self) -> float:
        return max(abs(p) for p in self.poles)


@dataclass(frozen=True)
class SOSDesign:
    sample_rate_hz: Fraction
    sections: tuple[Biquad, ...]
    purpose: str

    def __post_init__(self) -> None:
        _rate(self.sample_rate_hz)
        if not isinstance(self.sections, tuple) or not 1 <= len(self.sections) <= MAX_SOS:
            raise ValueError("SOS design requires 1..4 sections")
        if any(not isinstance(s, Biquad) for s in self.sections):
            raise ValueError("all sections must be validated biquads")
        if not isinstance(self.purpose, str) or not self.purpose.strip():
            raise ValueError("document the SOS processing purpose")


def design_biquad(kind: str, sample_rate_hz: Fraction, cutoff_hz: Fraction,
                  q: float = 1.0 / math.sqrt(2.0), gain_db: float = 0.0) -> SOSDesign:
    """RBJ/W3C Audio EQ Cookbook Q-formulas (LP, HP, notch, peaking).

    Q is dimensionless; not a bandwidth-in-octaves parameter. Peaking gain
    is ±24 dB max, others require exactly 0 dB. No shelf filters in oracle.
    """
    fs = _rate(sample_rate_hz)
    (f,) = _cutoffs(fs, (cutoff_hz,), 1)
    if kind not in ("lowpass", "highpass", "notch", "peaking"):
        raise ValueError("unsupported biquad type")
    if isinstance(q, bool) or not isinstance(q, (int, float)) or not math.isfinite(q) or not 0.2 <= q <= 20:
        raise ValueError("Q must be finite in [0.2, 20]")
    if isinstance(gain_db, bool) or not isinstance(gain_db, (int, float)) or not math.isfinite(gain_db) or abs(gain_db) > 24:
        raise ValueError("gain must be finite within ±24 dB")
    if kind != "peaking" and gain_db != 0:
        raise ValueError("gain_db only applies to peaking EQ")
    w0 = 2.0 * math.pi * float(f / fs)
    cw = math.cos(w0)
    alpha = math.sin(w0) / (2.0 * q)
    if kind == "lowpass":
        b0, b1, b2 = (1 - cw) / 2, 1 - cw, (1 - cw) / 2
        a0, a1, a2 = 1 + alpha, -2 * cw, 1 - alpha
    elif kind == "highpass":
        b0, b1, b2 = (1 + cw) / 2, -(1 + cw), (1 + cw) / 2
        a0, a1, a2 = 1 + alpha, -2 * cw, 1 - alpha
    elif kind == "notch":
        b0, b1, b2 = 1, -2 * cw, 1
        a0, a1, a2 = 1 + alpha, -2 * cw, 1 - alpha
    else:
        A = 10.0 ** (gain_db / 40.0)
        b0, b1, b2 = 1 + alpha * A, -2 * cw, 1 - alpha * A
        a0, a1, a2 = 1 + alpha / A, -2 * cw, 1 - alpha / A
    coeffs = Biquad(b0 / a0, b1 / a0, b2 / a0, a1 / a0, a2 / a0)
    return SOSDesign(fs, (coeffs,),
                     f"RBJ {kind}; cutoff={f} Hz, Q={q}, gain={gain_db} dB")


def quantize_biquad(section: Biquad, fractional_bits: int) -> tuple[Biquad, float]:
    """Nearest-even uniform coefficient grid; unstable result explicitly fails."""
    if not isinstance(section, Biquad):
        raise ValueError("expected validated Biquad")
    _integer(fractional_bits, "fractional_bits", 4)
    if fractional_bits > 30:
        raise ValueError("fractional_bits must be <= 30")
    scale = 1 << fractional_bits
    orig = (section.b0, section.b1, section.b2, section.a1, section.a2)
    after = tuple(round(v * scale) / scale for v in orig)
    # Biquad validator rejects unstable or dangerously marginal quantized poles.
    changed = Biquad(*after)
    return changed, max(abs(a - b) for a, b in zip(orig, after))


def _sample_frequency(fs: Fraction, frequency_hz: Fraction) -> float:
    _rate(fs)
    if not isinstance(frequency_hz, Fraction) or not 0 <= frequency_hz <= fs / 2:
        raise ValueError("probe frequency must be an exact Fraction in [0,Nyquist]")
    return 2.0 * math.pi * float(frequency_hz / fs)


def _response_rad(plan: FIRDesign | SOSDesign, omega: float) -> complex:
    zinv = complex(math.cos(omega), -math.sin(omega))
    if isinstance(plan, FIRDesign):
        real = math.fsum(v * math.cos(omega * k) for k, v in enumerate(plan.taps))
        imag = -math.fsum(v * math.sin(omega * k) for k, v in enumerate(plan.taps))
        return complex(real, imag)
    result = 1.0 + 0.0j
    for s in plan.sections:
        z2 = zinv * zinv
        numerator = s.b0 + s.b1 * zinv + s.b2 * z2
        denominator = 1.0 + s.a1 * zinv + s.a2 * z2
        if denominator == 0:
            raise ValueError("singular frequency response: biquad denominator zero")
        result *= numerator / denominator
    return result


def frequency_response(plan: FIRDesign | SOSDesign, frequency_hz: Fraction) -> complex:
    if not isinstance(plan, (FIRDesign, SOSDesign)):
        raise ValueError("expected FIRDesign or SOSDesign")
    value = _response_rad(plan, _sample_frequency(plan.sample_rate_hz, frequency_hz))
    if not math.isfinite(value.real) or not math.isfinite(value.imag):
        raise ValueError("nonfinite filter frequency response")
    return value


def group_delay_samples(plan: FIRDesign | SOSDesign, frequency_hz: Fraction) -> float:
    """Local phase-slope estimate, undefined near response nulls or Nyquist/DC.

    Uses complex phase ratio and symmetric radian increment to avoid global
    phase unwrapping; no claim of accuracy in a sharp transition or notch.
    """
    if not isinstance(plan, (FIRDesign, SOSDesign)):
        raise ValueError("invalid filter plan")
    w = _sample_frequency(plan.sample_rate_hz, frequency_hz)
    if not 0 < w < math.pi:
        raise ValueError("phase-slope group delay undefined at DC/Nyquist here")
    h = min(1e-4, 0.25 * w, 0.25 * (math.pi - w))
    if h < 1e-8:
        raise ValueError("group-delay probe too close to frequency boundary")
    minus, at, plus = (_response_rad(plan, v) for v in (w-h, w, w+h))
    if min(abs(minus), abs(at), abs(plus)) < 1e-7:
        raise ValueError("group delay undefined/unstable near a response null")
    delay = -cmath.phase(plus / minus) / (2.0 * h)
    if not math.isfinite(delay):
        raise ValueError("nonfinite group delay")
    return delay


@dataclass(frozen=True)
class SampledBandResult:
    passband_min_db: float
    passband_max_db: float
    stopband_max_db: float
    samples_examined: int
    meets_sampled_targets: bool


def sampled_band_check(plan: FIRDesign | SOSDesign,
                       passbands_hz: tuple[tuple[Fraction, Fraction], ...],
                       stopbands_hz: tuple[tuple[Fraction, Fraction], ...],
                       passband_tolerance_db: float, stopband_min_attenuation_db: float,
                       samples_per_band: int = 81) -> SampledBandResult:
    """Finite frequency-grid *screen*, not proof between grid samples.

    The passbands target 0 dB (unity). Does not fit peaking-EQ specifications.
    """
    if not isinstance(plan, (FIRDesign, SOSDesign)):
        raise ValueError("invalid filter plan")
    if not isinstance(passbands_hz, tuple) or not passbands_hz or not isinstance(stopbands_hz, tuple) or not stopbands_hz:
        raise ValueError("need explicit nonempty passband and stopband intervals")
    for v, desc in ((passband_tolerance_db, "passband_tolerance_db"),
                    (stopband_min_attenuation_db, "stopband_min_attenuation_db")):
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0 or v > 180:
            raise ValueError(f"{desc} must be finite within (0,180]")
    _integer(samples_per_band, "samples_per_band", 3)
    if samples_per_band > 1025:
        raise ValueError("sampling grid is bounded to 1025 per band")
    fs = plan.sample_rate_hz
    def band_points(intervals: tuple[tuple[Fraction, Fraction], ...]) -> list[Fraction]:
        result = []
        if len(intervals) > 4:
            raise ValueError("maximum four band intervals")
        for band in intervals:
            if not isinstance(band, tuple) or len(band) != 2:
                raise ValueError("band must be an ordered (start,end) tuple")
            start, end = band
            if not isinstance(start, Fraction) or not isinstance(end, Fraction) or not 0 <= start < end <= fs/2:
                raise ValueError("band endpoints must be exact Hz within [0,Nyquist]")
            result.extend(start + (end-start)*Fraction(i, samples_per_band-1)
                          for i in range(samples_per_band))
        return result
    pfrequencies = band_points(passbands_hz)
    sfrequencies = band_points(stopbands_hz)
    def dB(f):
        magnitude = abs(frequency_response(plan, f))
        return -math.inf if magnitude == 0 else 20.0 * math.log10(magnitude)
    p = [dB(f) for f in pfrequencies]
    s = [dB(f) for f in sfrequencies]
    low, high, reject = min(p), max(p), max(s)
    return SampledBandResult(low, high, reject, len(p)+len(s),
                             low >= -passband_tolerance_db and
                             high <= passband_tolerance_db and
                             reject <= -stopband_min_attenuation_db)


def _validate_planes(planes: list[list[float]], channels: int) -> tuple[list[list[float]], int]:
    if not isinstance(planes, (tuple, list)) or len(planes) != channels or any(not isinstance(row, (tuple, list)) for row in planes):
        raise ValueError("planar audio must match channel count")
    count = len(planes[0])
    if not 1 <= count <= MAX_FRAMES or any(len(p) != count for p in planes):
        raise ValueError("each channel needs 1..256 matching frames")
    normalized = []
    for p in planes:
        values = []
        for x in p:
            if isinstance(x, bool) or not isinstance(x, (float, int)):
                raise ValueError("audio must be a finite real number")
            try:
                value = float(x)
            except (ValueError, OverflowError) as exc:
                raise ValueError("sample out of representable float range") from exc
            if not math.isfinite(value):
                raise ValueError("nonfinite sample")
            values.append(value)
        normalized.append(values)
    return normalized, count


class FilterStream:
    """Fixed-coefficient causal per-channel FIR or SOS, zero initial conditions.

    State lasts for a whole epoch; each push computes in a temporary state
    and commits atomically if all channels and outputs are finite.
    """
    def __init__(self, design: FIRDesign | SOSDesign, epoch_id: str,
                 origin_sample: int, channels: int):
        self._validate_config(design, epoch_id, origin_sample, channels)
        self._used_epochs = {epoch_id}
        self._initialize(design, epoch_id, origin_sample, channels)

    @staticmethod
    def _validate_config(design: FIRDesign | SOSDesign, epoch_id: str,
                         origin_sample: int, channels: int) -> None:
        if not isinstance(design, (FIRDesign, SOSDesign)):
            raise ValueError("expected designed filter")
        if not isinstance(epoch_id, str) or not epoch_id.strip():
            raise ValueError("epoch identifier must be nonempty")
        _integer(origin_sample, "origin_sample")
        _integer(channels, "channels", 1)
        if channels > MAX_CHANNELS:
            raise ValueError("at most 8 channels")

    def _initialize(self, design, epoch_id, origin, channels):
        self.design = design
        self.epoch_id = epoch_id
        self.next_sample = origin
        self.channels = channels
        self.accepted_blocks = 0
        if isinstance(design, FIRDesign):
            self._states = [[0.0] * (len(design.taps) - 1) for _ in range(channels)]
        else:
            self._states = [[[0.0, 0.0] for _ in design.sections] for _ in range(channels)]

    def push(self, start_sample: int, planes: list[list[float]]) -> dict:
        _integer(start_sample, "start_sample")
        if start_sample != self.next_sample:
            raise ValueError(f"gap or overlap; expected {self.next_sample}, received {start_sample}; new epoch required")
        data, n = _validate_planes(planes, self.channels)
        # Copy mutable histories; validation, overflow, and arithmetic failures
        # cannot advance the authoritative stream state.
        if isinstance(self.design, FIRDesign):
            trial = [v.copy() for v in self._states]
        else:
            trial = [[stage.copy() for stage in channel] for channel in self._states]
        out = []
        try:
            for ch in range(self.channels):
                samples = []
                for x in data[ch]:
                    if isinstance(self.design, FIRDesign):
                        taps = self.design.taps
                        history = trial[ch]
                        y = math.fsum([taps[0] * x] +
                                      [taps[j+1] * history[-j-1] for j in range(len(history))])
                        history.append(x)
                        history.pop(0)
                    else:
                        y = x
                        for stage_index, section in enumerate(self.design.sections):
                            s1, s2 = trial[ch][stage_index]
                            output = math.fsum((section.b0*y, s1))
                            ns1 = math.fsum((section.b1*y, -section.a1*output, s2))
                            ns2 = math.fsum((section.b2*y, -section.a2*output))
                            if not all(math.isfinite(a) for a in (output, ns1, ns2)):
                                raise ValueError("IIR state/output nonfinite")
                            trial[ch][stage_index] = [ns1, ns2]
                            y = output
                    if not math.isfinite(y):
                        raise ValueError("filter output nonfinite")
                    samples.append(y)
                out.append(samples)
        except OverflowError as exc:
            raise ValueError("filter numeric overflow; block rejected without state advancement") from exc
        self._states = trial
        self.next_sample += n
        self.accepted_blocks += 1
        return {"epoch_id": self.epoch_id, "start_sample": start_sample,
                "end_sample_exclusive": self.next_sample, "frames": n,
                "sample_rate_hz": self.design.sample_rate_hz,
                "channels": self.channels, "planar_samples": out,
                "over_reference_by_channel": [sum(abs(v) > 1 for v in row) for row in out],
                "clipped": False, "state_preserved_between_blocks": True}

    def reset_epoch(self, new_id: str, origin_sample: int,
                    design: FIRDesign | SOSDesign | None = None,
                    channels: int | None = None) -> None:
        if not isinstance(new_id, str) or not new_id.strip() or new_id in self._used_epochs:
            raise ValueError("epoch ID must be nonblank and never reused")
        plan = self.design if design is None else design
        count = self.channels if channels is None else channels
        self._validate_config(plan, new_id, origin_sample, count)
        self._initialize(plan, new_id, origin_sample, count)
        self._used_epochs.add(new_id)
