# 48 kHz programme loudness contract

- [Standards and profile](#standards-and-profile)
- [Inputs and channel mapping](#inputs-and-channel-mapping)
- [Filtering, windows and gating](#filtering-windows-and-gating)
- [Reference API and numerical behavior](#reference-api-and-numerical-behavior)
- [Verification and use cases](#verification-and-use-cases)

## Standards and profile

Annex 1 specifies the filter, power weights and gated loudness for up to
five main channels. Use Tables 1–3 and equations (1)–(7). Use Annex 2 for
true peak, Annex 3 for advanced channel-based beds and Annex 4 for objects.
[ITU-R BS.1770-5 (11/2023)](https://www.itu.int/dms_pubrec/itu-r/rec/bs/R-REC-BS.1770-5-202311-I%21%21PDF-E.pdf) ·
[ITU edition catalogue](https://www.itu.int/rec/R-REC-BS.1770/en)

Tech 3341 §§2.1–2.3 specifies M, S and I. Sections 2.5, 2.9 and Table 1 cover
units, alignment and the ±0.1 LUFS loudness test tolerance. Use Tech 3342
for Loudness Range. [EBU Tech 3341 v4 (11/2023)](https://tech.ebu.ch/docs/tech/tech3341.pdf)

BS.1770 loudness is a standardized measurement model, not a universal
subjective-loudness estimate or an acoustic SPL measurement. Calibration tones
test meter behavior; agreement on tones alone does not validate perception
across listeners, content and playback conditions.

R 128 recommends normalizing whole-programme I to −23 LUFS for its delivery
workflow. It allows ±1.0 LU in impractical cases such as live programmes and
±0.2 LU for QC implementation errors. Under its reference, 0 LU corresponds
to −23 LUFS. Peak levels remain a separate acceptance check.
[EBU R 128 v5 (11/2023)](https://tech.ebu.ch/publications/r128)

## Inputs and channel mapping

Use one 48,000 Hz clock and planar, binary64-compatible PCM. Normalize source
PCM to nominal full-scale amplitude 1 with a declared format conversion.
Float headroom above 1 is allowed when the arithmetic is representable.
Supply the input tap and a unique epoch ID. Use integer sample indexes in
the same clock domain throughout the epoch. Declare the channel identities
in the same order as their planes. Use one of these label sets.

| Layout | Labels in any declared order | Power weights |
| --- | --- | --- |
| Mono | `MONO`, or one of `L`, `R`, `C` | 1.0 |
| Stereo | `L`, `R` | 1.0 each |
| 5.0 | `L`, `R`, `C`, `LS`, `RS` | Fronts 1.0, surrounds 1.41 |
| 5.1 | `L`, `R`, `C`, `LS`, `RS`, `LFE` | Same as 5.0, LFE excluded |

These are labels for the intended Annex 1 speaker roles. Confirm the roles
from source metadata before translating container-specific labels. Decode
and do any downmix, bass management, mono duplication, or gain changes
upstream of the declared tap. Duplicating the same mono signal into L and R
adds about 3.01 LU when that change preserves gate membership. Check values
in every plane, including excluded LFE, for valid PCM representation.

## Filtering, windows and gating

Apply the shelf then RLB high-pass independently to each included channel.
The recurrence uses `H(z) = (b0 + b1*z^-1 + b2*z^-2) / (1 + a1*z^-1 + a2*z^-2)`.
In direct form, subtract `a1*y[n-1]` and `a2*y[n-2]`. The reference uses the
equivalent transposed direct form II. The ITU publishes these coefficients
for 48 kHz. Other rates need separate coefficients with verified response.

| Stage | `b0` | `b1` | `b2` | `a1` | `a2` |
| --- | ---: | ---: | ---: | ---: | ---: |
| Shelf | 1.53512485958697 | −2.69169618940638 | 1.19839281085285 | −1.69065929318241 | 0.73248077421585 |
| RLB | 1.0 | −2.0 | 1.0 | −1.99004745483398 | 0.99007225036621 |

For a window of `N` frames, use `P = sum_i(G_i * sum_n(y_i[n]^2) / N)`.
Convert with `L(P) = -0.691 + 10*log10(P)`. The reference stores `sqrt(P)`
and computes `-0.691 + 20*log10(sqrt(P))`. Weighting the filtered amplitude
by `sqrt(G_i)` gives the specified power weight. Channel polarities and
cross-channel phase do not change the sum of their separate powers.

| Quantity | Window at 48 kHz | Grid relative to the epoch start |
| --- | --- | --- |
| M | 19,200 frames | First complete window, then every readout hop |
| S | 144,000 frames | First complete window, then every readout hop |
| I gate input | 19,200 frames | First complete block, then every 4,800 frames |

Use rectangular windows without additional attack or release smoothing.
The readout hop defaults to 480 samples (10 ms) for M and S. It is adjustable
in multiples of 480 samples. The fixed I grid is independent of that setting.
For M/S maxima, check time alignment as well as the window length. A 100 ms
readout can miss the maximum of an offset 400 ms burst in Tech 3341 case 13.

For I, keep complete block powers `P_j` above `L^-1(-70)`. Compute their
energy mean `P_abs`. Keep powers above both `L^-1(-70)` and `P_abs / 10`.
Convert the new energy mean to LUFS. In the square-root representation the
relative threshold is `sqrt(P_abs) / sqrt(10)`. Compare unrounded values
strictly with `>`. Gate membership uses the precision policy below; rounded
RMS thresholds and formatted LUFS readings do not decide membership.
With no complete blocks or an empty absolute gate, there is no final mean.
Store block history so new material can change the relative gate and which
earlier blocks pass it.

## Reference API and numerical behavior

[reference_program_loudness.py](../scripts/reference_program_loudness.py) runs
with Python 3.9+ and its standard library. It takes normalized `int`/`float`
samples in equal, nonempty lists or tuples and has no file or network side
effects. Put the `scripts` directory on the Python import path to run this
example.

```python
import math
from reference_program_loudness import LoudnessConfig, ProgramLoudnessStream

config = LoudnessConfig(48000, ("MONO",), "decoded programme PCM")
meter = ProgramLoudnessStream(config, epoch_id="programme-1", start_sample=0)
pcm = [0.1 * math.sin(2 * math.pi * (n % 48) / 48) for n in range(19200)]
readings = meter.push(0, [pcm], epoch_id="programme-1")
assert len(readings["momentary"]) == 1 and not readings["short_term"]
print(meter.integrated()["gating"].integrated_lufs)  # about -23 LUFS
```

`push` returns only new windows, with their absolute `[start_sample,
end_sample_exclusive)` bounds, and the immutable input config and epoch.
Before the first full M or S window the corresponding series is empty.
Complete zero-power M/S windows read `-inf`. Finite under-gate levels remain
finite. `integrated()` returns the received span, the end of the last complete
gating block (or `None`), and a gating result with the absolute and final gate
survivor counts. Interpret the status as follows.

| I status | Meaning | `integrated_lufs` |
| --- | --- | --- |
| `insufficient_data` | No complete block | `None` |
| `silence` | Every complete block has zero measured weighted power | `None` |
| `below_absolute_gate` | Some measured power, no block strictly above −70 LUFS | `None` |
| `ok` | Gate survivors give a programme reading | Finite LUFS |

`gate_block_rms` makes the complete block roots available in chronological
order for diagnostics. Preserve the gate status when exporting a number to a
screen or a format that cannot encode infinity. A UI can choose its own floor.

Send only contiguous frames with the same epoch and config. A noncontiguous
start, wrong epoch, malformed input or nonfinite sample/arithmetic raises
`ValueError` before any part of that push becomes visible to the caller.
`reset_epoch` takes a new ID, sample origin, and optional new config. It resets
the filters, pending window samples and gate history. The caller validates
upstream format, layout and tap metadata before providing PCM. The reference
has no live transport or pause control. A pause with a stopped source cursor
can preserve state. A source jump needs a new epoch. There is no synthetic
pre-roll, post-roll, filter tail or gap fill.

The reference stores 10 ms RMS summaries and uses scaled reductions
with a fresh positive sum for each window. This avoids subtracting an old
loud interval from a large running sum and erasing a much quieter interval.
It also avoids eagerly squaring large or tiny amplitudes. Filter state and
weighted RMS must fit binary64. Overflow rejects the chunk. At subnormal
scales, roundoff in the filters or the RMS can erase a residual. Test the
required numerical range explicitly. The reference is single-caller offline
code. It keeps up to 3 s of window summaries, plus the 10 gate blocks per
second needed to reevaluate I. Querying I scans the history.

### Gate precision policy

`integrate_block_rms` first validates and converts inputs to finite nonnegative
binary64 values. The gate decisions are exact for those **represented roots**
and the published decimal gate constants, not for an unrounded PCM history or
an arbitrary-precision integer before conversion.

- **Absolute:** the published threshold is
  `T = 10**((-70 + 0.691)/20) = 10**(-69309/20000)`.
  It lies strictly between adjacent binary64 roots
  `a = 0x1.670bbcee4aad0p-12` and `b = 0x1.670bbcee4aad1p-12`.
  Thus for any binary64 root `r`, `r > T` is equivalent to `r > a`.
  This is a representation-specific cutoff, not an epsilon or `>=` rule.
  The regression certifies both endpoints by exact integer inequalities:
  for `v = n/d`, compare `n**20000 * 10**69309` with `d**20000`.
  The lower endpoint is strictly below and the upper strictly above, with
  no binary64 number between. No runtime transcendental fallback is needed.
- **Relative:** for the `N` absolute survivors, form each squared root as an
  exact `Fraction` from its binary64 value. A candidate `r_j` passes exactly
  when `10*N*r_j**2 > sum(r_i**2)`. No normalization, square root, logarithm,
  or binary64 power intermediate participates in this decision. Equality
  remains excluded. Python integer arithmetic avoids intermediate range loss.

The scaled reductions, filter recurrence, channel weights, block roots and
LUFS conversions still round in binary64. In particular, `relative_gate_lufs`
is a rounded diagnostic, not the comparator's threshold. This policy does not
make the entire PCM-to-LUFS pipeline exact. High-precision oracle tests use
`Decimal.from_float` at 100 and 160 digits to check the exact input roots;
survivor identities/counts are checked separately from a fixture-specific
5e-12 LU output budget. Tests cover the hostile roots, both error directions,
strict ties and neighbors, exact power-of-two rescaling, seeded nearby cases,
and finite range extremes.

Exact rational comparison adds allocation and integer-arithmetic cost per
historical block. Both memory and query work grow with programme length;
`integrated()` is not a real-time-safe callback. A production meter needs a
separate performance and accuracy contract, including its own verified gate
strategy. No real-time or physical-device certification follows from this code.

## Verification and use cases

Use the [independent fixture ledger](../../../tests/fixtures/AUDIO_PROGRAM_LOUDNESS_OFFICIAL_GOLDENS.md)
for exact source requirements, external test acquisition and evidence limits.
Run the focused unit tests from the repository root.
[Test source](../../../tests/test_audio_program_loudness_reference.py)

```sh
python3 -m unittest discover -s tests -p 'test_audio_program_loudness_reference.py' -v
```

- If a 5.1 mix contains LFE only, expect zero main-channel weighted power.
  Check the map before treating that result as a failed capture.
- If a task asks for clipping risk after gain changes, measure sample peak or
  true peak on the resulting tap. Matching I can leave different peaks.
- If a programme contains long quiet sequences, compare gate survivors before
  and after the sequence. Averaging displayed LUFS can hide how the real gate
  treats silence and newly added loud sections.

These checks establish the exercised 48 kHz measurement behavior. A complete
EBU Mode meter also needs display and live controls, LRA and true peak coverage.
