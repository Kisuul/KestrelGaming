# Scope triggering measurement contract

[Detection](#detect-on-the-sample-clock) · [Acquisition](#decide-and-complete) ·
[Single-shot and epoch changes](#single-shot-and-epoch-changes) · [Reference](#offline-reference)

## Detect on the sample clock

Declare the tap, clock, epoch, sample rate, units, ordered channel IDs,
trigger channel, and direction. Set level $T$ and hysteresis $h\ge0$ in
the input's units. Detect on the named channel of the original PCM.
Retain aligned samples for all capture channels.
[Waveform capture contract](../../audio-oscilloscope/references/OSCILLOSCOPE_CONTRACT.md)

| Direction | Arm at positive hysteresis | Arm at zero hysteresis | Crossing at right sample $i$ |
| --- | --- | --- | --- |
| Rising | $x\le T-h$ | $x<T$ | $x_{i-1}<T\le x_i$ |
| Falling | $x\ge T+h$ | $x>T$ | $x_{i-1}>T\ge x_i$ |

Use the arm latch carried into the crossing. The first sample can arm.
A crossing needs an adjacent previous sample in the same epoch. After a
qualified crossing, clear the latch regardless of its disposition. Then
check rearming with the current sample and retain it for the next pair.
Keep updating these states during holdoff and while a capture is pending.
A plateau can supply a crossing at its first arrival at the level.
[NI edge hysteresis](https://www.ni.com/en/support/documentation/supplemental/21/ni-daqmx-data-acquisition-triggering-techniques-using-labview.html)

For each crossing, store right index $i$, the bracketing values, and the
interpolated position as left index $i-1$ and local fraction

$$
r=\frac{T-x_{i-1}}{x_i-x_{i-1}},\qquad 0<r\le1.
$$

Evaluate the arming boundary and this quotient with exact rationals of
the represented input values. The fraction estimates the crossing of
the line between the two samples. Use $i$ for scheduling. For a time
relative to the epoch, subtract its integer origin from $i-1$ before
adding $r$ and dividing by the sample rate.
[Timebase](../../audio-timebase-sync/SKILL.md)

## Decide and complete

Use nonnegative integer counts $P$, $Q$, and $H$ for pretrigger frames,
posttrigger frames, and holdoff intervals. A trigger at $i$ requests
$[i-P,i+Q+1)$. On acceptance at $i$, set release to $i+H$. At release,
a fresh qualified crossing is eligible.
[Tektronix holdoff and trigger modes](https://www.tek.com/en/documents/primer/oscilloscope-systems-and-controls)

Evaluate each crossing in this order. Record the first applicable decision.

| Decision | Condition |
| --- | --- |
| `unarmed` | The source-side latch is clear. |
| `single_disarmed` | Single-shot permission is absent. |
| `holdoff` | The right index is earlier than release. |
| `busy` | An earlier capture is still pending at this sample. |
| `missing_prehistory` | The requested start is before the first retained frame. |
| `span_out_of_range` | The requested exclusive end exceeds the supported range. |
| `accepted` | The edge passes every gate. |

A suppression preserves the existing release. A qualified edge uses
its arm at the crossing. On acceptance, save the epoch, settings, crossing, and
requested bounds. Keep the span pending until its exclusive end arrives.
On the final sample of a pending span, decide any crossing before
publishing the older capture. With $Q=0$, publish the acceptance followed
by the complete capture at the same sample.

Validate and freeze every channel plane in an input block before changing
state. Require its start to match the exclusive cursor. Retain the newest
$P+Q+1$ frames and snapshot a complete span before ingest can evict it.
One block can complete several captures. Compare their sequence in sample
order across callback partitions.

## Single-shot and epoch changes

Normal mode starts enabled. Single-shot starts disabled. An explicit arm
while idle starts a fresh hysteresis search on the next valid sample and
permits one acceptance. Keep the measured prehistory and current holdoff.
Repeated arm while enabled is idempotent. Reject arm while a span is
pending. An acceptance uses permission. A suppression preserves it.
Label an auto-mode fallback from a deployed scope as untriggered.

Reject invalid input, gaps, and overlaps before committing state. A valid
contiguous retry uses the prior state. For a confirmed discontinuity,
reset to a fresh epoch. Reset reports an abort for a pending span and
clears history, previous sample, latch, holdoff, and shot permission.
Use a fresh reference instance to change trigger settings.

## Offline reference

Put both `audio-oscilloscope/scripts` and `audio-scope-triggering/scripts`
on the Python module search path. Create `ScopeTrigger` with the shared
`ScopeEpoch` and `TriggerSettings`. Use `ingest(epoch=..., start_sample=...,
planes=...)` for each block, `arm_single()` for single-shot, and
`reset_epoch(epoch)` for a fresh clock epoch.

Ingest returns ordered `CrossingDecision` and `CaptureComplete` records.
A decision gives the requested bounds and current holdoff release, including
`None` before the first acceptance in an epoch. A completion carries the
accepted decision and a `CaptureWindow` for projection. Reset returns
`CaptureAborted` when it cancels a pending span, or `None`.

The sequential reference uses the shared epoch, PCM and block limits.
Use one through eight channels, up to 256 input frames per block, and
$P+Q+1\le1024$. Input starts, exclusive ends, and the holdoff count fit
$[0,2^{256}-1]$. The computed release may extend beyond that range.
Give level and hysteresis as finite binary64 floats or integers.
[Frozen fixtures](../../../tests/fixtures/AUDIO_SCOPE_TRIGGERING_GOLDENS.md)
