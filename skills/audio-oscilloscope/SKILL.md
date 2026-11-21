---
name: audio-oscilloscope
description: Capture or audit audio waveforms on a sample clock and preserve recorded peaks in a display. Use when a scope loses a transient, shows a channel mismatch, or shifts a trace after callback splits, gaps, or seeks.
---

# Audio oscilloscope

1. **Trace the signal to its tap.** Identify the clock domain, epoch, sample
   rate, amplitude units, and channel order. Check whether the tap exposes
   separate channels or a mix. Compare the raw channels before interpreting
   a flat stereo display.
   [Channel routing](../audio-channel-mapping/SKILL.md)
2. **Choose the capture interval.** Set the window length and hop in sample
   frames. Start from the declared epoch origin and publish only complete
   windows. Keep the same integer bounds for every channel. Report a gap
   or overlap at the expected and observed sample positions. Use a fresh
   epoch after a discontinuity.
   [Timebase](../audio-timebase-sync/SKILL.md) · [Capture contract](references/OSCILLOSCOPE_CONTRACT.md#capture-on-the-sample-clock)
3. **Check history before changing the display.** Follow the ingest cursor
   through every capture end in the block. Take the snapshot while its
   samples remain in history. A render pass can skip or redraw a snapshot
   while capture continues.
   [Stream buffering](../audio-stream-buffering/SKILL.md)
4. **Project the measured samples.** When several samples share a column,
   retain the signed minimum and maximum for that column and channel. Keep
   the original sample positions at high zoom. Treat a connecting line as
   display interpolation. Use a resampling method when the output needs a
   new audio sample grid.
   [Display projection](references/OSCILLOSCOPE_CONTRACT.md#display-projection)
5. **Locate a lost transient.** Probe the tap with a known short pulse.
   Check its sample index in the raw capture, then check the extrema in
   its column. Replay with different callback splits and display widths.
   If the raw capture has the pulse, inspect the projection and render path.
   If the raw capture loses it, inspect the tap, window, and continuity.
   [Frozen fixtures](../../tests/fixtures/AUDIO_OSCILLOSCOPE_GOLDENS.md)

Report the tap, channel IDs, units, clock and epoch, exact window bounds,
hop, and projection mode. Use the [offline reference](scripts/reference_oscilloscope.py)
to check sample ownership and window timing. For device latency or
presentation cadence, measure the target system.
