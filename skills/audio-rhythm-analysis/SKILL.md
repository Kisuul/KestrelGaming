---
name: audio-rhythm-analysis
description: Measure inter-onset intervals, beat-relative event positions, subdivision residuals, and swing from sample-clocked events and a beat grid. Use to analyze groove, syncopation, tempo-dependent timing, ambiguous subdivisions, or rhythm alignment.
---

# Audio rhythm analysis

1. **Define the rhythm target.** Name the intended pulse, voices, and
   accepted onset events. Label offbeats when measuring swing. For
   bar position or meter, collect bar-level evidence.
2. **Preserve timing and support.** Put events and beat anchors on
   one declared clock. Keep the epoch, tap, voice, source positions,
   and capture intervals. Measure adjacent onsets within each voice.
   Preserve distinct simultaneous observations.
   [Clock and intervals](references/RHYTHM_ANALYSIS_CONTRACT.md#clock-and-inter-onset-intervals)
3. **Use local beat anchors.** Map each event between consecutive
   anchors in one qualified beat segment. Use the actual beat length.
   Record inferred anchors and the data boundary used for the result.
   Leave phase unavailable across gaps.
   [Beat coordinates](references/RHYTHM_ANALYSIS_CONTRACT.md#beat-coordinates-and-readiness) ·
   [Beat tracking](../audio-beat-tracking/SKILL.md)
4. **Compare subdivision grids.** Keep signed residuals, exact ties,
   and the number of distinct beats that support each slot. Use the
   same eligible events and tolerance for each candidate. Check the
   evidence for extra slots on a denser grid.
   [Subdivision evidence](references/RHYTHM_ANALYSIS_CONTRACT.md#subdivision-evidence)
5. **Check the interpretation.** Test straight, swung, and syncopated
   timing with known anchors. Compare periodicity and phase evidence
   when several rates fit. Report the voice, local tempo, timing
   errors, and uncertain cases.
   [Swing and periodicity](references/RHYTHM_ANALYSIS_CONTRACT.md#swing-and-periodicity) ·
   [Fixtures](../../tests/fixtures/AUDIO_RHYTHM_ANALYSIS_GOLDENS.md)
