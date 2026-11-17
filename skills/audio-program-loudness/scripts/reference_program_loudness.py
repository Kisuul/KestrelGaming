"""Offline 48 kHz BS.1770-5 Annex 1 reference with EBU M/S/I time scales."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from fractions import Fraction
from itertools import chain, islice
import math
from typing import Literal, Sequence


SAMPLE_RATE_HZ = 48_000
MOMENTARY_FRAMES = 19_200
SHORT_TERM_FRAMES = 144_000
GATE_HOP_FRAMES = 4_800
READOUT_GRID_FRAMES = 480
STANDARDS_SCOPE = "BS.1770-5 Annex 1 / Tech 3341 v4 M/S/I, 48 kHz educational reference"

# BS.1770-5 Annex 1 Tables 1 and 2. Each denominator is 1 + a1*z^-1 + a2*z^-2.
_SHELF = (1.53512485958697, -2.69169618940638, 1.19839281085285,
          -1.69065929318241, 0.73248077421585)
_RLB = (1.0, -2.0, 1.0, -1.99004745483398, 0.99007225036621)
_POWER_WEIGHTS = {"MONO": 1.0, "L": 1.0, "R": 1.0, "C": 1.0, "LS": 1.41, "RS": 1.41}
_FIVE_MAIN = frozenset(("L", "R", "C", "LS", "RS"))
_LAYOUTS = (
    frozenset(("MONO",)), frozenset(("L",)), frozenset(("R",)), frozenset(("C",)),
    frozenset(("L", "R")), _FIVE_MAIN, _FIVE_MAIN | {"LFE"},
)
_LOUDNESS_OFFSET = -0.691
# Exact published gate T = 10**(-69309/20000) lies strictly between this
# binary64 value and its successor. Compare to the lower neighbor, not a
# rounded evaluation of T. See the contract and exact-integer bracket test.
_ABSOLUTE_GATE_RMS_FLOOR = float.fromhex("0x1.670bbcee4aad0p-12")
_RELATIVE_GATE_DIVISOR = math.sqrt(10.0)
_FilterState = tuple[float, float, float, float]
_ZERO_FILTER_STATE = (0.0, 0.0, 0.0, 0.0)


def _integer(value: int, name: str, minimum: int = 0) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")


def _finite(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite real number")
    try:
        result = float(value)
    except OverflowError as exc:
        raise ValueError(f"{name} exceeds binary64 range") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


@dataclass(frozen=True)
class LoudnessConfig:
    """One labeled layout and tap, with PCM referenced to unit amplitude."""

    sample_rate_hz: int
    channel_labels: tuple[str, ...]
    source_tap: str
    readout_hop_samples: int = READOUT_GRID_FRAMES

    def __post_init__(self) -> None:
        _integer(self.sample_rate_hz, "sample_rate_hz", 1)
        if self.sample_rate_hz != SAMPLE_RATE_HZ:
            raise ValueError("only 48,000 Hz is supported by the published coefficients")
        labels = self.channel_labels
        if not isinstance(labels, tuple) or any(not isinstance(label, str) for label in labels):
            raise ValueError("channel_labels must be an ordered tuple of names")
        if len(set(labels)) != len(labels) or frozenset(labels) not in _LAYOUTS:
            raise ValueError("expected unique labels for mono, stereo, 5.0, or 5.1")
        if not isinstance(self.source_tap, str) or not self.source_tap.strip():
            raise ValueError("source_tap must identify the measured signal")
        _integer(self.readout_hop_samples, "readout_hop_samples", READOUT_GRID_FRAMES)
        if self.readout_hop_samples % READOUT_GRID_FRAMES:
            raise ValueError("readout_hop_samples must be a multiple of 480")


@dataclass(frozen=True)
class LoudnessWindow:
    start_sample: int
    end_sample_exclusive: int
    lufs: float


@dataclass(frozen=True)
class GatedLoudness:
    status: Literal["insufficient_data", "silence", "below_absolute_gate", "ok"]
    integrated_lufs: float | None
    absolute_gated_lufs: float | None
    relative_gate_lufs: float | None
    complete_block_count: int
    absolute_survivor_count: int
    final_survivor_count: int


def _root_mean_power(amplitudes: Sequence[float], frames: int) -> float:
    """Root of sum of squares divided by frames, including all channel terms."""
    scale = max(map(abs, amplitudes))
    if scale == 0.0:
        return 0.0
    scaled_mean = math.fsum((value / scale) ** 2 for value in amplitudes) / frames
    result = scale * math.sqrt(scaled_mean)
    if not math.isfinite(result):
        raise ValueError("weighted RMS exceeds binary64 range")
    return result


def _lufs(rms: float) -> float:
    return -math.inf if rms == 0.0 else _LOUDNESS_OFFSET + 20.0 * math.log10(rms)


def integrate_block_rms(block_rms: Sequence[float]) -> GatedLoudness:
    """Gate exact binary64 roots; RMS reductions and LUFS outputs remain rounded.

    Relative decisions use exact rational powers: 10*N*r_j**2 > sum(r_i**2).
    This offline reference deliberately favors correctness over query speed.
    """
    roots = [_finite(value, "block RMS") for value in block_rms]
    if any(value < 0.0 for value in roots):
        raise ValueError("block RMS must be nonnegative")
    count = len(roots)
    if count == 0:
        return GatedLoudness("insufficient_data", None, None, None, 0, 0, 0)
    absolute = [value for value in roots if value > _ABSOLUTE_GATE_RMS_FLOOR]
    if not absolute:
        status = "below_absolute_gate" if any(roots) else "silence"
        return GatedLoudness(status, None, None, None, count, 0, 0)

    absolute_mean_rms = _root_mean_power(absolute, len(absolute))
    relative_gate_rms = absolute_mean_rms / _RELATIVE_GATE_DIVISOR
    # Avoid rounding a sqrt/normalization chain before a discontinuous decision.
    powers = [Fraction.from_float(value) ** 2 for value in absolute]
    power_sum = sum(powers, Fraction(0))
    survivors = [value for value, power in zip(absolute, powers)
                 if 10 * len(absolute) * power > power_sum]
    integrated_rms = _root_mean_power(survivors, len(survivors))
    return GatedLoudness("ok", _lufs(integrated_rms), _lufs(absolute_mean_rms),
                         _lufs(relative_gate_rms), count, len(absolute), len(survivors))


def _filter_into(plane: Sequence[float], start: int, end: int, state: _FilterState,
                 amplitude_weight: float, output: list[float]) -> _FilterState:
    """Append K-weighted, amplitude-weighted samples using transposed biquads."""
    shelf_d1, shelf_d2, rlb_d1, rlb_d2 = state
    sb0, sb1, sb2, sa1, sa2 = _SHELF
    rb0, rb1, rb2, ra1, ra2 = _RLB
    for index in range(start, end):
        sample = _finite(plane[index], "audio sample")
        shelf = sb0 * sample + shelf_d1
        shelf_d1 = sb1 * sample - sa1 * shelf + shelf_d2
        shelf_d2 = sb2 * sample - sa2 * shelf
        filtered = rb0 * shelf + rlb_d1
        rlb_d1 = rb1 * shelf - ra1 * filtered + rlb_d2
        rlb_d2 = rb2 * shelf - ra2 * filtered
        weighted = filtered * amplitude_weight
        if not math.isfinite(weighted):
            raise ValueError("K-weighted sample exceeds binary64 range")
        output.append(weighted)
    next_state = shelf_d1, shelf_d2, rlb_d1, rlb_d2
    if not all(map(math.isfinite, next_state)):
        raise ValueError("K-weighting state exceeds binary64 range")
    return next_state


def _window_rms(cells: deque[float], frames: int) -> float:
    cell_count = frames // READOUT_GRID_FRAMES
    recent = tuple(islice(reversed(cells), cell_count))
    return _root_mean_power(recent, cell_count)


class ProgramLoudnessStream:
    """Contiguous planar PCM with atomic pushes and explicit epoch transitions."""

    def __init__(self, config: LoudnessConfig, *, epoch_id: str, start_sample: int):
        self._used_epochs: set[str] = set()
        self._start_epoch(config, epoch_id, start_sample)

    @property
    def config(self) -> LoudnessConfig:
        return self._config

    @property
    def epoch_id(self) -> str:
        return self._epoch_id

    @property
    def next_sample(self) -> int:
        return self._next_sample

    @property
    def gate_block_rms(self) -> tuple[float, ...]:
        return tuple(self._gate_blocks)

    def _start_epoch(self, config: LoudnessConfig, epoch_id: str, start_sample: int) -> None:
        if not isinstance(config, LoudnessConfig):
            raise ValueError("config must be a LoudnessConfig")
        if not isinstance(epoch_id, str) or not epoch_id.strip() or epoch_id in self._used_epochs:
            raise ValueError("epoch ID must be nonblank and never reused")
        _integer(start_sample, "start_sample")
        self._config = config
        self._epoch_id = epoch_id
        self._origin = self._next_sample = start_sample
        self._used_epochs.add(epoch_id)
        self._main_planes = tuple(
            (index, math.sqrt(_POWER_WEIGHTS[label]))
            for index, label in enumerate(config.channel_labels) if label != "LFE"
        )
        self._filter_states = [_ZERO_FILTER_STATE for _ in self._main_planes]
        self._pending: list[list[float]] = [[] for _ in self._main_planes]
        self._cells: deque[float] = deque(maxlen=SHORT_TERM_FRAMES // READOUT_GRID_FRAMES)
        self._gate_blocks: list[float] = []

    def reset_epoch(self, epoch_id: str, start_sample: int,
                    config: LoudnessConfig | None = None) -> None:
        """Discard filter and measurement state before accepting a fresh epoch."""
        self._start_epoch(self.config if config is None else config, epoch_id, start_sample)

    def push(self, start_sample: int, planes: Sequence[Sequence[float]], *, epoch_id: str) -> dict:
        """Process one chunk and return its newly completed M/S readings."""
        _integer(start_sample, "start_sample")
        if epoch_id != self.epoch_id or start_sample != self.next_sample:
            raise ValueError(f"expected epoch {self.epoch_id!r} at sample {self.next_sample}")
        labels = self.config.channel_labels
        if (not isinstance(planes, (list, tuple)) or len(planes) != len(labels)
                or any(not isinstance(plane, (list, tuple)) for plane in planes)):
            raise ValueError("provide one planar list or tuple for each named channel")
        frames = len(planes[0])
        if frames == 0 or any(len(plane) != frames for plane in planes):
            raise ValueError("audio planes must be nonempty and have equal length")
        if "LFE" in labels:
            for sample in planes[labels.index("LFE")]:
                _finite(sample, "LFE sample")

        states = self._filter_states.copy()
        cells = self._cells.copy()
        pending = [samples.copy() for samples in self._pending]
        gate_blocks = []
        momentary = []
        short_term = []
        readout_hop = self.config.readout_hop_samples
        offset = 0
        while offset < frames:
            elapsed = start_sample + offset - self._origin
            cell_remaining = READOUT_GRID_FRAMES - elapsed % READOUT_GRID_FRAMES
            stop = min(frames, offset + cell_remaining)
            for channel, (plane_index, weight) in enumerate(self._main_planes):
                states[channel] = _filter_into(planes[plane_index], offset, stop,
                                               states[channel], weight, pending[channel])
            elapsed += stop - offset
            offset = stop
            if elapsed % READOUT_GRID_FRAMES:
                continue

            cells.append(_root_mean_power(list(chain.from_iterable(pending)), READOUT_GRID_FRAMES))
            for samples in pending:
                samples.clear()
            end = self._origin + elapsed
            since_first_m = elapsed - MOMENTARY_FRAMES
            emits_m = since_first_m >= 0 and since_first_m % readout_hop == 0
            emits_gate = since_first_m >= 0 and since_first_m % GATE_HOP_FRAMES == 0
            if emits_m or emits_gate:
                rms = _window_rms(cells, MOMENTARY_FRAMES)
                if emits_m:
                    momentary.append(LoudnessWindow(end - MOMENTARY_FRAMES, end, _lufs(rms)))
                if emits_gate:
                    gate_blocks.append(rms)
            since_first_s = elapsed - SHORT_TERM_FRAMES
            if since_first_s >= 0 and since_first_s % readout_hop == 0:
                rms = _window_rms(cells, SHORT_TERM_FRAMES)
                short_term.append(LoudnessWindow(end - SHORT_TERM_FRAMES, end, _lufs(rms)))

        # A rejected PCM sample or arithmetic failure leaves all prior state intact.
        end = start_sample + frames
        self._gate_blocks.extend(gate_blocks)
        self._filter_states, self._cells, self._pending = states, cells, pending
        self._next_sample = end
        return self._context(start_sample, end) | {
            "momentary": tuple(momentary), "short_term": tuple(short_term),
        }

    def _context(self, start_sample: int, end_sample: int) -> dict:
        return {
            "config": self.config,
            "standards_scope": STANDARDS_SCOPE,
            "epoch_id": self.epoch_id,
            "start_sample": start_sample,
            "end_sample_exclusive": end_sample,
        }

    def integrated(self) -> dict:
        """Recalculate I and both gate counts for the current epoch."""
        gating = integrate_block_rms(self._gate_blocks)
        gate_end = None
        if self._gate_blocks:
            gate_end = self._origin + MOMENTARY_FRAMES + (len(self._gate_blocks) - 1) * GATE_HOP_FRAMES
        return self._context(self._origin, self.next_sample) | {
            "gating": gating, "gate_end_sample_exclusive": gate_end,
        }
