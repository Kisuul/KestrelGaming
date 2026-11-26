---
schema: 1
id: 2026-11-26-audio-spatial-localization-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-26
updated: 2026-11-26
sources: "Audio branch 3d65d0ddb88fead8d8a067e6abb8877ae5609d7b; Knapp and Carter (1976), Grinstein et al. (2024) SRP review, Kestrel signed cross-correlation; executed geometry, sign, and narrowband ambiguity checks below."
---

# Skill 57 research for audio spatial localization

## Summary

**Task outcome:** COMPLETE

Start with a synchronized array and declare its coordinate
system. Estimate physically supported microphone-pair delays
and compare them with a near- or far-field propagation model.
A single pair can support several directions or positions.
Use additional independent geometry and report competing results.
[Grinstein et al. (2024), sections 2–3](https://link.springer.com/article/10.1186/s13636-024-00377-z)

## Evidence

### Declare the propagation and clock model

Record microphone coordinates $\mathbf r_i$ in metres,
channel IDs, sample rate, tap, epoch, and relative channel
timing corrections. Define the position $\mathbf s$ and
the array axes. In a homogeneous medium with stated sound
speed $c$, the modeled delay of receiver $j$ relative to
receiver $i$ is

$$
\tau_{ij}=\frac{\|\mathbf s-\mathbf r_j\|-
                    \|\mathbf s-\mathbf r_i\|}{c}.
$$

A positive value means receiver $j$ is later. The absolute
delay bound is $\|\mathbf r_j-\mathbf r_i\|/c$ from the
triangle inequality. Use a clock calibration or reference
stimulus before treating a channel offset as propagation.
Allow a declared margin for geometry, clock and estimation
uncertainty. Flag delays outside that margin. Keep the
nominal speed and its justification with the measurement.
[Sample clocks](../../../../../skills/audio-timebase-sync/SKILL.md) ·
[Signed lag convention](../../../../../skills/audio-cross-correlation/references/CROSS_CORRELATION_CONTRACT.md#clock-and-lag)

For a distant source, use the direction $\hat{\mathbf s}$
from the array toward it and
$\tau_{ij}\approx-(\mathbf r_j-\mathbf r_i)\cdot\hat{\mathbf s}/c$.
For a two-element array along $+x$, define $\theta$ from
broadside toward $+x$. Then $\tau_{ij}=-(d/c)\sin\theta$
in the far-field approximation. This resolves a directional
projection. In two dimensions a source on either side of
the array line can share it. In three dimensions more
directions may share it. Close sources require the distance
model when the approximation is too coarse for the task.

### Check evidence before assigning a location

Use linear cross-correlation with a stated physical lag range
and common observation support. With cross-spectrum $X_i^*X_j$,
PHAT weights the retained bins by the inverse magnitude before
transforming them to a lag curve. Define the gate for quiet
or unreliable bins, and keep the unweighted comparison.
A narrowband or repeated signal can yield several valid
peaks. Near endfire, a small delay error can yield a large
angle error because the projection changes slowly there.
[Knapp and Carter (1976)](https://doi.org/10.1109/TASSP.1976.1162830) ·
[GCC-PHAT review](https://link.springer.com/article/10.1186/s13636-024-00377-z)

For an array, a bounded steered-response check evaluates
each candidate position or direction using the corresponding
delay on each qualified pair. Sum the pair scores with
declared weights and interpolation. Return the search region,
grid spacing, used pairs and competing peaks. Check the
residual delays and pair closure where useful. A consistent
reflection can satisfy multiple pairs. Compare a known source
and include a second geometry or reference when the result is
ambiguous. Angles or positions need accuracy evidence beyond
grid spacing and score magnitude.

### Executed checks and portable fixtures

| Probe | Verified result |
| --- | --- |
| For a 0.20 m pair use $c=343$ m/s, 48 kHz and a far-field source 30° toward $+x$. Compare the rounded delay with a 128-sample fixture containing `[1,-1,1,1,-1,-1,1]` starting at 55 on $i$ and 41 on $j$. | The formula gives −13.994169 samples. The direct correlation picks lag −14, corresponding to 30.013784°. The physical interval is approximately ±27.988338 samples. Lag +29 exceeds that interval even with a half-sample margin. |
| Place two receivers at $(−0.3,0)$ and $(0.3,0)$ m. Try sources at $(0,0.4)$ and $(0,−0.4)$ m. Add a third receiver at $(0,0.15)$ m. | Both original receivers are 0.5 m from either source. The third is at distances 0.25 and 0.55 m respectively. Its delay relative to the first distinguishes the mirror points in this model. |
| At 48 kHz compare phase for a 4 kHz tone with a −14-sample delay. List phase-equivalent integer delays within the 0.20 m physical interval. | The equally supported phase lags are `[-26,-14,-2,10,22]`. Broadband timing or additional evidence is required to choose among them. |

The checks exercise geometry and signed timing. A reverberant
room, several sources, or independent hardware clocks require
their own accuracy checks.

## Next action

Implement a bounded pair-delay and geometry baseline. Keep
unsupported, ambiguous and resolved states. Compare a known
direction, mirror points, narrowband ambiguity, channel
swap and a sample-clock mismatch. Check a real array at
several known positions before using confidence thresholds.

## Revisit when

The array geometry, channel timing, propagation model,
frequency bands, search grid, or evidence model changes.
