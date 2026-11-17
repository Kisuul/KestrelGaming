---
name: audio-loudness-range
description: Measure, interpret, or audit EBU Tech 3342 Loudness Range (LRA) in LU for the loudness variation of a programme or segment. Use for gated short-term loudness distributions, R 128 dynamics reports, or LRA meter and percentile verification.
---

# Audio Loudness Range

LRA describes the spread of foreground and medium-level programme loudness.
Use integrated loudness for gain matching, maximum short-term loudness for a
short-form delivery limit that specifies it, and true peak for headroom.
Use crest factor when the question is about peak-to-RMS ratio.

1. Declare the measured tap, programme span, channel labels, full-scale
   reference, rate, and epoch. For PCM, use K-weighted, ungated, rectangular
   3 s short-term loudness windows. Keep the same filter state across
   contiguous chunks and start a fresh epoch at a seek or change in tap,
   format, rate, or layout. Reuse [programme loudness](../audio-program-loudness/SKILL.md).
2. Sample the short-term series at 10 Hz or faster. Use one constant hop from
   the programme origin. For the 48 kHz reference use 144,000-sample windows
   and a 4,800-sample hop. Collect complete windows continuously. Use one
   documented trailing-silence policy for file comparisons.
3. Keep readings at or above −70 LUFS. Average the powers of those readings
   and find the loudness of that mean. Set the second gate 20 LU below it.
   Keep readings at or above the second gate. Recompute the gates from all
   current windows when the programme grows. Use unrounded short-term
   readings and retain equality at both gates.
4. Sort the surviving levels. Select P10 and P95 with the Tech 3342 §5
   order-statistic rule. For zero-based index use
   `floor((N - 1) * p / 100 + 0.5)` for percentage `p`.
   Report P95 minus P10 in LU. Use integer index arithmetic to preserve
   half-up ties. Report a missing value when there is no admitted window.
5. Mark a defined reading as provisional during the first 60 s of the
   measurement. Treat short clips, isolated utterances, and silence-heavy
   programmes with care. A constant programme can have a valid 0 LU range.
   Report the source span, analysis padding, window cadence, gate counts,
   percentile endpoints, and duration flag with the result.
6. For validation, compare to the hash-verified EBU test set and to
   independent gate and percentile vectors. Include neighboring binary64
   values at a gate, gain shifts with the same gate membership, chunk
   partitions, and measurement resets. State the version and tests that
   support the result.

Use the [measurement contract](references/LOUDNESS_RANGE_CONTRACT.md) for the
algorithm, input states, timing, and example. The
[Python reference](scripts/reference_loudness_range.py) accepts a sequence of
short-term readings or processes 48 kHz labelled PCM with Skill #20.
Use the [fixture checker](scripts/check_ebu_lra.py) and
[frozen expectations](../../tests/fixtures/AUDIO_LOUDNESS_RANGE_GOLDENS.md)
for offline comparison. These checks cover the LRA calculation and selected
PCM fixtures. Full EBU Mode requires additional measurements and meter controls.
