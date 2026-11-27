---
name: audio-tuning-analysis
description: Estimate a shared tuning offset from qualified pitches and measure signed cents for a known note. Use for A4 references, tuning drift, octave or semitone errors, stable-note weighting, partial bias, clock calibration, or tuning before chroma.
---

# Audio tuning analysis

1. **Declare the pitch target.** Set the temperament and A4
   reference. Keep known-note errors unwrapped. Use a 100-cent
   circle to estimate a shared offset from unlabeled 12-TET pitches.
   [Pitch quantities](references/TUNING_ANALYSIS_CONTRACT.md#pitch-quantities)
2. **Qualify observations.** Use stable voiced fundamentals from
   the declared tap. Preserve frame support and note event IDs.
   Give each stable note one vote by default. If using partials,
   check harmonic assignment before pooling their evidence.
   [Evidence and weights](references/TUNING_ANALYSIS_CONTRACT.md#evidence-and-weights) ·
   [Pitch tracking](../audio-pitch-tracking/SKILL.md)
3. **Estimate on the circle.** Retain the residues, weights, and
   resultant length. Check the seam on both sides of 50 cents.
   Require evidence for a direction. Compare groups and spans if
   several offsets fit the recording.
   [Circular estimate](references/TUNING_ANALYSIS_CONTRACT.md#circular-estimate) ·
   [Offline reference](scripts/reference_tuning_analysis.py)
4. **Check the clock.** Verify the sample rate used to convert
   periods to hertz. Keep the calibration source and affected
   span. Compare against a known-frequency observation when a
   common offset could come from the clock.
   [Clock and coverage](references/TUNING_ANALYSIS_CONTRACT.md#clock-and-coverage)
5. **Verify and hand off.** Replay the seam, opposite directions,
   and repeated-note fixtures. Report the reference, validity,
   evidence, and scope. Use the offset once before chroma and use
   labels or a prior to anchor the semitone when needed.
   [Use and verify](references/TUNING_ANALYSIS_CONTRACT.md#use-and-verify) ·
   [Fixtures](../../tests/fixtures/AUDIO_TUNING_ANALYSIS_GOLDENS.md)
