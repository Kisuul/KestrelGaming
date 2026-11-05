"""Bounded, explicit PCM channel-layout mapping reference (not a mixer backend).

No inferred speaker assignment, resampling, LFE bass management, limiter,
psychoacoustic spatial rendering, or normative downmix preset is implemented.
All transfer coefficients are explicit exact rationals.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math

MAX_CHANNELS = 8
MAX_FRAMES = 256

# Microsoft WAVEFORMATEXTENSIBLE dwChannelMask order: ascending mask bit.
WAVE_POSITIONS = (
    (0x00001, "FL"), (0x00002, "FR"), (0x00004, "FC"),
    (0x00008, "LFE"), (0x00010, "BL"), (0x00020, "BR"),
    (0x00040, "FLC"), (0x00080, "FRC"), (0x00100, "BC"),
    (0x00200, "SL"), (0x00400, "SR"), (0x00800, "TC"),
    (0x01000, "TFL"), (0x02000, "TFC"), (0x04000, "TFR"),
    (0x08000, "TBL"), (0x10000, "TBC"), (0x20000, "TBR"),
)
WAVE_VALID_MASK = sum(mask for mask, _ in WAVE_POSITIONS)
WAVE_LABELS = frozenset(label for _, label in WAVE_POSITIONS)


def _integer(x: int, label: str, minimum: int = 0) -> None:
    if not isinstance(x, int) or isinstance(x, bool) or x < minimum:
        raise ValueError(f"{label} must be an integer >= {minimum}")


@dataclass(frozen=True)
class ChannelLayout:
    """Speaker labels, explicitly unassigned discrete labels, or Mid/Side signals.

    A channel-count-only buffer is not a stereo/surround speaker assignment.
    """
    labels: tuple[str, ...]
    kind: str = "speaker"

    def __post_init__(self) -> None:
        if not isinstance(self.labels, tuple) or not 1 <= len(self.labels) <= MAX_CHANNELS:
            raise ValueError("labels must be a tuple of 1..8 names")
        if any(not isinstance(v, str) or not v.strip() for v in self.labels):
            raise ValueError("every channel needs a nonempty identifier")
        if len(set(self.labels)) != len(self.labels):
            raise ValueError("channel identifiers must be distinct")
        if self.kind not in ("speaker", "discrete", "mid_side"):
            raise ValueError("unknown channel representation kind")
        if self.kind == "speaker" and any(v not in WAVE_LABELS for v in self.labels):
            raise ValueError("speaker channel identifier not in the supported WAVE set")
        if self.kind == "mid_side" and self.labels != ("M", "S"):
            raise ValueError("Mid/Side ordering is exactly (M,S)")
        if self.kind == "discrete" and any(not v.startswith("CH") or
                                           not v[2:].isdigit() for v in self.labels):
            raise ValueError("discrete channels require CH-index labels")

    @property
    def channels(self) -> int:
        return len(self.labels)


def unassigned_layout(channels: int) -> ChannelLayout:
    """Explicit count-only lanes; cannot silently become speaker channels."""
    _integer(channels, "channels", 1)
    if channels > MAX_CHANNELS:
        raise ValueError("reference channel limit exceeded")
    return ChannelLayout(tuple(f"CH{i}" for i in range(channels)), "discrete")


def from_wave_mask(mask: int, channels: int, *, allow_unassigned: bool = False) -> ChannelLayout:
    """Strict WAVE mask decoder; unknown/mismatched bits fail, unlike permissive hosts.

    mask=0 is a count-only layout *only* with allow_unassigned=True. It does
    not imply a canonical mono or stereo speaker identity.
    """
    _integer(mask, "WAVE channel mask")
    _integer(channels, "channels", 1)
    if channels > MAX_CHANNELS:
        raise ValueError("reference channel limit exceeded")
    if mask == 0:
        if allow_unassigned:
            return unassigned_layout(channels)
        raise ValueError("WAVE mask 0 has no speaker identity; request explicit unassigned layout")
    if mask & ~WAVE_VALID_MASK:
        raise ValueError("unknown or reserved WAVE channel mask bits")
    labels = tuple(label for bit, label in WAVE_POSITIONS if mask & bit)
    if len(labels) != channels:
        raise ValueError("strict WAVE layout requires number of set bits equal channel count")
    return ChannelLayout(labels, "speaker")


def _rank(rows: tuple[tuple[Fraction, ...], ...]) -> int:
    """Exact Gaussian elimination for tiny coefficient matrices."""
    a = [list(row) for row in rows]
    if not a:
        return 0
    nrow, ncol, rank = len(a), len(a[0]), 0
    for col in range(ncol):
        pivot = next((j for j in range(rank, nrow) if a[j][col]), None)
        if pivot is None:
            continue
        a[rank], a[pivot] = a[pivot], a[rank]
        value = a[rank][col]
        a[rank] = [v / value for v in a[rank]]
        for j in range(rank+1, nrow):
            factor = a[j][col]
            if factor:
                a[j] = [x - factor * y for x, y in zip(a[j], a[rank])]
        rank += 1
        if rank == nrow:
            break
    return rank


@dataclass(frozen=True)
class ChannelMatrix:
    source: ChannelLayout
    target: ChannelLayout
    # matrix[destination_channel][source_channel]
    coefficients: tuple[tuple[Fraction, ...], ...]
    purpose: str
    allow_drop: bool = False
    allow_silent_outputs: bool = False
    allow_possible_peak_gain: bool = False
    acknowledge_discrete_to_speaker: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.source, ChannelLayout) or not isinstance(self.target, ChannelLayout):
            raise ValueError("source/target must be explicit ChannelLayout values")
        if not isinstance(self.purpose, str) or not self.purpose.strip():
            raise ValueError("document a nonempty matrix purpose")
        for field in ("allow_drop", "allow_silent_outputs",
                      "allow_possible_peak_gain", "acknowledge_discrete_to_speaker"):
            if not isinstance(getattr(self, field), bool):
                raise ValueError(f"{field} must be boolean")
        if self.source.kind == "discrete" and self.target.kind != "discrete" and not self.acknowledge_discrete_to_speaker:
            raise ValueError("unassigned source channels require explicit mapping acknowledgement")
        if not isinstance(self.coefficients, (list, tuple)) or len(self.coefficients) != self.target.channels:
            raise ValueError("matrix needs one row per destination channel")
        prepared = []
        for row in self.coefficients:
            if not isinstance(row, (tuple, list)) or len(row) != self.source.channels:
                raise ValueError("each matrix row must cover all source channels")
            coeffs = []
            for v in row:
                if isinstance(v, bool) or not isinstance(v, (Fraction, int)):
                    raise ValueError("coefficients must be exact Fraction or int, not float/bool")
                f = Fraction(v)
                if abs(f) > 16:
                    raise ValueError("reference coefficient magnitude exceeds 16")
                coeffs.append(f)
            prepared.append(tuple(coeffs))
        normalized = tuple(prepared)
        used = tuple(any(row[i] != 0 for row in normalized)
                     for i in range(self.source.channels))
        silent = tuple(not any(row) for row in normalized)
        gains = tuple(sum((abs(f) for f in row), Fraction(0)) for row in normalized)
        if not all(used) and not self.allow_drop:
            raise ValueError("source channel discarded; acknowledge allow_drop")
        if any(silent) and not self.allow_silent_outputs:
            raise ValueError("silent destination; acknowledge allow_silent_outputs")
        if any(v > 1 for v in gains) and not self.allow_possible_peak_gain:
            raise ValueError("coherent peak gain may exceed 1; acknowledge headroom")
        object.__setattr__(self, "coefficients", normalized)

    @property
    def dropped_source_labels(self) -> tuple[str, ...]:
        return tuple(label for i, label in enumerate(self.source.labels)
                     if not any(row[i] for row in self.coefficients))

    @property
    def silent_target_labels(self) -> tuple[str, ...]:
        return tuple(label for row, label in zip(self.coefficients, self.target.labels)
                     if not any(row))

    @property
    def coherent_gain_bounds(self) -> tuple[Fraction, ...]:
        return tuple(sum((abs(v) for v in row), Fraction(0)) for row in self.coefficients)

    @property
    def rank(self) -> int:
        return _rank(self.coefficients)

    @property
    def loses_linear_information(self) -> bool:
        return self.rank < self.source.channels


def identity_matrix(layout: ChannelLayout) -> ChannelMatrix:
    if not isinstance(layout, ChannelLayout):
        raise ValueError("layout must be explicit")
    n = layout.channels
    return ChannelMatrix(layout, layout,
                         tuple(tuple(int(i == j) for j in range(n)) for i in range(n)),
                         "identity preservation")


def reorder_matrix(source: ChannelLayout, target: ChannelLayout) -> ChannelMatrix:
    if not isinstance(source, ChannelLayout) or not isinstance(target, ChannelLayout):
        raise ValueError("source/target must be explicit")
    if source.kind != target.kind or set(source.labels) != set(target.labels):
        raise ValueError("reordering requires same representation and exact label set")
    return ChannelMatrix(source, target,
                         tuple(tuple(int(a == b) for b in source.labels) for a in target.labels),
                         "label-preserving permutation")


def mid_side_encode() -> ChannelMatrix:
    return ChannelMatrix(ChannelLayout(("FL", "FR")),
                         ChannelLayout(("M", "S"), "mid_side"),
                         ((Fraction(1, 2), Fraction(1, 2)),
                          (Fraction(1, 2), Fraction(-1, 2))),
                         "M=(L+R)/2; S=(L-R)/2, amplitude normalization")


def mid_side_decode() -> ChannelMatrix:
    return ChannelMatrix(ChannelLayout(("M", "S"), "mid_side"),
                         ChannelLayout(("FL", "FR")),
                         ((1, 1), (1, -1)), "L=M+S; R=M-S",
                         allow_possible_peak_gain=True)


def _validate_audio(planes: list[list[float]], n: int) -> tuple[list[list[float]], int]:
    if not isinstance(planes, (list, tuple)) or len(planes) != n:
        raise ValueError("input must have one planar signal per source channel")
    if any(not isinstance(p, (list, tuple)) for p in planes):
        raise ValueError("channel buffers must be lists or tuples")
    count = len(planes[0])
    if not 1 <= count <= MAX_FRAMES or any(len(p) != count for p in planes):
        raise ValueError("nonempty equal-length channels required, maximum 256 frames")
    data = []
    for plane in planes:
        row = []
        for x in plane:
            if isinstance(x, bool) or not isinstance(x, (int, float)):
                raise ValueError("audio values must be finite real numbers")
            try:
                v = float(x)
            except (ValueError, OverflowError) as exc:
                raise ValueError("audio value cannot be represented as finite float") from exc
            if not math.isfinite(v):
                raise ValueError("nonfinite audio sample")
            row.append(v)
        data.append(row)
    return data, count


def apply_channel_matrix(planes: list[list[float]], plan: ChannelMatrix,
                         *, epoch_id: str, start_sample: int) -> dict:
    """No temporal filtering. Inputs and outputs share exactly the same sample clock."""
    if not isinstance(plan, ChannelMatrix):
        raise ValueError("plan must be a ChannelMatrix")
    if not isinstance(epoch_id, str) or not epoch_id.strip():
        raise ValueError("epoch identifier must be nonempty")
    _integer(start_sample, "start_sample")
    data, frames = _validate_audio(planes, plan.source.channels)
    output = [[] for _ in plan.target.labels]
    over_ref = [0] * plan.target.channels
    for i, row in enumerate(plan.coefficients):
        single = [(j, coefficient) for j, coefficient in enumerate(row) if coefficient]
        try:
            if len(single) == 1 and single[0][1] == 1:
                # Identity / reordering should preserve signed floating zero.
                out = data[single[0][0]].copy()
            else:
                weights = tuple(float(w) for w in row)
                out = [math.fsum(weights[j] * data[j][k]
                                 for j in range(plan.source.channels))
                       for k in range(frames)]
        except (OverflowError, ValueError) as exc:
            raise ValueError("nonrepresentable channel-matrix output") from exc
        if any(not math.isfinite(v) for v in out):
            raise ValueError("nonfinite output channel")
        output[i] = out
        over_ref[i] = sum(abs(x) > 1 for x in out)
    return {
        "epoch_id": epoch_id,
        "start_sample": start_sample,
        "end_sample_exclusive": start_sample + frames,
        "frames": frames,
        "input_labels": plan.source.labels,
        "output_labels": plan.target.labels,
        "input_kind": plan.source.kind,
        "output_kind": plan.target.kind,
        "planar_samples": output,
        "dropped_source_labels": plan.dropped_source_labels,
        "silent_target_labels": plan.silent_target_labels,
        "coherent_gain_bounds": plan.coherent_gain_bounds,
        "matrix_rank": plan.rank,
        "loses_linear_information": plan.loses_linear_information,
        "over_reference_by_output": over_ref,
        "clipped": False,  # An assertion about THIS conversion, not the input history.
        "purpose": plan.purpose,
    }


class ChannelMapStream:
    """Tiny epoch-aware reference. Matrix is stateless; continuity is not."""

    def __init__(self, plan: ChannelMatrix, epoch_id: str, origin_sample: int):
        if not isinstance(plan, ChannelMatrix):
            raise ValueError("plan must be a ChannelMatrix")
        if not isinstance(epoch_id, str) or not epoch_id.strip():
            raise ValueError("epoch_id must be nonempty")
        _integer(origin_sample, "origin_sample")
        self._used_epochs = {epoch_id}
        self.plan = plan
        self.epoch_id = epoch_id
        self.next_sample = origin_sample
        self.accepted_blocks = 0

    def push(self, start_sample: int, planes: list[list[float]]) -> dict:
        _integer(start_sample, "start_sample")
        if start_sample != self.next_sample:
            raise ValueError(f"noncontiguous audio mapping: expected {self.next_sample}, "
                             f"observed {start_sample}; new epoch required")
        result = apply_channel_matrix(planes, self.plan,
                                      epoch_id=self.epoch_id, start_sample=start_sample)
        self.next_sample = result["end_sample_exclusive"]
        self.accepted_blocks += 1
        return result

    def reset_epoch(self, new_epoch_id: str, origin_sample: int,
                    plan: ChannelMatrix | None = None) -> None:
        if not isinstance(new_epoch_id, str) or not new_epoch_id.strip():
            raise ValueError("new_epoch_id must be nonempty")
        if new_epoch_id in self._used_epochs:
            raise ValueError("epoch identifier cannot be reused")
        _integer(origin_sample, "origin_sample")
        next_plan = self.plan if plan is None else plan
        if not isinstance(next_plan, ChannelMatrix):
            raise ValueError("plan must be a ChannelMatrix")
        self.plan = next_plan
        self.epoch_id = new_epoch_id
        self.next_sample = origin_sample
        self.accepted_blocks = 0
        self._used_epochs.add(new_epoch_id)
