# Rational sample-rate conversion: FIR, sample clocks and stream lifecycle

Companion to [audio-resampling](../SKILL.md). Consult [audio-timebase-sync](../../audio-timebase-sync/SKILL.md) for stream epochs and [math verification](../../math-verification/references/FIXTURE_POLICY.md) when evaluating oracle independence.

## Exact clock and output convention

For source rate F_s and destination rate F_d, both positive rational Hz, reduce F_d/F_s to L/M (coprime integers). An input epoch holds N contiguous sample **frames**, origin O_in, and C separate planar channels. The finite input interval is [0,N/F_s), not merely the timestamp span from its first to last sample.

- Output count: N_out=ceil(NL/M) (for N>0); this is a defined reference policy, not a general unbounded stream allocation rule.
- Output sample offset m ranges from 0 to N_out-1, with integer output coordinate O_out+m.
- Exact source-relative position of output m: p=mM/L source sample intervals; exact nominal time t=m/F_d seconds after origin.
- O_in+p is generally a *fractional* source coordinate and must not be silently rounded. O_out+m belongs to a different timebase from O_in+n. This reference's integer/fractional coordinates retain precision beyond 2^53.
- An output sample near the finite input's last interval can depend on zero extension, and output timestamp alignment does not mean exactly identical first-sample amplitude.

## Explicit filter and delay

The educational [FIR reference](../scripts/reference_resampling.py) uses Q=max(L,M), H=10Q, beta=5 and d=-H,...,H. On the zero-inserted intermediate sample grid at L·F_s:

`h_raw[d] = sinc(d/Q)/Q · I0(beta sqrt(1-(d/H)^2)) / I0(beta)`

with sinc(v)=sin(pi v)/(pi v) and sinc(0)=1. Normalize `h[d] = L h_raw[d]/sum(h_raw)`. The odd symmetric tap sequence has 2H+1 coefficients; the unfiltered L=M=1 case uses exact identity. The cutoff is 1/Q relative to intermediate-grid Nyquist, equivalent to the lower of input/output Nyquist frequency. Actual transition and stopband responses must be measured. Sum(h)=L is not a promise that **every individual phase** has exactly unity DC gain.

The centered sample formula is

`y[m] = sum_j x[j]·h[H + mM - jL]`

where terms outside the finite tap support are excluded. The oracle assumes zero for j outside [0,N), but only after the input epoch has been explicitly finalized. The causal-equivalent linear-phase FIR group delay is H intermediate-grid intervals, H/L source-sample intervals, or H/M destination periods. The returned **centered** output has no nominal timestamp shift but **requires future lookahead**, bounded by its full FIR support. Timestamp compensation is not physical buffering-latency elimination. The edge sample at m=0 can differ from x[0] even though both are labelled time zero.

For the limited tested 48→24 kHz case, a 256-frame 2 kHz sine retained RMS within 0.01 of 1/sqrt(2) in a central window, while 18 kHz was suppressed to RMS below 0.001. That is a **fixture-specific observation**, not an all-frequency error bound or a universal anti-alias specification. Identity, zero input, antiphase channels, near-boundary impulses and floating output above ±1 have distinct fixture expectations.

## Streaming, boundaries and state integrity

`StreamResampler(epoch_id, input_origin_sample, source_hz, destination_hz, channels, output_origin_sample=0)` preserves exact phase across contiguous `push()` input blocks. To publish output at offset m, its latest possibly contributing discrete input sample has index `floor((mM+H)/L)`. If that source index is not yet available, the output remains **withheld**—never padded as though a callback boundary were measured silence. Once stable, the output cannot be changed by future callbacks. The reference *stores every input frame* and recomputes from a bounded array for clarity; it is not a realtime circular-buffer implementation.

Only `finalize()` authorizes right-side zero extension, emits remaining output (if any), and marks the epoch closed. Each output group reports `output_start_sample`, `first_source_offset` (an exact Fraction), per-sample `boundary_affected`, and `finalized_tail`. A boundary flag means the complete discrete FIR support touches positions before first or after last **known sample** in this epoch. Flags are invariant under different chunk partitions; flagging a callback edge would be an error.

`push()` rejects gaps/overlaps, wrong channel count, nonfinite values, empty/unequal planes, output overflow and reference-size violations without modifying accepted state. `reset_epoch()` requires a never-used ID and reinitializes filter/rate/channel/output-origin state after validation. Neither a new epoch nor a no-op pause permits silently inserting absent samples. Real clock drift and transport timestamp jitter are outside the model.

## Acceptance matrix

| Claim | Check / reference | Evidence limitation |
| --- | --- | --- |
| Ratio & clock | Exact 44.1↔48 kHz ratios 160/147 and 147/160, ceil count and Fraction output clock | Not hardware drift |
| Coefficients | Odd symmetric FIR, sum(h)=L, impulse at documented location, interior DC tolerance | Not universal phase ripple bound |
| Anti-aliasing | 48→24 kHz 2k/18k tone pair, central RMS checks | Only tested signals and rate |
| Per-channel | Antiphase stereo, over-reference preservation | No channel speaker-mask interpretation |
| Stream state | Single-sample and irregular chunking equals offline output/flags, gap and overlap rejection | Bounded 256-frame epoch only |
| Delay & edges | Future-support withholding, explicit flush, per-sample boundary flags | Not measured real hardware latency |
| External vectors | Frozen NumPy 2.3.5 / SciPy 1.17.0 outputs for four ratios | Shared filter design family; no normative conformance |
| Optional comparison | Seeded SciPy differential over more lengths and channel arrangements | External dependencies, not ordinary CI |

See [SciPy golden provenance](../../../tests/fixtures/AUDIO_RESAMPLING_EXTERNAL_GOLDENS.md), [the 22 core tests](../../../tests/test_audio_resampling_reference.py), and [optional live comparison script](../scripts/check_scipy_resampling.py). Tolerances belong to those bounded input domains; they are not certified maximum-error claims. Production host acceptance needs a separate measured response/CPU/delay test, handling of dropped packets, device-time correlation, long-running phase and audible artifacts.

Limits: 1–256 source frames, ≤8 planar channels, ratio factors ≤320, ≤4096 output frames, finite float samples only, zero extension on finalized finite epochs. Neither file decoding nor sample-format quantization is performed.

References: [SciPy resample_poly](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.resample_poly.html); [SciPy upfirdn](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.upfirdn.html).
