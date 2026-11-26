---
schema: 1
id: 2026-11-26-audio-transfer-response-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-26
updated: 2026-11-26
sources: "Audio branch 3d65d0ddb88fead8d8a067e6abb8877ae5609d7b; Kestrel paired Welch and group delay, SciPy 1.17.0 CSD, Siemens FRF estimator guidance, Muller and Massarani (2001); executed transfer and noise-location fixtures below."
---

# Skill 48 research for transfer response

## Summary

**Task outcome:** COMPLETE

Measure complex response from a stated input tap to a stated
output tap. Pair the observations on a known timebase, preserve
excitation and coherence, and choose an estimator that fits where
the noise enters. The fixtures check both estimator biases,
delay sign, and an exact spectral null.
[Phase and coherence](../../../../../skills/audio-phase-coherence/SKILL.md) ·
[Group delay](../../../../../skills/audio-group-delay/SKILL.md)

## Evidence

### Establish the path and stimulus

Name the input and output channels, units, tap locations,
clock, epoch, gains, and any time offset already applied. Use
the same complete window starts for each paired capture. A
single complex ratio $Y/X$ on a coherent known stimulus
depends on nonzero input and adequate capture support. For an
impulse test, retain the entire response required by the task.
For a sweep, keep the emitted reference, the matching inverse,
and the support and frequency range in which deconvolution is
well conditioned.
[Test-signal research](2026-11-26-audio-test-signals-research-r01.md) ·
[Muller and Massarani (2001)](https://publications.rwth-aachen.de/record/192865)

Test whether the system is adequately linear and time invariant
for the result. Repeat the probe at a second declared drive
level or time and compare complex response, residuals and
coherence. Changing source or response gain during a Welch
average can change the estimate. For multiple active inputs,
estimate a transfer matrix only when the stimulus and input
spectral matrix support separating the channels. Otherwise
excite one input at a time and state what was measured.
[FRF estimation](https://www.svibs.com/resources/ARTeMIS_Modal_Help_v7/Frequency%20Response%20Function%20estimation.html)

### Choose the response estimator

For paired spectra, set $P_x=\langle X^*X\rangle$,
$P_y=\langle Y^*Y\rangle$, and $C=\langle X^*Y\rangle$.
Use the same normalization and support when averaging the
complex and auto powers. The conjugate-reference convention
matches Kestrel and SciPy's CSD argument order.

$$
H_1=C/P_x,\qquad H_2=P_y/C^*,\qquad
\gamma^2=\lvert C\rvert^2/(P_xP_y).
$$

$H_1$ matches the population transfer when the reference is
reliable and additive output noise is uncorrelated with it.
Independent measurement noise added to the input tap biases
$H_1$ toward smaller magnitude. $H_2$ matches the transfer
with noise only on the input measurement under the corresponding
uncorrelated model. Independent output noise can bias
$H_2$ upward in magnitude. When all denominators are nonzero,
$H_1/H_2=\gamma^2$. This identity checks convention and
aggregation. Choosing an estimator for a particular device
still requires evidence of its noise, excitation and model.
[Siemens H1 and H2](https://community.sw.siemens.com/articles/en_US/Knowledge/what-is-a-frequency-response-function-frf) ·
[SciPy 1.17.0 CSD](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.signal.csd.html)

### Qualify and report the result

Report the available complex response, magnitude and phase
with the actual frequency grid, support, and tap references.
For magnitude in dB use $20\log_{10}\lvert H\rvert$ with
the input/output unit ratio stated. Gate weak excitation,
inadequate support and coherence using a declared policy.
Distinguish no reference power, a response null, and an
unavailable phase. A single supported segment can produce
unity coherence by algebra. Keep segment counts and measured
levels with the curve.

Under the negative-exponent Fourier convention a delayed
copy contributes negative phase slope. Check the sign with a
known delay and retain any advance or alignment offset. If
the device requires an absolute delay result, restore the
declared timing correction. Do not infer a first arrival from
group delay in a frequency band. Check the impulse response
and the clock mapping for that question.
[Paired Welch contract](../../../../../skills/audio-phase-coherence/references/PHASE_COHERENCE_CONTRACT.md#welch-profile) ·
[Group delay timing](../../../../../skills/audio-group-delay/references/GROUP_DELAY_CONTRACT.md#timing-and-units)

### Executed checks and portable fixtures

| Probe | Verified result |
| --- | --- |
| At one bin use two equally weighted spectral pairs with $X=(1,1)$ and $Y=(3,1)$. Interpret $Y$ as gain 2 plus output noise $(1,-1)$. | $H_1=2$, $H_2=2.5$, and $\gamma^2=0.8$. The additive component cancels in the cross sum. |
| Use $X=(1.5,0.5)$ and $Y=(-2j,-2j)$. Interpret the true input as $(1,1)$ and the input measurement error as $(0.5,-0.5)$. | $H_1=-1.6j$, $H_2=-2j$, and $\gamma^2=0.8$. The estimator choice changes magnitude in this case, while the signed phase stays the same. |
| Place an impulse of value 1 at input sample 32 and an impulse of value 0.25 at output sample 39. Transform both in 256 samples. | All 129 nonnegative bins agree with $0.25\exp(-j2\pi 7k/256)$ within `6.14e-16` in complex gain. |
| Use the input impulse and the FIR coefficients $(1/2,1/2)$ with output support retained. | The DC gain is 1, and the Nyquist response is exactly zero. There is no phase at the null. |

These checks use synthetic spectral pairs and finite impulses.
Stationarity, level-dependent response, channel isolation, and
device or room measurement accuracy need separate evidence.

## Next action

Implement a bounded paired-transfer baseline that preserves
$P_x$, $P_y$, $C$, support and timing. Provide estimator-specific
validity. Verify a raised noise floor, inadequate excitation,
a null, and known timing before interpreting a new transfer.

## Revisit when

The excitation, clock alignment, system model, estimator noise
assumptions, noise floor, or valid response band changes.
