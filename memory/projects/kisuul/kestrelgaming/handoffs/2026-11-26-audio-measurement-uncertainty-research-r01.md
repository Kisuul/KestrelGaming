---
schema: 1
id: 2026-11-26-audio-measurement-uncertainty-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-26
updated: 2026-11-26
sources: "Audio branch a435c790546b7aefc8ba35ba18be1d7c235f916f; JCGM 100:2008; NIST TN 1297; executed covariance budget and paired Monte Carlo check with NumPy 2.3.5."
---

# Skill 69 research for measurement uncertainty

## Summary

**Task outcome:** COMPLETE

Define the measurand and its measurement model before
assigning an uncertainty. Record the evidence, units and
common causes for each input. In a paired level
comparison, the same calibration offset can cancel.
Repeated readings of an absolute level retain that
common uncertainty.
[JCGM 100:2008](https://www.bipm.org/en/doi/10.59161/jcgm100-2008e)

## Evidence

### Build a budget around the measurement

State the tap, level reference, bandwidth, time
support, conditions, and scope of the result. Account
for significant known effects with corrections and
record the uncertainty of each correction. For each
input, record its estimate, unit, distribution or
method, standard uncertainty, evidence, and dependence
on other inputs. Use Type A for evaluation by
statistical analysis of observations. Use Type B for
evaluation from other information such as calibration
records, resolution, or supported bounds. Both enter
the budget as standard uncertainties.
[NIST TN 1297, combined standard uncertainty](https://www.nist.gov/pml/nist-technical-note-1297/nist-tn-1297-5-combined-standard-uncertainty) ·
[SPL metering](2026-11-26-audio-spl-metering-research-r01.md) ·
[Microphone calibration](2026-11-26-audio-microphone-calibration-research-r01.md)

For $y=f(x)$, use the sensitivity row
$J=(\partial f/\partial x_i)$ at the input estimates
and covariance matrix $C$. First-order combined
standard uncertainty is $u_c(y)=\sqrt{JCJ^\mathsf{T}}$.
The expression is exact for the linear model below.
Check that the measurement chain supports the assumed
covariances. A change in gain, instrument, channel,
frequency response, or drift can change which terms
are shared. For significant nonlinearity, validate
propagation using the declared joint input model.
[NIST TN 1297, law of propagation](https://www.nist.gov/pml/nist-technical-note-1297/nist-tn-1297-appendix-law-propagation-uncertainty)

Report the result, $u_c$, and the conditions. If using
expanded uncertainty $U=k u_c$, state $k$ and the basis
for any coverage probability. Keep the scale and
distribution assumptions visible. An instrument
tolerance, a numerical test tolerance, and a measurement
uncertainty serve different decisions.
[NIST TN 1297, expanded uncertainty](https://www.nist.gov/pml/nist-technical-note-1297/nist-tn-1297-6-expanded-uncertainty)

### Executed checks and portable fixtures

Let the measured levels be $L_A=84+c+e_A$ and
$L_B=80+c+e_B$ in dB relative to the same reference.
Use zero-mean independent terms $c,e_A,e_B$ with
standard uncertainties 0.6, 0.2, and 0.3 dB
respectively. The two levels use the same draw of
$c$, which gives covariance 0.36 dB². Their marginal
variances are 0.40 and 0.45 dB². The sensitivity row
for $\Delta L=L_A-L_B$ is $(1,-1)$.

| Budget for the 4 dB difference | Combined standard uncertainty |
| --- | --- |
| Same calibration offset | $\sqrt{0.40+0.45-2(0.36)}=0.360555$ dB |
| Separate offset terms with correlation 0.5 | $\sqrt{0.40+0.45-2(0.18)}=0.700000$ dB |
| Zero covariance | $\sqrt{0.40+0.45}=0.921954$ dB |

At $k=2$ the first budget gives $U\approx0.721110$ dB.
For an arithmetic cross-check, draw 500,000 independent
normal triples with the specified standard deviations
and share each $c$ within its pair. With PCG64 seed
690069 in NumPy 2.3.5, the sample standard deviation
of $\Delta L$ was 0.360006 dB. This checks the
stipulated covariance model.

For sixteen absolute readings with common calibration
uncertainty 0.6 dB and independent repeat uncertainty
0.4 dB per reading, the uncertainty of their mean is
$\sqrt{0.6^2+0.4^2/16}=0.608276$ dB. Treating both
terms as independently redrawn at each reading instead
gives 0.180278 dB. More repeats reduce the independent
term. Calibration evidence determines the common term.

## Next action

Give Gauge budgets for fully shared, partially shared,
and independent calibration. Record the calibration ID
and conditions that justify each relation. Recalculate
absolute and paired results with repeated readings.
Check any assumed coverage probability against the
input model and available evidence.

## Revisit when

The measurand, calibration, number of repeats, input
dependence, estimator, or coverage requirement changes.
