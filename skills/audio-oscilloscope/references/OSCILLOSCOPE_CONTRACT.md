# Oscilloscope waveform capture contract

## Capture on the sample clock

Choose a tap and a clock domain. Declare their identifiers with the epoch ID,
epoch origin $o$, positive rational sample rate $f_s$, linear amplitude units,
and ordered channel IDs. Record one value per channel at each sample index.
Use the original units, including signed values beyond nominal full scale
when the tap permits them.
[Sample clock contract](../../audio-timebase-sync/SKILL.md) ·
[Channel mapping](../../audio-channel-mapping/SKILL.md)

For window length $L$ and hop $H$, use integer starts $s=o+kH$ for $k\ge0$.
Emit each complete interval $[s,s+L)$ once when the cursor reaches its
exclusive end. Store all channel planes for that interval in one snapshot.
Report $2s+L-1$ as the doubled center sample. The window duration is
$L/f_s$. Its first-to-last sample time span is $(L-1)/f_s$. To get
epoch-relative time, subtract $o$ from the integer sample index before
dividing by $f_s$. Keep the integer coordinates for a long-running stream.

Require each block to match the epoch metadata and start at the exclusive
input cursor. Reject a gap, overlap, invalid sample, or shape mismatch
before accepting any part of the block. With a confirmed discontinuity,
start a fresh epoch with empty history and a new origin. Also start a
fresh epoch when the tap, clock, rate, channel layout, or units change.
Wait for a full window after the reset. A valid contiguous retry uses the
previous state after rejection.

Retain at least $L$ sample frames. A single block can complete several
windows. After validation, ingest through each scheduled end in order and
take the snapshot there. This preserves earlier captures when the block
exceeds retained history. At origin 100 with $L=4$, $H=2$, and four frames
of history, a nine-frame block emits $[100,104)$, $[102,106)$, and
$[104,108)$. Committing the full block first would leave only $[105,109)$
in history. Copy the complete capture before the ring can overwrite its
samples.
[Stream buffering](../../audio-stream-buffering/SKILL.md)

The renderer can skip a presentation or redraw the same snapshot at a
different width. Use target measurements for presentation cadence,
latency, and device-clock alignment.

## Display projection

For width $1\le W\le L$, let $j$ range from $0$ through $W-1$. The support
of column $j$ is

$$
[s+\lfloor jL/W\rfloor,\ s+\lfloor(j+1)L/W\rfloor).
$$

Compute both edges by integer division. Each bucket owns at least one
sample and the buckets partition the window. Per channel, return the
minimum, maximum, and earliest index attaining each. With $W=L$, each
bucket has one sample. For $W>L$, report the original indexed points with
all channel values in order.

The bucket preserves recorded extrema and discards the remaining waveform
shape. Draw connecting lines as an interpolation of displayed points.
For a lower-rate audio signal, specify a dedicated resampler with a filter
and an output time grid. Route intersample-level questions to true-peak
analysis.
[Tektronix acquisition modes](https://www.tek.com/en/documents/primer/oscilloscope-systems-and-controls) ·
[BBC min/max waveform example](https://github.com/bbc/audiowaveform) ·
[Resampling](../../audio-resampling/SKILL.md) · [True peak](../../audio-true-peak/SKILL.md)

A float time-domain readback from one `AnalyserNode` with an array of length
`fftSize` returns recent samples after mono downmix. The stereo speaker
downmix uses equal left and right weights. Opposite-polarity input can
cancel there. Capture distinct channel planes at one graph tap with one
sample cursor when the requirement is a clocked stereo trace.
[Web Audio readback](https://www.w3.org/TR/2021/REC-webaudio-20210617/#dom-analysernode-getfloattimedomaindata) ·
[Web Audio mixing rules](https://www.w3.org/TR/2021/REC-webaudio-20210617/#channel-up-mixing-and-down-mixing)

## Offline reference

Create a `ScopeEpoch` with `Fraction` rate in Hz. Configure `ScopeAcquisition`
with fixed window, hop, and retained length in sample frames. Each call to
`ingest(epoch=..., start_sample=..., planes=...)` returns the newly complete
`CaptureWindow` values in order. The reference accepts a list or tuple of
channel planes. Each plane is a list or tuple of equal length. The window
stores immutable planar tuples and can also describe an explicit span with
the same metadata. Call `reset_epoch(epoch)` to start a fresh capture grid.

Use `project_waveform(capture, width=...)` to get `min_max` buckets or
`points`. Bucket extrema and point values follow the epoch's channel order.
The result carries the epoch and the original capture bounds. Shape,
configuration, and continuity errors raise `ValueError`.

The reference supports one through eight channels, up to 1,024 retained
frames, and one through 256 input frames per block. Choose
`1 <= window_frames <= history_frames`. Starts, origins, and exclusive
ends are integers from zero through $2^{256}-1$. The hop is positive and
fits that range. The first scheduled end must fit when an epoch begins.
A later scheduled end beyond the range remains unavailable in that epoch.
Width is a positive integer. Use finite binary64 floats or signed 32-bit
integers. The sequential reference retains used epoch labels.

Verify the buffer handoff and timing on the target backend.
[Frozen fixtures](../../../tests/fixtures/AUDIO_OSCILLOSCOPE_GOLDENS.md)
