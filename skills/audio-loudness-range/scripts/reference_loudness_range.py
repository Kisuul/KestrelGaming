"""Offline EBU Tech 3342 v4 Loudness Range for ungated short-term readings."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
from decimal import (
    Context, Decimal, DivisionByZero, InvalidOperation, Overflow,
    ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_EVEN,
)
from fractions import Fraction
import math
from pathlib import Path
import sys
from typing import Literal, Sequence

# The sibling skill owns the filter, channel weighting and sample clock.
_PROGRAM_SCRIPTS = Path(__file__).resolve().parents[2] / "audio-program-loudness/scripts"
if str(_PROGRAM_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_PROGRAM_SCRIPTS))

from reference_program_loudness import (
    LoudnessConfig, LoudnessWindow, ProgramLoudnessStream, SAMPLE_RATE_HZ,
)


STANDARDS_SCOPE = "EBU Tech 3342 v4 LRA / BS.1770-5 Annex 1, 48 kHz PCM reference"
LRA_HOP_FRAMES = SAMPLE_RATE_HZ // 10
EOF_PADDING_FRAMES = SAMPLE_RATE_HZ * 3 // 2
PROVISIONAL_FRAMES = SAMPLE_RATE_HZ * 60
_ABSOLUTE_GATE_LUFS = -70.0
_RELATIVE_DROP_LU = 20
_RELATIVE_POWER_FACTOR = 100


@dataclass(frozen=True)
class LoudnessRange:
    """Percentiles and gate counts for one history of short-term readings."""

    status: Literal["insufficient_data", "silence", "below_absolute_gate", "ok"]
    window_count: int
    absolute_survivor_count: int = 0
    final_survivor_count: int = 0
    p10_lufs: float | None = None
    p95_lufs: float | None = None
    lra_lu: float | None = None
    relative_gate_lufs: float | None = None


def _level(value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("short-term level must be a real LUFS number or -inf for silence")
    try:
        level = float(value)
    except OverflowError as exc:
        raise ValueError("short-term level exceeds binary64 range") from exc
    if not (math.isfinite(level) or level == -math.inf):
        raise ValueError("short-term level must be finite or -inf for silence")
    return level if level != 0.0 else 0.0


def _power_bounds(
    levels: Counter[Decimal], peak: Decimal, lower: Context, upper: Context,
) -> tuple[dict[Decimal, tuple[Decimal, Decimal]], Decimal, Decimal]:
    """Enclose each peak-normalized power and their sum by outward rounding."""
    one, zero, ten = Decimal(1), Decimal(0), Decimal(10)
    nearest = lower.copy()
    nearest.rounding = ROUND_HALF_EVEN
    ln_ten = nearest.ln(ten)
    factor_low = lower.divide(lower.next_minus(ln_ten), ten)
    factor_high = upper.divide(upper.next_plus(ln_ten), ten)
    powers = {}
    sum_low = sum_high = zero
    for level, count in levels.items():
        if level == peak:
            power_low = power_high = one
        else:
            # level - peak is negative, so use the opposite factor bound.
            exp_low = lower.multiply(lower.subtract(level, peak), factor_high)
            exp_high = upper.multiply(upper.subtract(level, peak), factor_low)
            power_low = max(zero, lower.next_minus(nearest.exp(exp_low)))
            power_high = min(one, upper.next_plus(nearest.exp(exp_high)))
        powers[level] = power_low, power_high
        sum_low = lower.add(sum_low, lower.multiply(power_low, count))
        sum_high = upper.add(sum_high, upper.multiply(power_high, count))
    return powers, sum_low, sum_high


def _exact_relative_tie(levels: Counter[Decimal], candidate: Decimal, count: int) -> bool:
    """Test equality by carrying decade counts with exact integer arithmetic."""
    # Eisenstein's criterion at 2 makes x**D - 10 irreducible for a common
    # exponent denominator D. Positive terms outside the candidate's
    # fractional exponent class cannot cancel.
    origin = Fraction(candidate)
    decades: Counter[int] = Counter()
    decades[0] = -_RELATIVE_POWER_FACTOR * count
    for level, occurrences in levels.items():
        decade = (Fraction(level) - origin) / 10
        if decade.denominator != 1:
            return False
        decades[decade.numerator] += occurrences

    carry, previous = 0, min(decades)
    for decade, occurrences in sorted(decades.items()):
        if carry:
            gap = decade - previous
            # A nonzero carry with too few digits cannot bridge this gap.
            if gap >= len(str(abs(carry))):
                return False
            carry, remainder = divmod(carry, 10 ** gap)
            if remainder:
                return False
        carry += occurrences
        previous = decade
    return carry == 0


def _first_relative_survivor(absolute: list[float]) -> int:
    if absolute[0] == absolute[-1]:
        return 0

    # Conversion from binary64 is exact. Sorting first lets us find the first
    # surviving value with a monotone search, including its duplicates.
    ordered = [Decimal.from_float(level) for level in absolute]
    counts = Counter(ordered)
    gain = _RELATIVE_POWER_FACTOR * len(ordered)
    first, last = 0, len(ordered) - 1  # The loudest value always passes.
    for precision in (32, 64, 128, 256, 512, 1024):
        lower = Context(
            prec=precision, rounding=ROUND_FLOOR, Emin=-999_999, Emax=999_999,
            clamp=0, traps=[InvalidOperation, DivisionByZero, Overflow],
        )
        upper = lower.copy()
        upper.rounding = ROUND_CEILING
        powers, sum_low, sum_high = _power_bounds(counts, ordered[-1], lower, upper)
        while first < last:
            index = (first + last) // 2
            candidate = ordered[index]
            power_low, power_high = powers[candidate]
            if lower.multiply(power_low, gain) >= sum_high:
                last = index
            elif upper.multiply(power_high, gain) < sum_low:
                first = index + 1
            elif _exact_relative_tie(counts, candidate, len(ordered)):
                last = index
            else:
                break  # Recompute the bounds with more precision.
        if first == last:
            return first
    raise ArithmeticError("LRA relative gate could not be resolved within 1024 decimal digits")


def calculate_lra(short_term_lufs: Sequence[float]) -> LoudnessRange:
    """Apply both Tech 3342 gates and select the P10 and P95 order statistics."""
    if (not isinstance(short_term_lufs, Sequence)
            or isinstance(short_term_lufs, (str, bytes, bytearray))):
        raise ValueError("provide a sequence of short-term LUFS readings")
    levels = [_level(value) for value in short_term_lufs]
    if not levels:
        return LoudnessRange("insufficient_data", 0)
    absolute = sorted(level for level in levels if level >= _ABSOLUTE_GATE_LUFS)
    if not absolute:
        status = "silence" if max(levels) == -math.inf else "below_absolute_gate"
        return LoudnessRange(status, len(levels))

    first = _first_relative_survivor(absolute)
    count = len(absolute) - first
    # Positive half ties round upward, even when floor(index) is even.
    p10 = absolute[first + (10 * (count - 1) + 50) // 100]
    p95 = absolute[first + (95 * (count - 1) + 50) // 100]
    peak = absolute[-1]
    scaled_mean = math.fsum(10.0 ** ((level - peak) / 10.0) for level in absolute) / len(absolute)
    # Report a binary64 diagnostic. Gate decisions use the enclosed powers above.
    gate_lufs = peak + (10.0 * math.log10(scaled_mean) - _RELATIVE_DROP_LU)
    return LoudnessRange(
        "ok", len(levels), len(absolute), count, p10, p95, p95 - p10, gate_lufs,
    )


@dataclass(frozen=True)
class LoudnessRangeReport:
    """LRA plus its source clock and explicit end-of-file analysis span."""

    result: LoudnessRange
    config: LoudnessConfig
    epoch_id: str
    start_sample: int
    programme_end_sample_exclusive: int
    analysis_end_sample_exclusive: int
    last_window_end_sample_exclusive: int | None
    provisional: bool
    finalized: bool
    standards_scope: str = STANDARDS_SCOPE


def _lra_config(config: LoudnessConfig) -> LoudnessConfig:
    if not isinstance(config, LoudnessConfig):
        raise ValueError("config must be a LoudnessConfig")
    return replace(config, readout_hop_samples=LRA_HOP_FRAMES)


class LoudnessRangeStream:
    """Collect 3 s S readings at 10 Hz from Skill #20 for one PCM epoch."""

    def __init__(self, config: LoudnessConfig, *, epoch_id: str, start_sample: int):
        self._meter = ProgramLoudnessStream(
            _lra_config(config), epoch_id=epoch_id, start_sample=start_sample,
        )
        self._start_history(start_sample)

    def _start_history(self, start_sample: int) -> None:
        self._start_sample = self._programme_end = start_sample
        self._levels: list[float] = []
        self._last_window_end: int | None = None
        self._finalized = False

    @property
    def next_sample(self) -> int:
        """Next sample on the analysis clock, which includes any EOF padding."""
        return self._meter.next_sample

    def reset_epoch(self, epoch_id: str, start_sample: int,
                    config: LoudnessConfig | None = None) -> None:
        """Reset the upstream filter and clear all LRA observations."""
        self._meter.reset_epoch(
            epoch_id, start_sample, None if config is None else _lra_config(config),
        )
        self._start_history(start_sample)

    def _ingest(self, start_sample: int, planes: Sequence[Sequence[float]], *,
                epoch_id: str) -> tuple[LoudnessWindow, ...]:
        windows = self._meter.push(start_sample, planes, epoch_id=epoch_id)["short_term"]
        if windows:
            self._levels.extend(window.lufs for window in windows)
            self._last_window_end = windows[-1].end_sample_exclusive
        return windows

    def push(self, start_sample: int, planes: Sequence[Sequence[float]], *,
             epoch_id: str) -> tuple[LoudnessWindow, ...]:
        """Take contiguous planar PCM and return newly completed S windows."""
        if self._finalized:
            raise ValueError("measurement is finalized; start a new epoch")
        windows = self._ingest(start_sample, planes, epoch_id=epoch_id)
        self._programme_end = self.next_sample
        return windows

    def measure(self) -> LoudnessRangeReport:
        """Recompute LRA from all complete windows in the current epoch."""
        return LoudnessRangeReport(
            calculate_lra(self._levels),
            self._meter.config,
            self._meter.epoch_id,
            self._start_sample,
            self._programme_end,
            self.next_sample,
            self._last_window_end,
            self._programme_end - self._start_sample < PROVISIONAL_FRAMES,
            self._finalized,
        )

    def finish(self) -> LoudnessRangeReport:
        """Append 1.5 s of analysis silence once after a nonempty file."""
        if not self._finalized:
            if self._programme_end > self._start_sample:
                zeros = [0.0] * EOF_PADDING_FRAMES
                planes = [zeros] * len(self._meter.config.channel_labels)
                self._ingest(self.next_sample, planes, epoch_id=self._meter.epoch_id)
            self._finalized = True
        return self.measure()
