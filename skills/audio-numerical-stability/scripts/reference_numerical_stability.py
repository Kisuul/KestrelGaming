"""Bounded numerical audio oracles. Language-neutral contract lives in references/.

This Python reference prioritizes falsifiable semantics over realtime throughput.
Big-integer rational arithmetic is for independently checking tiny examples,
NOT for streaming DSP or a generic precision/performance recommendation.
"""
from __future__ import annotations

import cmath
from fractions import Fraction
import math
import sys
import struct

MAX_FRAMES = 256


def _samples(values: list[float], *, allow_zero: bool = True) -> tuple[float, ...]:
    if not isinstance(values, (list, tuple)) or not 1 <= len(values) <= MAX_FRAMES:
        raise ValueError('requires a nonempty sequence of at most 256 samples')
    out = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError('samples must be real, not bool or complex')
        try:
            x = float(value)
        except (OverflowError, ValueError) as exc:
            raise ValueError('sample cannot be represented in binary64') from exc
        if not math.isfinite(x):
            raise ValueError('nonfinite sample')
        out.append(x)
    if not allow_zero and not any(out):
        raise ValueError('zero-energy input')
    return tuple(out)


def _as_exact(x: float) -> Fraction:
    return Fraction.from_float(x)


def _float_checked(result: Fraction, *, label: str) -> float:
    if not isinstance(result, Fraction):
        raise ValueError('internal exact result required')
    try:
        answer = float(result)
    except (OverflowError, ValueError) as exc:
        raise ValueError(f'{label}: exact final result is not representable as finite binary64') from exc
    if not math.isfinite(answer):
        raise ValueError(f'{label}: exact final result is not representable as finite binary64')
    if result and answer == 0:
        raise ValueError(f'{label}: nonzero final result underflows binary64; no silent zero')
    return answer


def stable_rms(samples: list[float]) -> float:
    """RMS in input sample units. Max-relative squares avoid huge intermediates.

    R = max(abs(x)) * sqrt( sum((x/max)^2) / N ), not sqrt(sum(x*x)/N).
    Never divides by zero for true silence. Does not claim calibrated dBFS.
    """
    values = _samples(samples)
    peak = max(abs(x) for x in values)
    if peak == 0:
        return 0.0
    norm = math.fsum((v / peak) ** 2 for v in values)
    out = peak * math.sqrt(norm / len(values))
    if not math.isfinite(out):
        raise ValueError('RMS not representable')
    if out == 0:
        raise ValueError('nonzero RMS underflow')
    return out


def stable_enbw_bins(window: list[float]) -> float:
    """ENBW in DFT bins: N sum(w²)/(sum w)²; undefined for zero coherent sum."""
    w = _samples(window, allow_zero=False)
    scale = max(abs(x) for x in w)
    normalized = [x / scale for x in w]
    coherent = math.fsum(normalized)
    if coherent == 0:
        raise ValueError('undefined ENBW: zero coherent window gain')
    power = math.fsum(x*x for x in normalized)
    # sqrt first; coherent**2 can underflow to zero even when coherent != 0.
    ratio = math.sqrt(len(w) * power) / abs(coherent)
    if not math.isfinite(ratio) or ratio > math.sqrt(sys.float_info.max):
        raise ValueError('ENBW is not representable')
    return ratio * ratio


