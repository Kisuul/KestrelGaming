---
schema: 1
id: 2026-11-20-audio-vectorscope-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-20
updated: 2026-11-20
sources: "Insight 2 Sound Field manual, Logic Pro 10.6 MultiMeter documentation, FFmpeg 7.1 vectorscope source, W3C Web Audio section 1.8.5, Kestrel channel mapping, and executed binary64 fixtures on 2026-11-20. PR #29 research baseline 50aeb37ba93816ea6da6c7d99612b065ec521c27."
---

# Audio vectorscope research

## Summary

Planned skill #30 · `audio-vectorscope`

**Task outcome:** COMPLETE

Use a vectorscope to inspect simultaneous sample pairs for a declared stereo tap.
Start with one linear sum/difference plot that preserves pair magnitude. Verify channel
identity, alignment, and display scale before interpreting the trace. The first reference
should produce coordinates from complete, aligned frames. Rendering, persistence and point
selection are consumers of that result.

The [audio curriculum backlog](https://github.com/Kisuul/KestrelGaming/blob/bc94f0562f8fa4eca0d92e9587ede044fb5d9b36/memory/projects/kisuul/kestrelgaming/handoffs/2026-11-17-audio-curriculum-status-r01.md#oscilloscopes-and-phase-8-pending)
places vectorscope after [oscilloscope waveform capture](2026-11-20-audio-oscilloscope-research-r01.md)
and [scope triggering](2026-11-20-audio-scope-triggering-research-r01.md).
The numbering follows that planning order.

## Evidence

### What existing instruments establish

| Source | Observed convention | Engineering consequence |
| --- | --- | --- |
| Tektronix oscilloscope primer | XY mode uses an input signal on the horizontal axis where a time-based scope uses time. | Pair input values at the same sample time. A waveform envelope over time is a different measurement. [Tektronix XY mode](https://www.tek.com/en/documents/primer/oscilloscope-systems-and-controls#horizontal-system-and-controls) |
| Insight 2 Sound Field | Polar Sample and Lissajous plot per-sample points. Polar Level draws rays from detected levels and exposes peak, RMS and envelope options. Its Lissajous guide describes equal channels as vertical. | Establish the input reduction before comparing plots with the same scope label. [Insight 2 Sound Field](https://s3.amazonaws.com/izotopedownloads/docs/insight200/en/print/index.html#sound-field) |
| FFmpeg 7.1 | The Lissajous branch uses a half-difference and half-sum after preprocessing. The XY branch uses the channel values directly, with its own screen signs. The projection uses separate video half extents. | Match channel order, mirror, mode, scale, zoom and aspect before a differential comparison. [FFmpeg 7.1, avf_avectorscope.c, lines 391–414](https://www.ffmpeg.org/doxygen/7.1/avf__avectorscope_8c_source.html#l00391) |
| Logic Pro 10.6 MultiMeter | Auto Gain changes displayed gain. Decay controls how long the trace remains visible. | Carry display gain and persistence as view settings. Obtain level evidence from the measured sample pairs. [Logic Pro Effects, MultiMeter Goniometer](https://cdsassets.apple.com/live/6GJYWVAV/user/ma1925_logic-pro-10-6-effects-user-guide.pdf) |

The proposed mapping below uses a defined sum/difference basis and one geometric screen
scale. This gives an analytical oracle even when another product uses a different view.

### Capture and coordinate contract

1. **Acquire ordered pairs.** Record tap, channel identities, input units and nominal full
   scale, sample rate, epoch, and exact half-open support $[s,s+N)$. Use $L[n],R[n]$ from
   the same frame number. Different callback boundaries may represent the same stream.
   A seek, sample loss, channel-map change, or resampling change needs an explicit
   continuity decision. Reuse the project channel and clock contracts.
   [Channel mapping](../../../../../skills/audio-channel-mapping/references/CHANNEL_MAPPING_CONTRACT.md)
   · [Audio timebase](../../../../../skills/audio-timebase-sync/SKILL.md)
2. **Preserve acquisition identity.** A valid zero stereo frame gives a point at the
   origin. A missing channel or mismatched support is unavailable until an explicit
   channel mapping supplies a pair. Reject malformed, nonfinite or unsupported input before
   changing capture state. Preserve digital headroom supported by the tap. If using a
   browser tap, verify that it can expose two channels with the same sample clock.
   The Web Audio AnalyserNode time-domain result is downmixed to mono.
   [Web Audio §1.8.5](https://www.w3.org/TR/webaudio/#time-domain-down-mixing)
3. **Map one pair at a time.** For positive-right and positive-up mathematical axes, use

   $$
   x=\frac{R-L}{\sqrt 2},\qquad y=\frac{L+R}{\sqrt 2}.
   $$

   This is an orthonormal basis. Kestrel's existing amplitude-normalized mapping
   $M=(L+R)/2$ and $S=(L-R)/2$ yields $x=-\sqrt 2 S$ and $y=\sqrt 2 M$. The inverse is
   $L=(y-x)/\sqrt 2$, $R=(y+x)/\sqrt 2$. The pair identity
   $x^2+y^2=L^2+R^2$ follows by expanding the squares. Swapping $L$ and $R$ reflects
   $x$ and leaves $y$ unchanged. Keep the input units on both axes. Freeze raw DC-coupled
   coordinates first. A centered view should declare its mean-removal interval.
4. **Map coordinates to pixels.** For screen center $(c_x,c_y)$ and down-positive
   pixel rows, use $(p_x,p_y)=(c_x+g x,c_y-g y)$ for one positive gain $g$.
   For a nominal amplitude $A_\mathrm{FS}$ on each channel, the input square maps
   to the diamond $\lvert x\rvert+\lvert y\rvert\le\sqrt 2 A_\mathrm{FS}$.
   Set $g=\min(h_x,h_y)/(\sqrt 2 A_\mathrm{FS})$ for usable geometric half-extents
   $h_x,h_y$. Make pixel rounding and viewport clipping a later step. On a view
   with 320 and 180 units of half-extent and $A_\mathrm{FS}=1$, the nominal vertical
   and horizontal extrema both map 180 units from center. Separate a point outside
   the viewport from a PCM sample over its nominal level. Claims of actual clipping
   need input or waveform evidence.

| Input pair | Expected coordinate at nominal full scale |
| --- | --- |
| $(1,1)$ | $(0,\sqrt 2)$, above center |
| $(1,-1)$ | $(-\sqrt 2,0)$, left of center |
| $(1,0)$ then $(0,1)$ | $(-1/\sqrt 2,1/\sqrt 2)$ then $(1/\sqrt 2,1/\sqrt 2)$ |
| $(0,0)$ | Origin |
| $(1.25,-1.25)$ when the tap permits it | $(-1.25\sqrt 2,0)$ before view clipping |

### Explain a shape from the signal

**Equal-amplitude tones.** Let $L[n]=A\cos\theta_n$ and
$R[n]=A\cos(\theta_n-\phi)$ with $\theta_n=2\pi fn/f_s$. Positive $\phi$ denotes a
right-channel lag in this signal model. Write $\alpha=\theta_n-\phi/2$. Then

$$
x[n]=\sqrt 2 A\sin(\alpha)\sin(\phi/2),\qquad
y[n]=\sqrt 2 A\cos(\alpha)\cos(\phi/2).
$$

The locus has horizontal and vertical semi-axis lengths
$\sqrt 2 A\lvert\sin(\phi/2)\rvert$ and $\sqrt 2 A\lvert\cos(\phi/2)\rvert$,
respectively. Identical channels give a vertical line. Opposite-polarity
copies give a horizontal line. A quarter-cycle offset gives a circle of radius
$A$. Both lag and lead yield that circle. Their time-ordered points travel
in opposite directions under the same axes. At 48 kHz, a delay of 12 samples
corresponds to a quarter cycle at 1 kHz and a half cycle at 2 kHz. Use a known
stimulus and capture timestamps to distinguish actual delay from pairing skew.

**Gain and DC are separate causes.** For $R=L/2$, the plot lies on $y=-3x$ even
though the channels are positively proportional. A common DC offset shifts $y$.
A differential DC offset shifts $x$. Controlled DC and unequal-gain fixtures help
distinguish centering or axis mistakes from a change in channel timing.

**Check mono with the real fold-down.** For an equal-weight stereo average, the
fold-down is $(L+R)/2=y/\sqrt 2$. A horizontal trace for $R=-L$ predicts cancellation
under that fold-down. In a real mix, inspect the actual matrix, check the result
over the relevant time/frequency support, and compare the audio. A width or spread
reading alone cannot identify which bands were affected.

For a useful guard against confusing scope geometry with a correlation meter, let
$E_x=\sum x^2$, $E_y=\sum y^2$, $E_L=\sum L^2$, and $E_R=\sum R^2$ over the same
raw frame. When $E_L,E_R>0$, the uncentered normalized inner product is
$\rho_0=\sum LR/\sqrt{E_LE_R}$. The plot's normalized axis-energy difference is

$$
\frac{E_y-E_x}{E_y+E_x}
=\rho_0\frac{2\sqrt{E_LE_R}}{E_L+E_R}.
$$

The multiplier is one when channel energies match. With $R=L/2$, $\rho_0=1$
and the plotted energy ratio is 0.8. With one silent channel and one nonzero channel,
the plotted ratio is zero and $\rho_0$ is undefined. A centered correlation estimator requires its
own support, preprocessing and missing-data contract.

### Preserve meaning when drawing fewer points

- Choose complete aligned pairs as the reference. A stride can repeatedly pick the
  same position in a periodic trace. If drawing fewer points, select pairs jointly and
  report the covered sample range and selection rule. Keep quantitative diagnostics on
  the underlying frame. An occupancy grid that counts all pairs can retain repeat visits
  when the drawing budget disallows an individual dot for every pair.
- For a density history, account for each sample once across overlapping snapshots.
  Count out-of-view pairs separately from visible bin counts. Repainting the same
  snapshot can otherwise make measured density depend on the render rate.
- Preserve channel pairing through any reduction. For pairs $(1,0)$ and $(0,1)$, taking
  each channel's maximum independently invents $(1,1)$. Keep the original pair from the
  chosen index. If connecting a chronological trace, break at discontinuities and
  distinguish sampled vertices from drawn segments.
- Treat view gain, persistence and palette as display settings. If persistence is
  expressed as an elapsed-time half-life $\tau$, multiply existing intensity by
  $2^{-\Delta t/\tau}$ for elapsed time $\Delta t$ measured in the same units.
  Clear old history at a discontinuity according to the view contract. Check identical
  elapsed-time decay at different render rates and distinguish old points from samples
  in the current window. Measure latency and draw cost on the intended host.

### Reproducible checks

Generate the samples in the table directly from the stated inputs. Compare the measured
points to analytical expectations before pixel quantization. The checks below used binary64
arithmetic in an isolated numerical probe. The results concern the stated fixtures.

| Input or experiment | Expected result and observation |
| --- | --- |
| 81 pairs from the Cartesian product of [−1.25, −1, −0.75, −0.25, 0, 0.25, 0.75, 1, 1.25] with itself | Invert the coordinates and compare to the original inputs. Maximum component error was about $2.22\times10^{-16}$ and maximum squared-norm error was about $4.44\times10^{-16}$. Channel swaps reflected the horizontal coordinate. |
| At 48 kHz use 480 frames of $L[n]=0.75\cos(2\pi fn/f_s)$ and $R[n]=L[n-D]$. Extend periodically using indices modulo the integer period. | For $f=1$ kHz and $D=\pm12$, both radii equal 0.75. Maximum squared-radius error was about $4.44\times10^{-16}$. The signed determinants of points 0 and 12 were approximately −0.5625 for lag and +0.5625 for lead. For $f=2$ kHz and $D=12$, maximum vertical magnitude was about $1.96\times10^{-16}$. |
| Plot the same 1 kHz lagged trace, starting at frame 0, with strides 1, 12 and 48 | It has 48, 4 and 1 distinct positions, respectively, when comparing coordinates to 12 decimal places. The stride-48 view collapses the circle to one dot. |
| Left samples [−1, −0.25, 0.25, 1] and half that amplitude on the right | The plot slope was −3. Axis-energy difference divided by total energy gave 0.8. The normalized raw inner product gave 1. |
| Compare $(1,0)$ and $(0,1)$ to the artificially combined maximum pair $(1,1)$ | The measured pairs have squared radius 1. The fabricated pair has squared radius 2. It would also plot on the equal-channel axis. |

### Acceptance cases for implementation review

| Failure to investigate | Test that distinguishes it |
| --- | --- |
| Wrong channel, axis or polarity | Use the signed basis pairs, channel swap, and one-channel impulses on different sample indices. Verify the numeric coordinates and projected quadrants independently. |
| Capture timing depends on callback grouping | At an origin above $2^{53}$, replay the same labelled pairs as one block and across uneven callbacks and a ring wrap. Check exact source indices, frame support and order. Introduce mismatched support, a gap and an epoch reset. Use known impulse timing to detect a one-sample payload shift that retains the original labels. |
| Presentation clips or deforms valid data | Draw the quadrature fixture in square and rectangular views. Check equal geometric scaling and expected extent before integer rounding. Separate over-level PCM, clipped pixels and valid full-scale diagonals. |
| Stale or invented points | Replay an impulse crossing a block boundary, followed by silence and a seek. Check paired selection and history policy. Keep measured occupancy, decayed intensity and input silence independently observable. |
| Unsupported input mutates state | Reject nonfinite values, a late malformed sample, mismatched channel counts and unavailable history according to the capture contract. Verify that a failed ingest preserves the last coherent frame and cursor. |

## Next action

Implement and independently test the frame-to-coordinate contract first. Ask a Kestrel
agent to diagnose a scope that shows a point on a controlled quadrature signal. Have the
agent trace the captured pairs and signs, verify the analysis window and shared viewport
scale, then vary the point-selection cadence. Use the full-rate circle and the stride-48
case to distinguish representation bias from a capture defect. Keep platform render
performance, real device behavior and future correlation estimates as separately verifiable
claims.

## Revisit when

The stereo tap, channel map, clock, DC policy, coordinate convention, drawing budget,
or persistence settings change. Recheck the expected shape and the relevant host behavior.
