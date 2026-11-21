---
schema: 1
id: 2026-11-20-audio-scope-triggering-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-20
updated: 2026-11-20
sources: "Tektronix trigger controls, Kestrel sample-clock guidance, and crossing, holdoff-boundary and binary64 coordinate checks. Audio curriculum PR #2 at 4dc854e450bac96ec985c7ab226941cc8efe13c9. VeNerVRA audio engineering research brief, revised 2026-11-20."
---

# Scope triggering research

## Summary

Planned skill #29 · `audio-scope-triggering`

**Task outcome:** COMPLETE

Detect and capture a waveform event on the sample clock. Specify arming, crossing, holdoff
and capture boundaries so a reviewer can audit every accepted or suppressed trigger from the
input samples.

## Evidence

**Detect and capture on the sample clock.** Reuse the
[waveform capture contract](2026-11-20-audio-oscilloscope-research-r01.md). Choose a
trigger channel, level, direction, hysteresis, holdoff, and pre/post lengths. Treat
threshold detection, acquisition acceptance, and capture completion as separate events. This
allows a reviewer to tell whether a trigger was missed, suppressed, or still awaiting
post-trigger samples.
[Tektronix trigger controls](https://www.tek.com/en/documents/primer/oscilloscope-systems-and-controls)

- **Arm and detect.** For $h>0$, arm a rising trigger after $x\le T-h$, or a falling
  trigger after $x\ge T+h$. At $h=0$, arm strictly below or above $T$, respectively.
  Detect rising at $x[i-1]<T\le x[i]$ and falling at $x[i-1]>T\ge x[i]$. Equality belongs
  to the arrival side. A constant plateau at threshold produces no edge. Preserve previous
  sample and arming state across callbacks.
- **Locate.** Record the right sample $i$ as the exact detection index. If interpolating,
  store left index $i-1$ and local fraction $(T-x[i-1])/(x[i]-x[i-1])$ separately. Keep
  track of the sample pair that defines this estimate. Converting $2^{53}+1+1/4$ to one
  binary64 sample coordinate rounds to $2^{53}+2$.
- **Qualify and complete.** After accepting a trigger at $i$, set the holdoff release index
  to $i+H$ for a holdoff of $H$ samples. A fresh crossing is eligible at or after release. Consume a qualified crossing during
  holdoff. Rearming can occur during holdoff, so a fresh qualified crossing can be accepted
  at release. With $P$ samples before the detection index and $Q$ after it, capture
  $[i-P,i+Q+1)$. Specify what happens with missing prehistory and when capture is busy.
  Emit the complete event once the exclusive end is available. A single-shot mode accepts
  one trigger per explicit arm. An optional auto mode measures timeout in samples and labels
  its fallback capture untriggered. Validate the incoming block before committing trigger
  state. On epoch reset, clear history and pending captures.

**Review from a hand-computed timeline.** At start index 100, send [−1, −1/4] then [3/4,
1/2]. With rising threshold 0, hysteresis 1/2, $P=2$, and $Q=1$, the right sample is 102,
the interpolated position is $101+1/4$, and the capture is [100, 104). The split falls
exactly on the crossing. Compare to one uninterrupted buffer. For $H=4$, $P=Q=0$, and the
same rising threshold and hysteresis, use [−1, 1, −1, −1, 1, −1] at start index 0. Accept
index 1 and suppress the fresh crossing at 4. With [−1, 1, −1, −1, −1, 1], accept indices 1
and 5. Add a level plateau, chatter that never rearms, insufficient history, a reset during
capture, and separate trigger/display channels. Compare detection indices and capture spans
even when the displayed trace looks stable.

### Reproducible checks

| Check | Reproduction method | Recorded result |
| --- | --- | --- |
| Interpolated crossing at a large index | Interpolate a rising crossing of zero from $-1/4$ to $3/4$ at left index $2^{53}+1$. Compare integer-plus-fraction with one binary64 coordinate. | The exact crossing is $9007199254740993+1/4$. One binary64 coordinate rounded to 9007199254740994. |

The scalar coordinate and hand-computed boundary examples were independently checked. The
capture state machine is proposed.

## Next action

Verify the trigger state machine with fixed sample vectors before attaching it to a display.
Replay the same stimulus as one block and with boundaries at an arming sample, the crossing
and the capture completion. Compare detection indices, fractional estimates and capture
intervals exactly for the rational fixtures.

## Revisit when

The trigger channel, hysteresis, holdoff, busy-capture policy, epoch handling, or latency
requirements change.
