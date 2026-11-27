---
schema: 1
id: 2026-11-26-audio-chroma-harmony-implementation-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: Kestrel
created: 2026-11-26
updated: 2026-11-26
sources: "Audio branch at 74298e8d26a74620413aafe9c4ae201f883c9740, merged research PR #54 and tuning PR #63, executed fixed-support PSD and tuning fixtures, and independent triangular and cosine references."
---

# Chroma and harmony skill #41 implementation and review

## Summary

**Task outcome:** COMPLETE

The [skill](../../../../../skills/audio-chroma-harmony/SKILL.md)
teaches a calibrated power fold into twelve classes and a
bounded comparison with 24 triad templates. The reference
preserves power through both interpolation weights and keeps
absolute power with the template ranking. It qualifies
absolute chord labels on a declared or anchored grid and
accepts independent bass evidence for inversion.
[Contract](../../../../../skills/audio-chroma-harmony/references/CHROMA_HARMONY_CONTRACT.md) ·
[Research](2026-11-26-audio-chroma-harmony-research-r01.md) ·
[Tuning handoff](2026-11-26-audio-tuning-analysis-implementation-r01.md)

## Evidence

- Structural validation, 32 local link and anchor checks,
  the whitespace check, and all 1,104 local tests passed.
  The 26 added tests cover the class seam, extreme
  represented power, PSD endpoints, the closed ambiguity
  margin, tuning scope, and independent bass. Eighteen
  deliberate faults failed targeted assertions.
  [Regression checks](../../../../../tests/test_audio_chroma_harmony_reference.py)
- An independent triangular kernel matched 256 exact
  folds and 768 transpositions with no mass loss. NumPy
  2.3.5 matched all 6,144 squared scores within
  $2.8\times10^{-16}$, with the same leading label sets.
  On 32 odd, even, and padded PSD frames, SciPy 1.17.0
  and the 65-digit mpmath 1.3.0 fold agreed within
  $4.2\times10^{-17}$ per chroma component. Integrated
  power matched the rectangular mean square within
  $1.2\times10^{-16}$.
- The +55-cent triad ranks C-sharp major on the wrapped
  grid. An explicit one-semitone lift recovers C major.
  The C-major reference and its inversion have identical
  chroma with different bass observations. Three partials
  of one C4 yield a C-major squared score near 0.989.
  [Fixtures](../../../../../tests/fixtures/AUDIO_CHROMA_HARMONY_GOLDENS.md)

## Next action

Have Gauge check the even Nyquist and final odd-bin masses,
the exact B-to-C seam, and both sides of the score margin.
Use the +55-cent fixture to identify a relative label before
resolving its semitone representative. Compare root and
first inversion with and without the bass observation.
Repeat with late tuning or bass and inspect the readiness
and evidence delivery boundaries.

Evaluate on labeled audio to set field thresholds. Use
qualified bass annotations for inversion evaluation and
separate timing checks for any beat-synchronous extension.

## Revisit when

The weight ordinate, time aperture, tuning scope, chord
vocabulary, bass qualification, or score policy changes.
