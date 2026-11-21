---
name: audio-vectorscope
description: Design or audit a stereo vectorscope from aligned PCM pairs. Use when a stereo trace has the wrong orientation, collapses to a dot, or changes shape with viewport size or display cadence.
---

# Audio vectorscope

1. **Trace the stereo tap.** Record the channel IDs, units, clock, epoch,
   sample rate, and capture bounds. Select two distinct channel IDs.
   Verify they share one sample interval and use the raw PCM at each
   index. Check routing before interpreting a silent or narrow trace.
   [Channel mapping](../audio-channel-mapping/SKILL.md) ·
   [Aligned capture](../audio-oscilloscope/SKILL.md)
2. **Check the axes with known pairs.** Use right minus left on the
   horizontal axis and their sum on the vertical axis. Divide both by
   the square root of two. Check the sign with
   a left-only and a right-only pair. A channel swap reflects the trace
   horizontally. Retain raw DC and amplitude in the measured coordinates.
   [Coordinate contract](references/VECTORSCOPE_CONTRACT.md#measured-coordinates)
3. **Check the view independently.** Use one gain for both axes and
   reverse the vertical sign when screen rows increase downward.
   Compare the coordinates and geometric bounds before pixel rounding.
   Label points above nominal PCM level and points outside the view.
   [Viewport geometry](references/VECTORSCOPE_CONTRACT.md#viewport-geometry)
4. **Locate a missing shape.** Feed a known quadrature tone. Check the
   ordered full-rate points, then the view's point selection and scale.
   For a horizontal trace, test the actual mono fold-down and listen.
   Use known timing and stimulus frequency to investigate channel delay.
   [Frozen fixtures](../../tests/fixtures/AUDIO_VECTORSCOPE_GOLDENS.md)

Report the selected channels, exact support, axis convention, gain,
and any point selection. Use the [offline projector](scripts/reference_vectorscope.py)
with a fixed-hop or completed triggered capture. Measure display timing
and persistence on the target host.
