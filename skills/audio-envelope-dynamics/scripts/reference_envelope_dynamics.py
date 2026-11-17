"""Offline educational envelope/gain-control reference; NOT a certified dynamics processor.

1/e (63.212% step) time constants; sample-clocked and allocation-heavy by design.
No interpolation, lookahead, gain application, host callbacks or true-peak guarantee.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Literal, Sequence


Convention = Literal["one_e", "rise_90", "residual_minus60_db"]
Detector = Literal["peak", "rms"]
Link = Literal["independent", "max"]
Phase = Literal["attack", "release", "steady"]
MAX_SAMPLE_RATE = 1_000_000_000
_CONVENTION_FACTOR = {
    "one_e": 1.0,
    "rise_90": math.log(10.0),
    "residual_minus60_db": math.log(1000.0),
}


def _finite_real(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite real number")
    try:
        converted = float(value)
    except OverflowError as exc:
        raise ValueError(f"{name} exceeds binary64") from exc
    if not math.isfinite(converted):
        raise ValueError(f"{name} must be finite")
    return converted


def _nonnegative(value: object, name: str) -> float:
    result = _finite_real(value, name)
    if result < 0:
        raise ValueError(f"{name} must be nonnegative")
    return result


def _sample_rate(value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= MAX_SAMPLE_RATE:
        raise ValueError(f"sample_rate_hz must be an integer in [1, {MAX_SAMPLE_RATE}]")


def _sample_index(value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("sample index must be a nonnegative integer")


def one_pole_weight(sample_rate_hz: int, time_seconds: float,
                    convention: Convention = "one_e") -> float:
    """Return beta for e <- e + beta*(target-e); tau=0 tracks immediately.

    The alternate time conventions mean 90% rise or -60dB amplitude error
    remaining after *time_seconds*, respectively. No hidden conversion.
    """
    _sample_rate(sample_rate_hz)
    seconds = _nonnegative(time_seconds, "time_seconds")
    if convention not in _CONVENTION_FACTOR:
        raise ValueError("unknown envelope time convention")
    if seconds == 0:
        return 1.0
    # Divide by fs before tau so fs*tau cannot overflow for long releases.
    exponent = -(_CONVENTION_FACTOR[convention] / sample_rate_hz) / seconds
    weight = -math.expm1(exponent)
    if weight <= 0 or not math.isfinite(weight):
        raise ValueError("time constant is unrepresentable for this sample rate")
    return min(1.0, weight)


@dataclass(frozen=True)
class EnvelopeConfig:
    sample_rate_hz: int
    channel_labels: tuple[str, ...]
    source_tap: str
    detector: Detector
    link: Link
    attack_seconds: float
    release_seconds: float
    convention: Convention = "one_e"
    initial_envelope: float = 0.0

    def __post_init__(self) -> None:
        _sample_rate(self.sample_rate_hz)
        if (not isinstance(self.channel_labels, tuple) or not self.channel_labels
                or len(self.channel_labels) > 32
                or any(not isinstance(label, str) or not label.strip()
                       for label in self.channel_labels)
                or len(set(self.channel_labels)) != len(self.channel_labels)):
            raise ValueError("channel_labels must contain 1..32 distinct nonblank names")
        if not isinstance(self.source_tap, str) or not self.source_tap.strip():
            raise ValueError("source_tap must name the measured input")
        if self.detector not in ("peak", "rms") or self.link not in ("independent", "max"):
            raise ValueError("unknown detector or link mode")
        one_pole_weight(self.sample_rate_hz, self.attack_seconds, self.convention)
        one_pole_weight(self.sample_rate_hz, self.release_seconds, self.convention)
        _nonnegative(self.initial_envelope, "initial_envelope")


@dataclass(frozen=True)
class EnvelopeFrame:
    sample_index: int
    detector_targets: tuple[float, ...]
    envelopes: tuple[float, ...]
    phases: tuple[Phase, ...]


def _follower_step(old: float, target: float, attack_beta: float,
                   release_beta: float, mode: Detector) -> tuple[float, Phase]:
    if target == old:
        return old, "steady"
    rising = target > old
    beta = attack_beta if rising else release_beta
    if beta == 1.0:
        return target, "attack" if rising else "release"
    if mode == "rms":
        # Numerically robust form of q <- (1-beta)*q+beta*target**2,
        # with old=sqrt(q). The raw square may overflow for valid float PCM.
        result = math.hypot(math.sqrt(1.0 - beta) * old, math.sqrt(beta) * target)
    else:
        result = old + beta * (target - old)
    if not math.isfinite(result):
        raise ValueError("envelope exceeds binary64 range")
    if result < 0:
        raise ArithmeticError("computed negative envelope")
    return result, "attack" if rising else "release"


class EnvelopeStream:
    """Per-sample peak or exponentially smoothed RMS, with exact integer clock.

    In max mode the *input magnitude* maximum feeds one shared follower.
    This is not a maximum of independently smoothed channel envelopes.
    One push commits atomically; no realtime-allocation guarantees.
    """

    def __init__(self, config: EnvelopeConfig, *, epoch_id: str, start_sample: int):
        self._used_epochs: set[str] = set()
        self.reset_epoch(epoch_id, start_sample, config)

    @property
    def config(self) -> EnvelopeConfig:
        return self._config

    @property
    def epoch_id(self) -> str:
        return self._epoch_id

    @property
    def next_sample(self) -> int:
        return self._next_sample

    @property
    def envelope(self) -> tuple[float, ...]:
        return tuple(self._state)

    def reset_epoch(self, epoch_id: str, start_sample: int,
                    config: EnvelopeConfig | None = None) -> None:
        if config is None:
            config = self._config
        if not isinstance(config, EnvelopeConfig):
            raise ValueError("config must be an EnvelopeConfig")
        _sample_index(start_sample)
        if (not isinstance(epoch_id, str) or not epoch_id.strip()
                or epoch_id in self._used_epochs):
            raise ValueError("epoch_id must be nonblank and unused")
        count = len(config.channel_labels) if config.link == "independent" else 1
        self._config = config
        self._epoch_id = epoch_id
        self._next_sample = start_sample
        self._state = [float(config.initial_envelope)] * count
        self._attack_beta = one_pole_weight(config.sample_rate_hz, config.attack_seconds,
                                            config.convention)
        self._release_beta = one_pole_weight(config.sample_rate_hz, config.release_seconds,
                                             config.convention)
        self._used_epochs.add(epoch_id)

    def push(self, start_sample: int, planes: Sequence[Sequence[float]], *,
             epoch_id: str) -> tuple[EnvelopeFrame, ...]:
        _sample_index(start_sample)
        if epoch_id != self.epoch_id or start_sample != self.next_sample:
            raise ValueError("epoch or sample cursor mismatch; start a fresh epoch")
        if (not isinstance(planes, (tuple, list))
                or len(planes) != len(self.config.channel_labels)
                or any(not isinstance(p, (tuple, list)) for p in planes)):
            raise ValueError("provide one planar tuple/list for every declared channel")
        frames = len(planes[0])
        if any(len(p) != frames for p in planes):
            raise ValueError("all planes must contain the same frame count")
        # Validate *all* input before computation to keep failures atomic.
        samples = tuple(tuple(_finite_real(x, "PCM sample") for x in p) for p in planes)
        state = self._state.copy()
        result = []
        for offset in range(frames):
            magnitudes = tuple(abs(plane[offset]) for plane in samples)
            targets = magnitudes if self.config.link == "independent" else (max(magnitudes),)
            phases = []
            for ch, target in enumerate(targets):
                state[ch], phase = _follower_step(state[ch], target, self._attack_beta,
                                                 self._release_beta, self.config.detector)
                phases.append(phase)
            result.append(EnvelopeFrame(start_sample + offset, targets, tuple(state),
                                        tuple(phases)))
        self._state = state
        self._next_sample += frames
        return tuple(result)


def compressor_gain_db(level_dbfs: float, threshold_dbfs: float, ratio: float) -> float:
    """Hard-knee feed-forward compressor target in dB gain (<= 0)."""
    threshold = _finite_real(threshold_dbfs, "threshold_dbfs")
    r = _finite_real(ratio, "ratio")
    if r < 1:
        raise ValueError("compressor ratio must be >=1")
    if level_dbfs == -math.inf:
        return 0.0
    level = _finite_real(level_dbfs, "level_dbfs")
    if level <= threshold or r == 1:
        return 0.0
    result = -(1.0 - 1.0 / r) * (level - threshold)
    if not math.isfinite(result):
        raise ValueError("gain request exceeds binary64 range")
    return result


def expander_gain_db(level_dbfs: float, threshold_dbfs: float, ratio: float) -> float:
    """Hard-knee downward expander; a silent level requests mute (-inf dB)."""
    threshold = _finite_real(threshold_dbfs, "threshold_dbfs")
    r = _finite_real(ratio, "ratio")
    if r < 1:
        raise ValueError("expander ratio must be >=1")
    if level_dbfs == -math.inf:
        return 0.0 if r == 1 else -math.inf
    level = _finite_real(level_dbfs, "level_dbfs")
    if level >= threshold or r == 1:
        return 0.0
    result = -(r - 1.0) * (threshold - level)
    if not math.isfinite(result):
        raise ValueError("gain request exceeds binary64 range")
    return result


def amplitude_dbfs(amplitude: float) -> float:
    magnitude = _nonnegative(amplitude, "amplitude")
    return -math.inf if magnitude == 0 else 20.0 * math.log10(magnitude)


@dataclass(frozen=True)
class GainFrame:
    sample_index: int
    requested_reduction_db: float
    applied_reduction_db: float
    gain_db: float
    gain_linear: float
    phase: Phase


class GainReductionStream:
    """Smooth requested nonnegative dB attenuation, not signal magnitude.

    This is a control-envelope demonstrator. It neither detects PCM nor
    applies a gain to audio, and it does not promise overshoot-free limiting.
    """

    def __init__(self, *, sample_rate_hz: int, attack_seconds: float,
                 release_seconds: float, epoch_id: str, start_sample: int,
                 convention: Convention = "one_e"):
        self._sample_rate_hz = sample_rate_hz
        self._attack_beta = one_pole_weight(sample_rate_hz, attack_seconds, convention)
        self._release_beta = one_pole_weight(sample_rate_hz, release_seconds, convention)
        self._used_epochs: set[str] = set()
        self._state = 0.0
        self.reset_epoch(epoch_id, start_sample)

    @property
    def next_sample(self) -> int:
        return self._next_sample

    @property
    def reduction_db(self) -> float:
        return self._state

    @property
    def epoch_id(self) -> str:
        return self._epoch_id

    def reset_epoch(self, epoch_id: str, start_sample: int) -> None:
        _sample_index(start_sample)
        if (not isinstance(epoch_id, str) or not epoch_id.strip()
                or epoch_id in self._used_epochs):
            raise ValueError("epoch_id must be nonblank and unused")
        self._state = 0.0
        self._next_sample = start_sample
        self._epoch_id = epoch_id
        self._used_epochs.add(epoch_id)

    def push(self, start_sample: int, requested_reduction_db: Sequence[float], *,
             epoch_id: str) -> tuple[GainFrame, ...]:
        _sample_index(start_sample)
        if epoch_id != self.epoch_id or start_sample != self.next_sample:
            raise ValueError("epoch or sample cursor mismatch")
        if not isinstance(requested_reduction_db, (tuple, list)):
            raise ValueError("reduction targets must be a sequence")
        targets = [_nonnegative(v, "reduction_db") for v in requested_reduction_db]
        state = self._state
        result = []
        for index, target in enumerate(targets):
            state, phase = _follower_step(state, target, self._attack_beta,
                                          self._release_beta, "peak")
            gain_db = -state
            gain_linear = 10.0 ** (gain_db / 20.0)
            if not math.isfinite(gain_linear):
                raise ValueError("gain is not representable")
            result.append(GainFrame(start_sample + index, target, state, gain_db,
                                    gain_linear, phase))
        self._state = state
        self._next_sample += len(targets)
        return tuple(result)
