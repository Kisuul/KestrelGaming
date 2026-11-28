---
name: audio-dropout-detection
description: Diagnose missing audio frames, underrun fill, packet loss concealment, and unexpected quiet intervals. Use when callbacks skip positions or playback is quiet, repeated, or continuous despite suspected source loss.
---

# Audio dropout detection

1. **Identify the timing evidence.** Record the tap, source and
   presentation clocks, epoch, channel IDs, rate, and observed span.
   Use trusted source positions to locate missing frames. Check the
   delivery policy before confirming a gap. Measure actual overlap
   when a block starts early.
   [Source coverage](references/DROPOUT_DETECTION_CONTRACT.md#source-coverage)
2. **Trace the playout.** Record original, replacement, and absent
   intervals at their presentation positions. Keep the replacement
   method with its span. Compare the two clocks through a verified
   mapping. Use host flags and counter changes at their available
   time resolution.
   [Playout provenance](references/DROPOUT_DETECTION_CONTRACT.md#playout-provenance)
3. **Qualify waveform candidates.** Compare quiet windows with
   adjacent active windows on the same channel. State the units,
   window grid, thresholds, and minimum duration. Wait for the
   complete following window. Preserve incomplete observations at
   a gap or capture boundary.
   [Quiet-window evidence](references/DROPOUT_DETECTION_CONTRACT.md#quiet-window-evidence)
4. **Check the suspected cause.** Compare aligned taps, delivery
   records, and known replacement policy. Test intentional quiet
   and repeated material as controls. Report the evidence, its
   support, and any uncertainty in the timing or cause.
   [Frozen fixtures](../../tests/fixtures/AUDIO_DROPOUT_DETECTION_GOLDENS.md)

Use the [offline reference](scripts/reference_dropout_detection.py)
to check ordered coverage, playout span accounting, and quiet
candidates. Preserve exact frame positions in the report.
