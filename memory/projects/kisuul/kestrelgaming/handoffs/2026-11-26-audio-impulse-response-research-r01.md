---
schema: 1
id: 2026-11-26-audio-impulse-response-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-26
updated: 2026-11-26
sources: "Audio branch 3d65d0ddb88fead8d8a067e6abb8877ae5609d7b; Farina (2000), Muller and Massarani (2001), Smith acyclic FFT convolution; executed finite-convolution, spectral-null and time-wrap fixtures below."
---

# Skill 54 research for impulse response measurement

## Summary

**Task outcome:** COMPLETE

Use the recorded excitation and response on a known timebase.
Specify linear convolution and the interval in which the result
is observable. Keep the earliest supported arrival and the
largest response separate. The fixtures expose circular wrap
and loss of information when the input has a spectral null.
[Muller and Massarani (2001)](https://publications.rwth-aachen.de/record/192865)

## Evidence

### Capture the signal path

Name the excitation and measurement taps, their scales, sample
rate, and clock relationship. For a linear time-invariant path
write $y[n]=\sum_i x[n-i]h[i]+e[n]$. In this model, $x$ is
the realized excitation, $h$ describes the transfer between
the chosen taps, and $e$ is an additive residual. Capture
guard time and a response tail sufficient for the question.
Retain the original time origin and any applied time correction
in the result. Changing the input or output tap changes what
the impulse response includes.
[Sample clock](../../../../../skills/audio-timebase-sync/SKILL.md) ·
[Analysis provenance](../../../../../skills/audio-analysis-provenance/SKILL.md)

A known digital impulse gives a direct linear fixture.
Sweeps allow a path with a low signal-to-noise ratio to be
measured with more energy distributed over time. Use the
matching inverse or deconvolution model for the emitted sweep.
Log sweep deconvolution can separate orders of harmonic
distortion under the conditions described by Farina. Compare
levels and repeated captures for time variation or nonlinearity.
Preserve the raw response before using a window to isolate
an arrival or remove parts of the tail.
[Farina (2000), §§2–3](https://angelofarina.it/Public/Papers/134-AES00.PDF) ·
[Phase and coherence](../../../../../skills/audio-phase-coherence/SKILL.md)

### Keep the inverse and its limits visible

For a finite source of length $N_x$ and assumed response
support of $N_h$ samples, the complete convolution has length
$N_x+N_h-1$. Capture that support with any added guard required
by the setup. For the finite FFT comparison use at least this
length. A shorter transform represents periodic time. If the
late response wraps, it can appear before the direct arrival.
Zero padding supplies zeros outside the capture support.
Recovering the true tail requires observing it.
[Acyclic FFT convolution](https://www.dsprelated.com/freebooks/sasp/Acyclic_FFT_Convolution.html)

For complex bins on the same grid, $H=Y/X$ is defined at
nonzero $X$. Where reference excitation is weak, gate the bin
or declare a regularized estimate such as

$$
\widehat H=\frac{X^*Y}{\lvert X\rvert^2+\lambda}.
$$

Use a positive $\lambda$ when filling unexcited bins and
record its value in the power scaling of $\lvert X\rvert^2$.
With no noise and $Y=XH$, this estimate is $H$ times
$\lvert X\rvert^2/(\lvert X\rvert^2+\lambda)$. A null in
$X$ gives no evidence of the true $H$ at that frequency,
even if an inverse fills it with zero. Report the band and
mask. The mask and regularization shape the time-domain result.
Check reconstruction by applying the estimate to the known
input and inspecting residuals over the retained support.

### Executed checks and portable fixtures

| Probe | Verified result |
| --- | --- |
| Convolve `[1,0.25,-0.125,0.0625]` with a 42-sample response whose only taps are +0.25 at 19 and −0.5 at 41. | The linear recording has 45 samples. Exact known times are 19 and 41 samples from the excitation. With a 64-point FFT, division and inverse FFT recovered the zero-padded response with maximum error about `4.2e-17`. |
| Fold the same recording by sample index modulo 32, then use a 32-point inverse. | The −0.5 tap wraps to index 9 and the +0.25 tap stays at 19. The largest peak now appears before the known direct arrival. |
| Convolve `[1,-1]` with `[0.5,0.25]`. Use a 16-point FFT and $\lambda=0.001$. | Both stimulus and recording have zero DC. The regularized estimate there is zero, while the known DC response is 0.75. Label that measurement unexcited. |

The time-domain convolution and the known taps provide the
independent expectations. Reflection selection, transducer
behavior, room noise, and actual sweep timing remain empirical
questions.

## Next action

Implement a bounded, guarded linear extraction with
clocked response provenance and an excitation-validity mask.
Verify a truncated tail, a stronger late reflection, and a
spectral null. Compare the recovered delay, polarity, complex
response and prediction residual with the declared model.

## Revisit when

The excitation, measurement geometry, support, inverse method,
clock correction, or linearity assumptions change.
