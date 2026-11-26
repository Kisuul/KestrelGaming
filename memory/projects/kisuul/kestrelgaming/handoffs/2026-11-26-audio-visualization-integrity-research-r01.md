---
schema: 1
id: 2026-11-26-audio-visualization-integrity-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-26
updated: 2026-11-26
sources: "Audio branch a435c790546b7aefc8ba35ba18be1d7c235f916f; Jugel et al. (2014), M4; Kestrel waveform and STFT contracts; executed gap, excursion, and density aggregation checks."
---

# Skill 70 research for visualization integrity

## Summary

**Task outcome:** COMPLETE

Keep the meaning, time support, and units of an analysis
value through the display projection. Mark unavailable
data at its original coordinates. A stride can miss both
extremes of a waveform. A mean of logarithmic density
values can misstate the power in a band.
[Oscilloscope display projection](../../../../../skills/audio-oscilloscope/references/OSCILLOSCOPE_CONTRACT.md#display-projection) ·
[STFT visualization checklist](../../../../../skills/audio-spectrogram-waterfall/references/STFT_WATERFALL_CONTRACT.md#visualization-integrity-checklist)

## Evidence

### Keep support and display geometry traceable

Record the source tap, channels, sample clock, analysis
support, statistic, unit and reference. Map display
columns to half-open intervals in that clock. A pixel
may summarize several samples or frames. Put a cursor,
peak marker, or exported event at its recorded coordinate
when the exact time is known. Report the displayed interval
when only an aggregate is available. Keep analytical
values and their display coordinates available to the
same audit.
[Timebase](../../../../../skills/audio-timebase-sync/references/TIMEBASE_CONTRACT.md) ·
[Analysis provenance](../../../../../skills/audio-analysis-provenance/references/PROVENANCE_CONTRACT.md)

For a waveform envelope, reduce each bucket to its minimum
and maximum over valid samples. Retain counts and the
subspans of valid data. For a connected approximation,
keep the original times of extrema and the first and
last points of each contiguous run. Render those
points in time order and terminate the trace at a gap.
M4 studies line rasterization with specified assumptions.
Verify pixel equivalence for the renderer and geometry
used if the application claims it. A band of min and max
values communicates bounds for the bucket.
[Jugel et al. (2014), M4](https://www.vldb.org/pvldb/vol7/p797-jugel.pdf) ·
[Dropout and coverage](2026-11-26-audio-dropout-detection-research-r01.md)

For a band built from disjoint cells of piecewise constant
power spectral density $S_i$, integrate $\sum_i S_i\Delta f_i$
with widths $\Delta f_i$ equal to the intersection with
the band. Divide by the summed width for a mean density
over that covered width. Convert the chosen statistic to
dB after forming it, with a reference in the same units.
For partial coverage, state the denominator and validity
policy. Preserve the support of overlapping analysis
frames when deriving a time average.
[STFT spectral ordinate](../../../../../skills/audio-spectrogram-waterfall/references/STFT_WATERFALL_CONTRACT.md#spectral-ordinate-and-visualization) ·
[Noise power and PSD](2026-11-26-audio-noise-snr-sinad-research-r01.md)

### Executed checks and portable fixtures

Use ticks 0 through 15. Tick 2 has value 1 and
tick 9 has value −0.5. Mark ticks 4 through 7 and
13 through 14 unavailable. Every other tick is valid
at zero. Use four buckets of width four.

| Bucket | Valid count | Minimum and maximum | Valid runs |
| --- | --- | --- | --- |
| `[0,4)` | 4 | 0, 1 | `[0,4)` |
| `[4,8)` | 0 | Unavailable | None |
| `[8,12)` | 4 | −0.5, 0 | `[8,12)` |
| `[12,16)` | 2 | 0, 0 | `[12,13)` and `[15,16)` |

Sampling just the first tick of each bucket returns
`[0, unavailable, 0, 0]`. It misses both excursions
and the internal gap in the final bucket. At this
resolution the trace needs a gap or coverage indication
even when the boundary of the gap is smaller than a pixel.

For a second check, take adjacent cells of widths 1
and 3 Hz, with densities 1 and 0.01 V²/Hz. They
integrate to 1.03 V². Their width-weighted mean is
0.2575 V²/Hz, or −5.8922 dB relative to 1 V²/Hz.
Taking the same weighted mean of the two dB ordinates
gives −15 dB. That calculation gives the log of a
geometric mean. The policy here displays the arithmetic
mean of density.

## Next action

Give Gauge the waveform and band probes at multiple
viewport widths, with gaps at both the boundary and
interior of a bucket. Verify displayed positions,
units, per-bucket coverage and exported values.
When using a line renderer, test the drawn paths
against a raw-point reference under the same geometry.

## Revisit when

The viewport, renderer, decimation, axis, rebinning
model, or validity policy changes.
