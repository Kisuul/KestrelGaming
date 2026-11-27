---
name: audio-chroma-harmony
description: Fold calibrated spectral power into twelve pitch classes and compare major and minor triads. Use for chroma, tuning before chord analysis, octave folding, ambiguous chords, inversions, or duration-weighted chord evaluation.
---

# Audio chroma and harmony

1. **Calibrate the observations.** Declare the tap, frame, rate,
   units, and frequency band. Convert each complete one-sided
   PSD bin to power with the bin spacing. Exclude DC and keep
   the admitted and excluded power.
   [Power and support](references/CHROMA_HARMONY_CONTRACT.md#power-and-support)
2. **Fold pitch on the declared grid.** Apply the tuning once.
   Split power between adjacent classes, including B and C.
   Keep the raw masses. For absolute chord labels, declare a
   reference or resolve the tuning estimate's semitone choice.
   [Tuned pitch classes](references/CHROMA_HARMONY_CONTRACT.md#tuned-pitch-classes) ·
   [Tuning analysis](../audio-tuning-analysis/SKILL.md)
3. **Rank chord evidence.** Check absolute power first. Score
   all major and minor triads on the same vector. Keep exact
   ties and candidates within the declared margin. Qualify
   the bass separately before reporting an inversion.
   [Chord scores and decisions](references/CHROMA_HARMONY_CONTRACT.md#chord-scores-and-decisions) ·
   [Reference](scripts/reference_chroma_harmony.py)
4. **Check the evidence and timing.** Compare partials with
   known fundamentals. Test two close notes with the actual
   window and level ratio. Keep the frame center, readiness,
   and observed data delivery. Evaluate chord labels over
   common intervals with a stated vocabulary and coverage.
   [Time and evaluation](references/CHROMA_HARMONY_CONTRACT.md#time-and-evaluation) ·
   [Fixtures](../../tests/fixtures/AUDIO_CHROMA_HARMONY_GOLDENS.md)
