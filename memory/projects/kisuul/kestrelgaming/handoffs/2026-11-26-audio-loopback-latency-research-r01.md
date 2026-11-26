---
schema: 1
id: 2026-11-26-audio-loopback-latency-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-26
updated: 2026-11-26
sources: "Audio branch 3d65d0ddb88fead8d8a067e6abb8877ae5609d7b; Android AOSP round-trip measurement, PortAudio callback time contract, W3C Web Audio timestamp mapping, Kestrel cross-correlation and timebase; executed synthetic arrival and drift fixtures below."
---

# Skill 59 research for loopback latency

## Summary

**Task outcome:** COMPLETE

Name the start and end of the latency measurement. Send a
distinctive signal through the actual route and recover its
position on a common clock. Keep the first credible arrival,
strongest peak and drift as separate measurements. The fixtures
exercise capture origins, a stronger echo and an independent
sample clock rate.
[Android AOSP round-trip method](https://source.android.com/docs/core/audio/latency/measure)

## Evidence

### Establish the path and timebase

State whether the path includes application buffering, driver,
converter, mixer, processing, acoustic propagation, and capture
delivery. Record the device and stream settings, requested and
observed block sizes, rate, timestamp source, and complete support.
An electrical and an acoustic loopback include different
components. A round-trip measurement combines the delays
between the defined taps. To attribute input and output
portions separately, collect independent timing evidence.

PortAudio exposes timestamps for the first input sample at
the ADC, callback invocation, and the first output sample
at the DAC. Interpret these fields on the associated stream
clock. Web Audio's output timestamp gives a mapping between
context time and estimated performance time for output. Use
the correct anchor for the intended end points and verify
the mapping. The number of frames in a buffer gives a nominal
duration. End-to-end latency includes the other contributing
stages and delays.
[PortAudio callback time fields](https://portaudio.com/docs/v19-doxydocs/structPaStreamCallbackTimeInfo.html) ·
[W3C output timestamp](https://www.w3.org/TR/webaudio/#dom-audiocontext-getoutputtimestamp) ·
[Timebase contract](../../../../../skills/audio-timebase-sync/references/TIMEBASE_CONTRACT.md)

### Select and qualify the arrival

Use a known probe with distinctive time structure, guard
intervals, and a recoverable broadband signal. Retain the
realized reference and response. Set a feasible delay range
and inspect competing peaks and their signs. The chosen arrival
may be the first credible detection, a peak used for alignment,
or another named quantity. Check noise and sidelobes before
selecting an earlier peak. Repeat with a changed probe or
geometry to distinguish an echo from the desired path.

With shared-rate sample coordinates and capture starts $s_x$
and $s_y$, pair $x[n]$ with $y[n+\ell]$. The clock delay is
$s_y-s_x+\ell$ samples. Divide by the actual sample rate to
obtain seconds. For a different timebase, first map both
positions to a common clock. Keep integer or rational coordinates
before the final display conversion. Record gaps, coverage and
any known resampling delay.
[Cross-correlation clock and lag](../../../../../skills/audio-cross-correlation/references/CROSS_CORRELATION_CONTRACT.md#clock-and-lag) ·
[Impulse response research](2026-11-26-audio-impulse-response-research-r01.md)

### Check repeatability and clock drift

For repeated probes in one stable regime, compare the difference
between paired times and the residuals of a clock model.
For separate output and input sample counts, an affine model
$n_{\mathrm{in}}=a n_{\mathrm{out}}+b$ can describe constant
rate ratio and offset. A fitted intercept includes time origins
and path delay. To name part of that intercept as absolute
latency, use independent anchors. A changing queue, clock
reset, concealed samples, or rate changes can break an affine
fit. Inspect residuals and verify clock behavior before
attributing a delay trend to hardware drift.

Report the route, observation count, distribution and
conditions. Distinguish cold start from steady operation and
report failures or timeouts with their occurrence rate.
For a live UI or control claim, measure the same endpoint
that the claim names.
[Stream buffering](../../../../../skills/audio-stream-buffering/SKILL.md) ·
[Temporal fusion research](2026-11-26-audio-temporal-fusion-research-r01.md)

### Executed checks and portable fixtures

For the first two rows use a common 48 kHz clock with
$s_x=2^{60}+37$ and $s_y=s_x+120$. The 128-sample reference
has the probe `[1,-1,1,1,-1,-1,-1,1]` at local index 40.
The 1,500-sample response has copies scaled by 0.25 and 0.8
at local indices 1,107 and 1,240. Other samples are zero.

| Probe | Verified result |
| --- | --- |
| Compare the two known arrivals on the shared clock. | Local lags are 1,067 and 1,200. Adding the capture-start offset gives 1,187 and 1,320 samples, about 24.729167 and 27.500000 ms. |
| Compute the direct and FFT linear correlations. | The raw scores at the known arrivals are 2.0 and 6.4. The latter is the global maximum. The two curves agree to about `7.2e-16` in product-sum units. |
| Pair send positions `[0,240000,480000]` with receive positions `[720,240732,480744]`. | The nominal sample differences are 720, 732 and 744. The exact affine slope is $20001/20000$, or +50 ppm relative to nominal, with intercept 720. The 24-sample difference across the test is 0.5 ms at 48 kHz. |

These results validate timing arithmetic and estimator behavior
on known signals. They leave device latency, timestamp accuracy,
clock drift in use and the physical path unmeasured.

## Next action

Implement an offline baseline with timed probe and arrival
records. Replay known offsets, echoes, repeats, drift and
clock resets. Use real acquisitions with an explicit route
before reporting typical latency or attributing it to a stage.

## Revisit when

The route, time mapping, clock, device profile, arrival rule,
buffering, or workload changes.