def exact_psd_bin(real: float, imag: float, window: list[float],
                  sample_rate: Fraction, nfft: int, bin_index: int) -> float:
    """Exact-binary-input rational periodogram oracle; not an FFT or realtime PSD.

    P[k] = factor * (Re{X[k]}²+Im{X[k]}²) / (fs * sum(w²))
    factor 2 strictly for positive non-Nyquist bins of one-sided real spectra.
    The bin is already the windowed DFT ordinate; window_length<=nfft.
    """
    if isinstance(real, bool) or isinstance(imag, bool) or not isinstance(real, (int, float)) or not isinstance(imag, (int, float)):
        raise ValueError('complex ordinate requires real/imag real scalars')
    components = _samples([real, imag])
    if not isinstance(sample_rate, Fraction) or sample_rate <= 0 or sample_rate > 384000:
        raise ValueError('explicit positive rational Hz sample_rate at most 384 kHz')
    if isinstance(nfft, bool) or not isinstance(nfft, int) or not 2 <= nfft <= MAX_FRAMES:
        raise ValueError('invalid nfft')
    if isinstance(bin_index, bool) or not isinstance(bin_index, int) or not 0 <= bin_index <= nfft // 2:
        raise ValueError('one-sided real-spectrum bin index outside range')
    w = _samples(window, allow_zero=False)
    if len(w) > nfft:
        raise ValueError('window must not exceed DFT size')
    energy = sum((_as_exact(x)**2 for x in w), Fraction(0))
    power = _as_exact(components[0])**2 + _as_exact(components[1])**2
    factor = 1 if bin_index == 0 or (nfft % 2 == 0 and bin_index == nfft//2) else 2
    return _float_checked(factor * power / (sample_rate * energy), label='PSD in sample²/Hz')


def exact_amplitude_bin(magnitude: float, window_sum: float, nfft: int,
                        bin_index: int) -> float:
    """Amplitude in sample units: factor*abs(DFT bin)/abs(sum window)."""
    v = _samples([magnitude, window_sum])
    if not isinstance(nfft, int) or isinstance(nfft, bool) or not 2 <= nfft <= MAX_FRAMES:
        raise ValueError('invalid nfft')
    if not isinstance(bin_index, int) or isinstance(bin_index, bool) or not 0 <= bin_index <= nfft//2:
        raise ValueError('invalid one-sided bin')
    if v[1] == 0:
        raise ValueError('undefined amplitude: zero coherent window gain')
    factor = 1 if bin_index == 0 or (nfft % 2 == 0 and bin_index == nfft//2) else 2
    return _float_checked(Fraction(factor)*abs(_as_exact(v[0]))/abs(_as_exact(v[1])), label='amplitude')


def stable_welch_mean(ordinates: list[float]) -> float:
    """Scaled arithmetic mean of nonnegative PSD ordinates (sample²/Hz)."""
    values = _samples(ordinates)
    if any(v < 0 for v in values):
        raise ValueError('PSD ordinates must be nonnegative')
    peak = max(values)
    if peak == 0:
        return 0.0
    avg = peak * (math.fsum(v / peak for v in values) / len(values))
    if not math.isfinite(avg):
        raise ValueError('Welch mean not representable')
    if avg == 0:
        raise ValueError('nonzero Welch mean underflow')
    return avg


def stable_signed_sum(values: list[float]) -> float:
    """Exact-rational binary-input sum oracle: cancellation and representability.

    Big-integer Fraction is deliberately an educational oracle, not a production
    reduction recommendation. Compare compensated/pairwise sums in a target backend.
    """
    seq = _samples(values)
    total = sum((_as_exact(x) for x in seq), Fraction(0))
    return _float_checked(total, label='signed sum')


def fixed_quantize_counts(counts: Fraction, bits: int, *, signed: bool, policy: str) -> dict:
    """Fixed-point integer counts, nearest ties-to-even, saturate/error; no wrap."""
    if not isinstance(counts, Fraction):
        raise ValueError('supply exact rational counts (units of one LSB)')
    if isinstance(bits, bool) or not isinstance(bits, int) or not 2 <= bits <= 32:
        raise ValueError('bit width must be 2..32')
    if not isinstance(signed, bool) or policy not in ('saturate', 'error'):
        raise ValueError('explicit signed flag and overflow policy required')
    q = round(counts)  # Fraction rounds ties to even
    lo, hi = (-2**(bits-1), 2**(bits-1)-1) if signed else (0, 2**bits-1)
    overflow = q < lo or q > hi
    if overflow and policy == 'error':
        raise ValueError('quantized count out of range')
    q = min(hi, max(lo, q))
    return {'counts':q, 'saturated':overflow, 'rounding':'nearest_ties_even',
            'low':lo, 'high':hi, 'units':'LSB counts'}


def inspect_float32(value: float) -> dict:
    """Actual platform IEEE-binary32 packing experiment, not a language norm."""
    x = _samples([value])[0]
    try:
        raw = struct.pack('<f', x)
    except (OverflowError, struct.error) as exc:
        raise ValueError('binary32 overflow') from exc
    y = struct.unpack('<f', raw)[0]
    if not math.isfinite(y):
        raise ValueError('binary32 overflow to infinity')
    return {'input_binary64':x, 'output_binary32':y,
            'loss_of_nonzero':bool(x and y == 0),
            'changed':x != y, 'hex_le':raw.hex()}


def biquad_pole_radius(a1: float, a2: float, *, quant_step: Fraction | None = None) -> dict:
    """For normalized denominator 1+a1*z^-1+a2*z^-2, roots of z²+a1 z+a2."""
    a, b = _samples([a1, a2])
    if quant_step is not None:
        if not isinstance(quant_step, Fraction) or quant_step <= 0:
            raise ValueError('positive exact quantization step required')
        a = _float_checked(Fraction(round(_as_exact(a)/quant_step))*quant_step, label='a1 coefficient')
        b = _float_checked(Fraction(round(_as_exact(b)/quant_step))*quant_step, label='a2 coefficient')
    delta = cmath.sqrt(a*a - 4*b)
    roots = ((-a+delta)/2,(-a-delta)/2)
    radius = max(abs(v) for v in roots)
    if not math.isfinite(radius):
        raise ValueError('nonfinite pole radius')
    return {'a1':a,'a2':b,'radius':radius,'stable_strict':radius < 1,
            'roots':roots,'criterion':'strict causal BIBO stability in exact coefficient model'}


class RmsAccumulator:
    """Tiny epoch-aware scaled-sum-squares reference; no realtime guarantees."""
    def __init__(self, epoch: str, sample_origin: int) -> None:
        self._used = set()
        self._initialize(epoch, sample_origin)

    @staticmethod
    def _check_epoch(epoch: str, start: int) -> None:
        if not isinstance(epoch, str) or not epoch.strip():
            raise ValueError('epoch must be nonempty')
        if isinstance(start, bool) or not isinstance(start, int) or start < 0:
            raise ValueError('start must be a nonnegative exact sample index')

    def _initialize(self, epoch: str, start: int) -> None:
        self._check_epoch(epoch, start)
        if epoch in self._used:
            raise ValueError('epoch cannot be reused')
        self.epoch = epoch
        self.next_sample = start
        self.count = 0
        self.scale = 0.0
        self.sumsq = 0.0
        self._used.add(epoch)

    def push(self, start: int, values: list[float]) -> dict:
        if isinstance(start, bool) or not isinstance(start, int) or start != self.next_sample:
            raise ValueError(f'noncontiguous block; expected {self.next_sample}')
        seq = _samples(values)
        # Validate all inputs before changing any state (atomic rejection).
        scale, sumsq = self.scale, self.sumsq
        for x in seq:
            v = abs(x)
            if v == 0:
                continue
            if scale < v:
                sumsq = 1.0 + sumsq*(scale/v)**2
                scale = v
            else:
                sumsq += (v/scale)**2
        count = self.count + len(seq)
        if not math.isfinite(sumsq):
            raise ValueError('accumulator out of range')
        # Check the *candidate* final result before committing any new state.
        # Even valid finite inputs can imply a nonzero RMS smaller than the
        # output format can represent. A rejected block is not consumed.
        result = self._rms_state(scale, sumsq, count)
        self.scale, self.sumsq = scale, sumsq
        self.count, self.next_sample = count, self.next_sample + len(seq)
        return {'epoch':self.epoch,'end_sample_exclusive':self.next_sample,
                'frames_total':self.count,'rms':result}

    @staticmethod
    def _rms_state(scale: float, sumsq: float, count: int) -> float:
        if count == 0 or scale == 0:
            return 0.0
        result = scale * math.sqrt(sumsq / count)
        if not math.isfinite(result) or result == 0:
            raise ValueError('nonzero accumulated RMS is not representable')
        return result

    def rms(self) -> float:
        return self._rms_state(self.scale, self.sumsq, self.count)

    def reset_epoch(self, epoch: str, origin: int) -> None:
        self._initialize(epoch, origin)
