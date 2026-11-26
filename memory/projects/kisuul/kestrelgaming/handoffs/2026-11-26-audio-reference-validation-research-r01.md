---
schema: 1
id: 2026-11-26-audio-reference-validation-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-26
updated: 2026-11-26
sources: "Audio branch a435c790546b7aefc8ba35ba18be1d7c235f916f; EBU Tech 3341 and EBU loudness test set; SciPy periodogram specification; executed exact-power and PSD comparisons with NumPy 2.3.5 and SciPy 1.17.0."
---

# Skill 68 research for reference validation

## Summary

**Task outcome:** COMPLETE

Verify the measured quantity against a reference with
known inputs, support, and expected results. Use an
independent calculation where possible. Test whether a
plausible wrong implementation fails. The fixtures expose
incorrect one-sided FFT weights and a normalization that
changes measured power when the transform is zero padded.
[FFT calibration](../../../../../skills/audio-fft-spectrum/references/FFT_CALIBRATION.md)

## Evidence

### Choose evidence for the claim

| Question | Check |
| --- | --- |
| Does this result have the correct units, support, and scale? | Use a small case with an exact result. Derive it without the production estimator. Check its clock and invalid states as well as its value. |
| Does an optimized path agree across supported inputs? | Compare it with a direct calculation on the same support. Exercise odd and even sizes, partial input, boundary conditions, and dynamic range. |
| Does a known change predict a definite change in the result? | Test a property such as power scaling by $g^2$ after linear amplitude gain $g$, within the estimator's valid range. A constant scale error can pass this property. |
| Does a defined profile meet published limits? | Pin the edition and test material. Apply its stated conditions and tolerances. Record the cases exercised and the scope of the claim. |

A library comparison can corroborate shared conventions.
Use a different derivation to expose errors that both
paths could share. Save the input, tap, algorithm,
declared transforms, versions, and observed output.
Select tolerances before seeing the outputs and state
their units. For a floating result, a bound such as
$|y-r|\le a+b|r|$ has a defined absolute allowance
$a$ near zero and a relative allowance $b$ at scale.
Check exact counts, channel identities, and sample ticks
directly. Use the profile's own comparison rule where
one is specified.
[Numerical stability](../../../../../skills/audio-numerical-stability/references/NUMERICAL_CONTRACT.md) ·
[Analysis provenance](../../../../../skills/audio-analysis-provenance/references/PROVENANCE_CONTRACT.md) ·
[EBU Tech 3341](https://tech.ebu.ch/publications/tech3341) ·
[EBU loudness test set](https://tech.ebu.ch/publications/ebu_loudness_test_set)

### Executed checks and portable fixtures

Use a real record of $N$ samples with a rectangular
window, no detrend, and an unnormalized forward DFT
$X[k]$ of length $M\ge N$. Weight each interior positive
frequency by two to include its negative partner. Weight
DC by one, and weight the Nyquist bin by one when $M$
is even. With these weights $c_k$, compute integrated
one-sided bin powers as $p_k=c_k|X[k]|^2/(MN)$.
Their sum is the mean square over the $N$ input samples.
Express a PSD in power per hertz by dividing each $p_k$
by the bin spacing $f_s/M$.
[SciPy periodogram normalization](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.periodogram.html)

| Probe | Verified result |
| --- | --- |
| Use `[3.5,0.5,−0.5,0.5,3.5,0.5,−0.5,0.5]` with $M=8$. Derive the result from the input sum of squares and from DC amplitude 1, Nyquist amplitude 0.5, and a bin-2 cosine of peak amplitude 2. | The powers at nonnegative bins are `[1,0,2,0,0.25]`. The exact energy is 26 and mean square is 3.25. Doubling DC and Nyquist gives the wrong total 4.5. |
| Use $x[n]=\cos(2\pi\cdot4n/9)$ for $0\le n<9$ with $M=9$. | Bin 4 is an interior bin and holds power 0.5 after folding. Weighting it by one gives 0.25. |
| Use the eight samples from the first case and set $M=32$. | Total power stays 3.25. Dividing the padded record's energy by 32 as though all 32 samples were observed gives 0.8125. |

At 16 kHz, SciPy 1.17.0 with a boxcar, no detrend,
and `density` scaling agreed with each folded bin power
after multiplication by $f_s/M$ within `1e-14`
power units. NumPy 2.3.5 supplied the comparison DFT.
The exact even-length result and the cosine identity
give reference values from the signal itself. These
checks use a rectangular window and declared input
support. Validation for shaped windows and external
meter profiles needs its own fixtures.

## Next action

Give Gauge a small exact oracle, a published case where
applicable, and at least one expected failure for each
major claim. For the spectrum, replay both parities,
zero padding, and an unsupported segment. Set a tolerance
from the specification or numerical error budget and
retain the first divergent stage when a check fails.

## Revisit when

The estimator, numeric representation, calibration,
window, tested profile, or meaning of a reported value changes.
