---
schema: 1
id: 2026-11-26-audio-offline-analysis-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-26
updated: 2026-11-26
sources: "Audio branch a435c790546b7aefc8ba35ba18be1d7c235f916f; SciPy linear convolution and forward-backward filter documentation; executed chunk, tail, crop, phase and reduction checks with NumPy 2.3.5 and SciPy 1.17.0."
---

# Skill 73 research for offline analysis

## Summary

**Task outcome:** COMPLETE

Analyze a declared decoded record with explicit history,
output support, and reduction. A chunk boundary can be
invisible to the measurement when state and output
ownership are correct. A forward-backward filter changes
the response and can produce output before a transient.
[SciPy overlap-add convolution](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.oaconvolve.html) ·
[SciPy forward-backward filtering](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.filtfilt.html)

## Evidence

### Define the record and execution policy

Record the input identity, decoder and analysis versions,
channel order, sample rate, trim rule, tap, time origin
and requested interval. Treat whole-record selection and
a cropped read of a whole-record result as distinct
support policies. Supply the history or lookahead needed
by the whole-record policy. Account for decoder priming
and explicit gaps. Declare padding at actual edges and
keep padded samples distinguishable from observations.
[Codec alignment and trim](2026-11-26-audio-codec-artifacts-research-r01.md) ·
[Analysis provenance](../../../../../skills/audio-analysis-provenance/references/PROVENANCE_CONTRACT.md)

Preserve causal filter state across blocks. For an FIR
with $M$ taps, save the preceding $M-1$ samples or use
an equivalent convolution rule. In overlap-add, compute
each block's linear convolution, using FFT length at
least its sample count plus $M-1$. Add each partial
result at the block's absolute position. Retain the
overlapped sums and apply any tail trim at the declared
record end. Assign each emitted output sample or frame
to one block. For framed analysis keep the frame grid
anchored to the record, including across resumed work.
[Linear convolution output sizes](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.fftconvolve.html) ·
[STFT frame geometry](../../../../../skills/audio-spectrogram-waterfall/references/STFT_WATERFALL_CONTRACT.md#frame-geometry)

Use mergeable sufficient statistics where the method
permits it. For RMS, sum valid squared samples and
counts before dividing and taking the square root.
For an operation with a global gate or percentile,
preserve the state or evidence needed by the global
method. Verify the error budget across partitions and
merge orders. If supporting restart, identify state by
the input, configuration and absolute output ranges.
Verify a resumed run against a continuous run, including
output completeness and duplicate handling.
[Reference validation](2026-11-26-audio-reference-validation-research-r01.md)

An offline method can use future samples, explicit edge
extension or multiple passes. For a forward-backward
filter, declare the resulting response and edge rule.
If the task needs comparability with streaming, keep
a mode with equivalent causal method and support.
[SciPy forward-backward filtering](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.filtfilt.html) ·
[Real-time integration](2026-11-26-audio-realtime-integration-research-r01.md)

### Executed checks and portable fixtures

Use input `[0,0,1,0,0,0,0,2]`, a causal FIR
`[1,0.5,0.25]`, and zeros outside the input record.
Adopt full convolution support, including the two
output samples after the last input sample.

| Probe | Verified result |
| --- | --- |
| Compare direct convolution with causal blocks `[0,3)`, `[3,7)` and `[7,8)`, keeping two history samples and flushing two zeros at the end. | Both give `[0,0,1,0.5,0.25,0,0,2,1,0.5]` at ticks 0 through 9. |
| Run overlap-add on that partition, on single-sample blocks, and on the whole record. | All three agree with the direct result within `1e-12` amplitude units. |
| Reset history at each block and flush the last tail only. Inspect output ticks 3 and 4. | Both become 0. The same coordinates in the whole-record output are 0.5 and 0.25. A fresh isolated computation of input `[3,5)` also lacks the impulse at tick 2. |
| Use a 32-sample record with a unit impulse at tick 10 and zeros elsewhere. Compare one causal pass of FIR `[1,0.5]` with a forward-backward pass with no padding. | The causal nonzero support is ticks 10 and 11. The forward-backward support is ticks 9 through 11 with values `[0.5,1.25,0.5]`. |
| Combine a block containing a single 1 with a block of nine zeros. | Pooled RMS is $\sqrt{1/10}\approx0.316228$. The unweighted mean of the two block RMS values is 0.5. |

These fixtures check the specified finite records. Give
stateful filters, framing, and global statistics their
own support and edge tests for the intended inputs.

## Next action

Give Gauge whole-record, varied partition, cropped,
and resumed cases with impulses near each boundary.
Check both crop policies and explicit EOF handling.
Compare the exact ranges and aggregate results on the
declared sample clock.

## Revisit when

The decoder, trim, sample clock, boundary policy,
algorithm, reducer, or restart mechanism changes.
