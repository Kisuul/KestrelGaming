# Loudness Range contract

[Standards](#standards-and-scope) · [Gates and percentiles](#gates-and-percentiles)
· [Timing and results](#timing-and-result-states) · [Example](#example)

## Standards and scope

Use EBU Tech 3342 v4 (November 2023), §§3–5 for LRA, and EBU Tech 3341 v4,
§§2.2 and 2.4 for ungated 3 s windows and the 60 s indication. Use ITU-R
BS.1770-5 Annex 1 for K-weighting and channel energy. Apply the relevant
delivery policy separately. [Tech 3342](https://tech.ebu.ch/publications/tech3342)
· [Tech 3341](https://tech.ebu.ch/publications/tech3341)
· [BS.1770-5](https://www.itu.int/rec/R-REC-BS.1770/en)
· [EBU R 128](https://tech.ebu.ch/publications/r128)

The LRA statistic accepts uniformly sampled ungated short-term loudness.
The PCM adapter uses the Skill #20 reference at 48 kHz with normalized
planar PCM, explicit mono, stereo, 5.0 or 5.1 labels, and LFE exclusion. See
the [programme loudness contract](../../audio-program-loudness/references/PROGRAM_LOUDNESS_CONTRACT.md).
The educational reference keeps a programme history and computes LRA on
demand. Full EBU Mode validation extends to concurrent I/LRA controls,
other measurements and display behavior.

## Gates and percentiles

1. Keep binary64 short-term levels `L >= -70` LUFS. For `N > 0` admitted
   readings, let `M = max(L)` and `p_i = 10**((L_i - M)/10)`.
2. A candidate stays when `100 * N * p_i >= sum(p_j)`. The sum uses all
   absolute-gated powers. The factor of 100 represents a drop of 20 LU
   from the level of the power mean. The loudest reading always stays.
   Use inclusive comparisons as in Tech 3342 §5. The strict −10 LU relative
   gate for integrated loudness applies to a different measurement.
3. Sort the final population. For percentile `p` and survivor count `K`,
   use zero-based index `(p * (K - 1) + 50) // 100`. Keep duplicate
   observations. Use the selected P10 and P95 readings without interpolation.
   Compute LRA as `P95 - P10` in LU.

The reference treats the supplied binary64 level as the exact gate input.
The PCM filter, RMS, and conversion to LUFS have their usual rounding.
The reference admits −70 LUFS exactly and discards the preceding binary64
value. It normalizes the relative-gate powers at the peak to avoid
overflow. It uses outward-rounded Decimal operations to bound normalized
powers, including adjacent representable bounds for correctly rounded
`ln` and `exp`. It only uses a bound to decide membership when the bound
proves the outcome. [Python Decimal arithmetic](https://docs.python.org/3/library/decimal.html)

For an exact relative tie, all powers divided by the candidate power must
have integer exponents of ten. To see this, write the rational exponent
differences over a common denominator `D`. The minimal polynomial of
`10**(1/D)` is `x**D - 10` by Eisenstein's criterion at 2. Powers with
different fractional exponents are therefore linearly independent over
the rationals. Positive terms outside the candidate's fractional class
cannot cancel. The reference compares integer-decade counts using exact
decimal carries and retains a tie. It increases precision on other
overlapping bounds. At 1,024 decimal digits an unresolved comparison raises
`ArithmeticError`. The reported relative threshold is a rounded diagnostic.
Use the survivor count for boundary verification.

## Timing and result states

- The first complete PCM window is `[origin, origin + 144000)`. After that,
  each window advances by 4,800 samples relative to the origin. Callback
  boundaries do not change the grid. Keep sample coordinates as integers.
- While the stream runs, measure through the latest complete window.
  For a nonempty file, call `finish()` once after the last source frame. It
  feeds 72,000 zero frames through the same filter state. This implements
  Tech 3342 §5's 1.5 s recommendation. It uses no leading padding and leaves
  a final partial hop outside the distribution. An empty file stays empty.
- The report gives separate exclusive end samples for source PCM and
  analysis PCM, and the end of the last complete window. A window can include
  the analysis silence. A nonempty clip under 3 s can first yield a value
  during padding. For a file with less than 1.5 s of source PCM, even the
  padded history is too short for a full window.
- Use actual source frames since the latest reset for the 60 s indication.
  EOF padding does not advance that duration. Finalized reports for shorter
  files can still be provisional. At 60 s the indication expires. Interpret
  the result in light of the programme and its duration.
- Use fresh epoch IDs after seeks, input changes, or resets. Pass contiguous
  source data only. A failed PCM push leaves the prior measurement intact.
  After EOF, call `reset_epoch()` before adding source PCM. Multiple calls to
  `finish()` add no extra padding.

| Result status | Meaning |
| --- | --- |
| `insufficient_data` | There are no complete short-term observations. |
| `silence` | All the observations are negative infinity, the upstream zero-energy sentinel. |
| `below_absolute_gate` | At least one observation is finite and every observation is below −70 LUFS. |
| `ok` | The gates define a population and the endpoints give an LRA in LU. Use `provisional` from the timed report when displaying this value. |

`calculate_lra()` takes a sequence of numeric short-term readings in LUFS and
checks each value. It accepts negative infinity for zero energy and rejects
NaN, positive infinity, boolean values, and text. The caller supplies readings
from one uniform analysis cadence and handles epoch and duration metadata.
Undefined results have `None` for LRA, percentiles and the relative threshold.

## Example

Run from the KestrelGaming root on Python 3.9 or later. Both skill directories
must be present. Use the PCM adapter when the source is PCM.

```bash
PYTHONPATH=skills/audio-loudness-range/scripts python3 - <<'PY'
from reference_loudness_range import LoudnessConfig, LoudnessRangeStream, calculate_lra

assert calculate_lra([-25.0, -22.0, -21.0]).lra_lu == 4.0

config = LoudnessConfig(48_000, ("L", "R"), "delivery")
meter = LoudnessRangeStream(config, epoch_id="file-1", start_sample=0)
left = right = [0.0] * 144_000
meter.push(0, [left, right], epoch_id="file-1")
report = meter.finish()
assert report.result.status == "silence"
assert report.result.lra_lu is None
assert report.programme_end_sample_exclusive == 144_000
assert report.analysis_end_sample_exclusive == 216_000
PY

python3 skills/audio-loudness-range/scripts/check_ebu_lra.py /path/to/ebu-loudness-test-setv05.zip
python3 -m unittest discover -s tests -p 'test_audio_loudness_range*.py' -v
```

Compare the actual error with the tolerance for each original case. Use the
[fixture ledger](../../../tests/fixtures/AUDIO_LOUDNESS_RANGE_GOLDENS.md) to
check archive identity, cases, and arithmetic expectations. For other
implementations, align the measurement interval, analysis cadence, EOF policy,
and units before comparing outputs.
