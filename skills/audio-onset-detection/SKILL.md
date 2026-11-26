---
name: audio-onset-detection
description: Detect audio onsets from positive spectral flux and weighted RMS rise. Use for transient timing, missed attacks, false peaks from pitch motion, peak readiness, or a sample-clocked novelty curve for beat tracking.
---

# Audio onset detection

1. **Define the event.** Specify what counts as a new attack. Decide how
   to label pitch changes, releases, and overlapping notes. For a digital
   test, record the first active sample. For music, state how listeners
   mark the event.
2. **Bind the input to its clock.** Record the tap, channel or mix, units,
   epoch, and exact rate. Use complete frames on a fixed window and hop.
   After a gap or seek, start a new epoch and clear all detector history.
   [Frame contract](references/ONSET_DETECTION_CONTRACT.md#frames-and-clock)
3. **Measure two kinds of change.** Start with positive peak-amplitude
   flux on matching bins. Compare it with positive weighted RMS rise on
   the same frames. Keep warm-up scores unavailable. Preserve both curves
   and the bins that contribute to flux.
   [Novelty calculation](references/ONSET_DETECTION_CONTRACT.md#novelty)
4. **Check the missed and extra events.** If pitch motion gives extra
   peaks, compare with a frequency-neighbor filter. Test a weak attack
   beside a held tone before using the filter. If an expected event
   disappears in a mix, inspect the input channels.
   [Diagnosis table](references/ONSET_DETECTION_CONTRACT.md#diagnose-errors)
5. **Pick and time the peak.** Require the full left flank, right flank,
   and trailing background. Record the peak center, event estimate, and
   earliest ready boundary. Record the observed release boundary when
   available. Keep a capture-end peak pending until its right flank exists.
   [Peak rules](references/ONSET_DETECTION_CONTRACT.md#peak-selection-and-readiness)
6. **Verify the operating point.** Check an impulse, a gradual attack,
   a quiet neighbor, and two close events. Match labels and detections
   one-to-one within a stated tolerance. Tune on separate audio from the
   final evaluation. Keep the continuous novelty curve for beat tracking.
   [Scoring](references/ONSET_DETECTION_CONTRACT.md#evaluate-the-detector) ·
   [Fixtures](../../tests/fixtures/AUDIO_ONSET_DETECTION_GOLDENS.md)
