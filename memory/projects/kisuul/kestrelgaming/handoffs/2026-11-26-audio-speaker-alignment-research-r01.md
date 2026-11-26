---
schema: 1
id: 2026-11-26-audio-speaker-alignment-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-26
updated: 2026-11-26
sources: "Audio branch 3d65d0ddb88fead8d8a067e6abb8877ae5609d7b; Linkwitz crossover guidance, REW Alignment Tool, Kestrel cross-correlation and group delay contracts; executed coherent sum, polarity, and position fixtures below."
---

# Skill 56 research for speaker alignment

## Summary

**Task outcome:** COMPLETE

Define the alignment objective and the receiver positions.
First establish coarse arrival timing on a shared reference.
Then use the complex sum across the crossover band to evaluate
gain, delay and polarity. A setting that maximizes level at
one frequency can give a different result over the rest of
the band.
[Linkwitz crossover behavior](https://www.linkwitzlab.com/crossovers.htm) ·
[REW Alignment Tool](https://www.roomeqwizard.com/help/help_en-GB/html/graph_allspl.html)

## Evidence

### Acquire each path on the same reference

Measure each branch and their combined output with the receiver
fixed. Retain the reference tap, clock, timing origin, gain,
crossover settings, sample coverage and microphone position.
Start with a distinctive probe for coarse timing. Identify
a credible direct arrival when the task needs arrival matching.
A larger reflection can follow it. Compare matched response
windows and use the bins where both paths have adequate level
and coherence. The desired window for direct-path analysis can
differ from the window for diagnosing bass at a listening seat.
[Impulse response research](2026-11-26-audio-impulse-response-research-r01.md) ·
[Cross-correlation](../../../../../skills/audio-cross-correlation/SKILL.md)

### Predict a coherent sum over a band

On a common complex frequency grid, let $H_A$ and $H_B$ describe
the two measured responses. For new gains $a,b\ge 0$, delays
$d_A,d_B$ in seconds and a polarity setting $\sigma$ of $+1$
or $-1$ on B, predict

$$
H_\Sigma(f)=aH_A(f)e^{-j2\pi f d_A}
            +\sigma bH_B(f)e^{-j2\pi f d_B}.
$$

Adding two magnitude curves misses phase cancellation. Group
delay is a local phase slope. A polarity change gives a
half-turn while a time delay changes the slope. Measurements
at just one frequency cannot identify both. Keep the allowed
delay range, step size, phase convention and band in the
decision. A live controller normally adds delay to the early
path for a relative compensation. Include any common added
delay in the delivery budget.
[Group delay](../../../../../skills/audio-group-delay/SKILL.md) ·
[Paired phase and coherence](../../../../../skills/audio-phase-coherence/SKILL.md)

Choose the objective before selecting a setting. For example,
compare target level error across a declared band at each
position, or minimize the worst dip in the supported overlap.
Use frequency and position weights that match the task.
Report the best alternatives and any incompatible positions.
Avoid deriving a conclusion from a phase curve at a response
null. Remeasure the combined output and inspect the prediction
residual. Check gain mismatch, changing receiver conditions,
processing and nonlinear behavior if the responses disagree.

### Executed checks and portable fixtures

Use unit gains and no change to the measurement clock.
The figures below are linear magnitude of the sum relative
to one branch.

| Probe | Verified result |
| --- | --- |
| Let B arrive 5 ms after A. Compare sums at 50, 100 and 150 Hz. | Unadjusted magnitudes are $\sqrt{2},0,\sqrt{2}$. Reversing B yields $\sqrt{2},2,\sqrt{2}$. Adding 5 ms to A with original polarity yields 2 at all three. |
| At 48 kHz put unit taps at 0 and 240 in a 720-sample response. Use a 960-point FFT. | The independent time-domain sum has its 100 Hz bin zero within `1e-13`. |
| At two positions, let B arrive 4 ms and 6 ms after A respectively. Test a single 5 ms correction on A at 100 Hz. | The relative timing errors have opposite signs. The predicted magnitude is $2\cos(\pi/10)\approx1.902113$ at both positions. |

The probes use a linear pure-delay model. Acoustic crossover
shape, real path repeatability, and the listener-area tradeoff
remain separate measurements.

## Next action

Implement a bounded comparison of delay, polarity and gain
on measured coherent responses. Return the exact bins and
positions used and the predicted sum. Have Gauge compare a
one-frequency optimum, a band optimum, a shifted receiver,
and a deliberately unsupported alignment.

## Revisit when

The crossover, target band, receiver geometry, timing budget,
control resolution, or objective changes.
