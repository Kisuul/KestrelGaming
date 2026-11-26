---
schema: 1
id: 2026-11-26-audio-room-acoustics-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-26
updated: 2026-11-26
sources: "Audio branch 3d65d0ddb88fead8d8a067e6abb8877ae5609d7b; ISO 3382-1 and 3382-2 catalogues, Schroeder decay method via REW, REW room decay documentation; executed decay, noise-floor and clarity fixtures below."
---

# Skill 55 research for room acoustics

## Summary

**Task outcome:** COMPLETE

Measure room behavior from qualified, band-limited room impulse
responses. Record the source and receiver geometry. Estimate
decay from a declared level range with enough usable data.
Keep different decay slopes and inadequate dynamic range
visible. The fixtures include a known straight decay, a
two-slope decay, a noise-floor bias, and a clarity split.
[Room impulse response research](2026-11-26-audio-impulse-response-research-r01.md) ·
[ISO 3382-1:2009 scope](https://www.iso.org/standard/40979.html) ·
[ISO 3382-2:2008 scope](https://www.iso.org/standard/36201.html)

## Evidence

### Fix the geometry and analysis support

Record source and receiver positions, orientations, measurement
band, rate, environment, levels, and the selected direct-arrival
time. Keep one result per position and band before pooling.
Changes of speaker directivity, excitation, furniture or
receiver position can change the evidence. In a small room,
inspect low-frequency modes and local decay curves separately
when spatial mixing is weak. A pooled scalar can hide positions
with a different response. Keep the complete usable tail for
the room question and a shorter analysis only for a stated
different objective.
[REW decay measurement guidance](https://www.roomeqwizard.com/help/help/html/graph_rt60.html)

### Integrate the decay and qualify each fit

For the band-filtered impulse response $h_b[n]$ starting at
the chosen arrival, compute the reverse sum
$E[n]=\sum_{k=n}^{N-1}h_b[k]^2$ over a declared tail.
Use $D[n]=10\log_{10}(E[n]/E[0])$ when energy is positive.
Use time in seconds for fitting and record the actual window
and noise treatment. A clean exponential energy decay has a
constant dB slope. For a negative fitted slope $m$ in dB/s,
the time extrapolated to a 60 dB drop is $-60/m$.

| Measure | Fit range relative to the starting energy |
| --- | --- |
| EDT | 0 to −10 dB |
| T20 | −5 to −25 dB |
| T30 | −5 to −35 dB |

Freeze the inclusive ranges and fitting rule for the reference.
Check the floor, usable decay range, fit residual or curvature,
and quality of the input response before returning a fit.
For noise handling, estimate background from genuinely
noise-dominated support or a separate observation under the
same conditions. Report the truncation or correction and see
how the fit changes when it changes. An integrated noise tail
can give a long apparent decay even with a precise regression.
Mark a fit unavailable if the needed range falls into noise
or outside the observed support.
[REW decay ranges and interpretation](https://www.roomeqwizard.com/help/help/html/graph_rt60.html)

### Measure early and late energy for the stated arrival

For clarity $C_{t_c}$ use $10\log_{10}(E_{\mathrm{early}}/
E_{\mathrm{late}})$ with a cutoff $t_c$ relative to the selected
arrival. For the bounded sampled fixture, energy strictly earlier
than the cutoff is early. A sample at the cutoff is late.
For $D_{50}$ report early energy divided by total energy up to
the usable end, with fraction or percent declared. Check
insufficient tail, zero energy and zero late-energy states.
Record the filter delay and how the arrival time was aligned.
[REW clarity and definition](https://www.roomeqwizard.com/help/help/html/graph_rt60.html)

### Executed checks and portable fixtures

For the first three probes set $t=n/1000$ s for $0\le n<2400$.
Use the listed expressions as the already band-limited squared
values for the arithmetic test. Fit the inclusive dB ranges
above by ordinary least squares with equal sample weights.

| Probe | Verified result |
| --- | --- |
| Use $10^{-6t/0.60}$. | EDT, T20 and T30 all give 0.600 s within `1e-12` seconds. |
| Use $10^{-6t/0.30}+0.04\cdot10^{-6t/0.90}$. | EDT is 0.355469 s, T20 is 0.634134 s, and T30 is 0.764818 s. They summarize different parts of one curve. |
| Add a constant squared floor of 0.0001 to the first probe. Fit without a floor check. | The numbers become about 0.612, 4.683 and 9.126 s. The T30 calculation overstates the known decay time by more than a factor of 15. |
| At 1 kHz put taps 1, 0.5 and 0.5 at time indices 0, 79 and 80 in a 150-sample response. Use an 80 ms cutoff. | Early and late energies are 1.25 and 0.25 in squared response units. The exact ratio 5 gives $C_{80}=6.989700$ dB. |

These checks verify decay arithmetic and expose bias under
specified synthetic conditions. Actual room repeatability,
spatial coverage, filter behavior and ISO conformance need
their own measurements.

## Next action

Implement the bounded backwards-energy and fit procedure with
band, position, floor and quality metadata. Give Gauge a
two-slope curve, a contaminated tail, and a shifted arrival.
Check what changes across receiver positions before deriving
a room-level conclusion.

## Revisit when

The room condition, geometry, frequency band, arrival estimate,
noise treatment, fit range, or reported metric changes.
