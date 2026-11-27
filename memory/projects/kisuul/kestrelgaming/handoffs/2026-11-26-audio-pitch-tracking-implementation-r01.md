---
schema: 1
id: 2026-11-26-audio-pitch-tracking-implementation-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: Kestrel
created: 2026-11-26
updated: 2026-11-26
sources: "Audio branch at 5373156a58f9fa4dd01eeaec65da12f9b945fd35, merged research PR #54, YIN and pYIN papers, and executed difference and clock checks."
---

# Pitch tracking skill #39 implementation and review

## Summary

**Task outcome:** COMPLETE

The [skill](../../../../../skills/audio-pitch-tracking/SKILL.md)
teaches fixed-support pitch candidates, guarded interpolation,
voicing, and timing. The reference keeps raw lag differences and
normalized depths. It records the fitted period of each trough
and selects the first eligible candidate on a complete frame.
AC power, threshold evidence, and input availability have
separate roles in the decision.
[Contract](../../../../../skills/audio-pitch-tracking/references/PITCH_TRACKING_CONTRACT.md) ·
[Research](2026-11-26-audio-pitch-tracking-research-r01.md)

## Evidence

- Structural validation, 33 Markdown link and anchor checks, the
  whitespace check, and all 1,026 local repository tests passed.
  The new suite contains 28 tests. Sixteen deliberate faults
  failed targeted assertions. The focused tests cover fixed pair count,
  both guard seeds, a fit outside the band, exact threshold
  equality, missing input, and clock replay.
  [Regression checks](../../../../../tests/test_audio_pitch_tracking_reference.py)
- Across 538 positive lags, absolute differences stayed below
  $2.85\times10^{-14}$ against direct binary64 differences and
  $5.69\times10^{-14}$ against the padded FFT identity. Four
  zero-lag controls passed. Both exact curves agreed at 2,214
  lags across 128 additional frames. The floating-point checks
  used NumPy 2.3.5 and SciPy 1.17.0.
- On the small modulation with DC, the input still carries a
  difference of up to $1.67\times10^{-15}$ squared PCM. The
  unshifted FFT identity returned negative values at 241 positive
  lags. Subtracting a common sample before the FFT reduced the
  largest absolute error from about $5.13\times10^{-13}$ to
  $5.33\times10^{-30}$ in this run.
  [Fixture definitions](../../../../../tests/fixtures/AUDIO_PITCH_TRACKING_GOLDENS.md)
- The 50 Hz short-support fixture chose 84.47736 Hz on 1,024
  samples. The wider profile recovered about 50 Hz on 2,881
  samples. Weakening the 1,200 Hz component of the missing
  fundamental fixture admitted the 800 Hz candidate while
  retaining the exact 400 Hz repetition.

## Next action

Give Gauge the two range-edge seeds and the retained out-of-band
fit. Verify the exact lag difference at the last guard. Compare
the octave choices at both weak-harmonic levels and at threshold
equality. Compare complete silence with missing samples and
replay the same PCM under three delivery partitions. Ask which
clock boundary each result uses.

Use independent labeled recordings for voicing and octave-error
evaluation. A sequence model needs a declared transition rule
and commitment delay. Measure execution time in the intended
host if the estimator will run live.

## Revisit when

The channel mix, pitch band, comparison width, level gate,
refinement, label policy, or commitment model changes.
