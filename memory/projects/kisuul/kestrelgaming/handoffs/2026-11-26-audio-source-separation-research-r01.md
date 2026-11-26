---
schema: 1
id: 2026-11-26-audio-source-separation-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-26
updated: 2026-11-26
sources: "Audio branch a435c790546b7aefc8ba35ba18be1d7c235f916f; Le Roux et al. (2019); SigSep MUSDB18 dataset documentation; executed gain, mixture reconstruction, and source-assignment checks."
---

# Skill 66 research for source separation

## Summary

**Task outcome:** COMPLETE

Estimate distinct source signals from a mixture and
measure them on the same support as the references.
Check source identity over the output duration, output
level and leakage. Two estimates can sum to the exact
mixture while interchanging sources midway.
[Le Roux et al. (2019)](https://www.merl.com/publications/TR2019-013)

## Evidence

### Declare what each output should contain

Record dataset version and split, stem labels and
channel order, render and reference taps, support,
gain, sample rate, and any permitted time alignment.
Declare whether the task expects named stems or
anonymous streams per recording. For an additive
reference, confirm its stems sum to the intended mixture
within the declared tolerance before scoring. Include
the unprocessed mixture as a baseline and measure
the residual between the mixture and sum of estimates.
Report source quality and consistency of reconstruction
with separate checks. Report inactive-source leakage
on intervals that have valid support and silent targets.
[SigSep MUSDB18 dataset documentation](https://sigsep.github.io/datasets/musdb.html) ·
[Sound classification and source partitioning](2026-11-26-audio-sound-classification-research-r01.md)

For a named output, compare to its declared reference.
For anonymous outputs, select an assignment on the entire
evaluation unit with a declared score and tie rule. Hold
this assignment over that unit when persistent identity
is part of the task. Scoring each window with a new
permutation can make switched identities appear correct.
Record assignment policy and unmatched outputs. Include
an explicit channel and time alignment check.

### Measure residual and gain

For matched nonzero reference $s$ and estimate $\hat{s}$,
declare the DC treatment and score the same sample
support. The scale-invariant signal-to-distortion ratio
(SI-SDR) uses an orthogonal projection onto $s$.

$$
\alpha=\frac{\langle s,\hat{s}\rangle}{\langle s,s\rangle},
\qquad
\mathrm{SI\!-\!SDR}=10\log_{10}
\frac{\|\alpha s\|^2}{\|\hat{s}-\alpha s\|^2}.
$$

Track signed $\alpha$, gain error or a level-sensitive
metric alongside SI-SDR when output level or polarity
matters. If the reference is all zeros, projection is
undefined. For a zero estimate with a nonzero reference,
the ratio is `0/0` and the miss needs explicit accounting.
Under the fixture policy, both scores are unavailable.
Record exact nonzero proportional matches as $+\infty$
and nonzero orthogonal estimates as $-\infty$ under the
mathematical definition. Define how these values and
silent cases enter aggregates. Report the underlying
counts before any finite limit or weighting.
[Le Roux et al. (2019)](https://www.merl.com/publications/TR2019-013)

### Executed checks and portable fixtures

Let $s=$ `[1,−1,1,−1]` and $v=$ `[1,1,−1,−1]`.
Both have zero mean, energy 4, and zero inner product.
All comparisons use the given sample alignment with
no gain adjustment outside the metric.

| Estimate for $s$ | Signed gain | SI-SDR |
| --- | --- | --- |
| $s+v$ (mixture) | 1 | 0 dB |
| $0.5s+0.125v$ | 0.5 | 12.0412 dB |
| $s+0.25v$ | 1 | 12.0412 dB |

Construct two true eight-sample stems $[s,s]$ and $[v,v]$
by concatenation. Return $[s,v]$ and $[v,s]$. Their sum
matches the true mixture at every sample. Each half has
perfect reconstruction of both sources if reassigned for
that half. Every full-record source-to-output pair has
SI-SDR $10\log_{10}(1/3)\approx -4.7712$ dB, whichever
fixed assignment is selected. An all-zero estimate for
$v$ yields no score under the policy above and records a
missing source.

## Next action

Give Gauge the gain and swap fixtures, unmatched outputs,
inactive references, polarity inversion, and an impulse
alignment check. Evaluate a held-out dataset after
confirming its mixture contract and split. Report
per-source performance against the mixture baseline,
gain error and aggregate support.

## Revisit when

The source taxonomy, dataset, mixture construction,
timing, assignment, or score aggregation changes.
