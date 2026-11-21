---
name: audio-scope-triggering
description: Design or audit edge-triggered PCM captures on a sample clock. Use for missing or false triggers, hysteresis, holdoff, pretrigger and posttrigger history, single-shot capture, and shifts at callback boundaries.
---

# Audio scope triggering

1. **Trace the trigger to its PCM tap.** Record the channel ID, clock, epoch,
   rate, units, direction, and level. A scope can show a different channel.
   Compare the trigger samples before interpreting the displayed trace.
   [Aligned waveform capture](../audio-oscilloscope/SKILL.md)
2. **Check arming and the crossing pair.** Apply hysteresis on the source
   side of the level. Keep the previous sample and the arm latch across
   callbacks. Use the right sample as the detection index. Keep the left
   index and interpolation fraction separate.
   [Detection rules](references/SCOPE_TRIGGERING_CONTRACT.md#detect-on-the-sample-clock)
3. **Check acquisition eligibility.** For a qualified edge, check shot
   permission, holdoff release, a pending capture, and available prehistory.
   Record the disposition at the crossing. A later acceptance requires a
   fresh qualified edge.
   [Decision order](references/SCOPE_TRIGGERING_CONTRACT.md#decide-and-complete)
4. **Check the complete span.** Include the detection sample and the
   declared numbers of samples before and after it. Publish when the
   exclusive end is available on the sample clock. Validate whole blocks
   before ingest. After a seek or discontinuity, start a fresh epoch.
   [Timebase](../audio-timebase-sync/SKILL.md)
5. **Replay a known edge.** Split the same PCM just before the crossing,
   at holdoff release, and in the posttrigger tail. Compare raw crossing
   pairs, decisions, and complete spans in sample order. Use the
   [offline reference](scripts/reference_scope_triggering.py) and
   [frozen fixtures](../../tests/fixtures/AUDIO_SCOPE_TRIGGERING_GOLDENS.md).

Report the trigger settings, epoch, exact detection index, interpolation
pair, and capture status. Check auto-mode labels on a live display so
a fallback trace is identified as untriggered.
