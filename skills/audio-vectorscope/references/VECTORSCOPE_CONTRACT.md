# Audio vectorscope measurement contract

[Input](#aligned-pairs) · [Coordinates](#measured-coordinates) ·
[Viewport](#viewport-geometry) · [Reference](#offline-reference)

## Aligned pairs

Use a complete `CaptureWindow` from one tap, clock, and epoch. Select two
distinct channel IDs in the capture and declare which is left and which
is right. Use the same original sample index for both values in each
pair. Keep the rate, amplitude units, exact half-open bounds, and IDs
with the projected points. Two measured zeros give the origin. Resolve
missing channels and ambiguous routing at the capture source.
[Capture contract](../../audio-oscilloscope/SKILL.md) ·
[Channel mapping](../../audio-channel-mapping/references/CHANNEL_MAPPING_CONTRACT.md)

Web Audio `AnalyserNode` time-domain readback uses a mono downmix. For a
stereo vectorscope, obtain separate channel planes from a shared sample
clock. When comparing scope products, check whether the display plots
raw pairs or derives shape from detected levels.
[Web Audio time-domain downmix](https://www.w3.org/TR/2021/REC-webaudio-20210617/#time-domain-down-mixing) ·
[Insight 2 Sound Field](https://s3.amazonaws.com/izotopedownloads/docs/insight200/en/print/index.html#sound-field)

## Measured coordinates

Use positive-right and positive-up mathematical axes. For a simultaneous
pair $(L,R)$, set $u=R-L$ and $v=L+R$. The displayed signal coordinates are

$$
x=\frac{u}{\sqrt{2}},\qquad y=\frac{v}{\sqrt{2}}.
$$

The exact transform preserves $x^2+y^2=L^2+R^2$ and has inverse
$L=(y-x)/\sqrt2,\ R=(y+x)/\sqrt2$. Swapping channels negates $x$.
Under Kestrel's half-gain Mid/Side convention, $x=-\sqrt2 S$ and
$y=\sqrt2 M$. Keep DC in the measured data. Specify the mean-removal
interval in a centered view.

Compute $u$ and $v$ exactly from the represented PCM. Check each
numerator $z$ against $z^2\le 2B^2$, where $B$ is the largest finite
binary64 value. The offline reference then divides by $\sqrt2$ in a
private 80-digit decimal context and returns binary64 coordinates.
A failed range check gives the axis and exact sample index and returns
no partial frame. Compare the rounded coordinates with a fixture tolerance.

Equal channels give a vertical line and opposite-polarity copies give a
horizontal line. The equal-weight mono mix is $y/\sqrt2$.
Use the measured fold-down when diagnosing a mix. Equal-amplitude
single-frequency channels in quadrature give a circle. With declared
axes, the time-ordered points distinguish the lead and lag cases of
that test tone. A known frequency and a controlled stimulus are needed
to infer a delay.

Use common and differential DC tests to check offsets. With $R=L/2$
the trace has slope $-3$ even though the channels are positively
proportional. The normalized raw inner product is 1 for that nonzero
pair sequence. The normalized difference of plotted axis energies
is 0.8. Choose and document the requested correlation estimator.

## Viewport geometry

Choose a positive finite nominal full scale $A$ in the input units.
The nominal input square maps to $|x|+|y|\le\sqrt2 A$. Choose a finite
center $(c_x,c_y)$ and positive finite half-extents $(h_x,h_y)$.
Set $m=\min(h_x,h_y)$. For down-positive rows, the continuous pixel
coordinates are

$$
p_x=c_x+\frac{m u}{2A},\qquad p_y=c_y-\frac{m v}{2A}.
$$

These offsets use the same geometric gain $m/(\sqrt2 A)$ for both axes.
The reference keeps the pixel coordinates exact as rationals. Flag an
out-of-view point if either offset exceeds the corresponding half-extent.
Equality is inside the continuous bounds. Quantize when rasterizing.
Flag over-nominal input if either measured channel exceeds $A$ in
magnitude. For a clipping diagnosis, inspect the tap and waveform.
Match basis, origin, and axis gains before comparing other tools.
[FFmpeg 7.1 vectorscope projection](https://www.ffmpeg.org/doxygen/7.1/avf__avectorscope_8c_source.html#l00391)

The frame has one point per measured pair. To draw fewer points, select
whole pairs by their shared sample index. Report the selection and
sample support. For a chronological line view, break the line at
discontinuities. If a view aggregates overlapping captures, account for
repeat visits by source index. Use host measurements for paint cadence
or latency.

## Offline reference

Put `audio-oscilloscope/scripts` and `audio-vectorscope/scripts` on the
Python module search path. Pass a shared `CaptureWindow` and explicit
`left_channel` and `right_channel` IDs to `project_vectorscope`. Supply
a `VectorscopeViewport` for screen coordinates and the two flags.
Geometry settings accept finite built-in integers or binary64 floats.
A frame retains the capture's epoch and bounds. Each point has the
same integer sample index as its input pair.

The input frame follows the shared limit of one to 1,024 frames and one
to eight named channels. Select two available channels. Fixed-hop
snapshots and `CaptureComplete.window` from a trigger use the same API.
All valid points are returned in sample order.
[Trigger capture](../../audio-scope-triggering/SKILL.md) ·
[Frozen fixtures](../../../tests/fixtures/AUDIO_VECTORSCOPE_GOLDENS.md)
