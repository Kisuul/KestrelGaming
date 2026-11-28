---
name: audio-clipping-detection
description: Detect and audit integer PCM rail contacts, rail plateaus, and floating-point reference exceedances. Use when a peak flattens, a clip indicator fires, or clipping must be located across taps or callback boundaries.
---

# Audio clipping detection

1. **Identify the tap and numeric domain.** Record channel IDs, clock,
   epoch, sample rate, units, and observed sample span. For integer PCM,
   unpack the valid codes and use the two signed rails. For float PCM,
   declare the reference levels and any verified clamp.
   [Input contract](references/CLIPPING_DETECTION_CONTRACT.md#inputs-and-profiles)
2. **Measure each channel at the sample rate.** Count both integer rail
   contacts. Report isolated contacts and same-rail runs. In float PCM,
   count equality separately from strict exceedance. Report the polarity,
   span, and extreme of each excess run. Keep the open run across
   contiguous callbacks.
   [Run contract](references/CLIPPING_DETECTION_CONTRACT.md#run-evidence)
3. **Record when the evidence is available.** Use exact sample indices.
   Report the first frontier that meets the plateau rule and the later
   frontier that confirms the end. Reject gaps and overlaps before
   updating state. Close open runs at an explicit boundary and retain
   their observed spans.
   [Continuity](references/CLIPPING_DETECTION_CONTRACT.md#continuity-and-boundaries)
4. **Check the suspected stage.** Compare aligned captures or the
   verified converter input, output, and saturation counts. Use a
   controlled stimulus to check soft saturation. Use a declared
   reconstruction to check intersample peaks. Report the observation
   and the evidence for its cause.
   [Attribution](references/CLIPPING_DETECTION_CONTRACT.md#diagnose-the-stage)

Use the [offline reference](scripts/reference_clipping_detection.py) and
[frozen fixtures](../../tests/fixtures/AUDIO_CLIPPING_DETECTION_GOLDENS.md)
to verify both rails, callback partitions, and a gap inside a candidate.
