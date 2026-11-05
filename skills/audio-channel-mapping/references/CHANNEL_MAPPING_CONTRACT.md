# Explicit audio channel identity and matrix-routing contract

Companion to [audio-channel-mapping](../SKILL.md). This is a small scientific oracle, not a loudspeaker standard converter, surround decoder, DAW mixer, codec or realtime renderer.

## Representation and authority

The reference [source](../scripts/reference_channel_mapping.py) supports at most 8 simultaneous channels and 256 frames per call. Each `ChannelLayout(labels, kind)` records exact ordered identities (no duplicate names) with one of three *different* kinds:

- `speaker`: a subset of Microsoft's 18 standard WAVE speaker labels; no speaker order is inferred from array length.
- `discrete`: named channels `CH0`, `CH1`, ... with **unknown physical position**. Assigning to known speakers requires explicit acknowledgment, *not* a guess from the count.
- `mid_side`: exactly (`M`,`S`) using the stated amplitude-normalized stereo representation. These are *signals*, not speaker locations.

`from_wave_mask(mask, channels)` interprets only recognized Microsoft bits and lists their channels by increasing bit significance. Unlike permissive media APIs, this bounded strict oracle rejects masks whose populated bit count differs from the declared number of channels, rejects reserved/unknown bits, and requires `allow_unassigned=True` for zero mask to become count-only `CH0` etc. This is a **validation choice**; Microsoft documents cases where bit counts and channel counts differ, but that permissiveness is not silently implemented here. For a source format that uses custom order, e.g. FFmpeg's custom AVChannelLayout, obtain an explicit ordered layout and map its conventions yourself. A WAVE count of 2 with no mask is *not* necessarily FL/FR. Different 5.1 masks: `0x3F` = FL FR FC LFE BL BR and `0x60F` = FL FR FC LFE SL SR.

## Exact matrix definition

For input `x[source][frame]`, output `y[destination][frame]`:

`y_i(k) = sum_j A_ij * x_j(k)`

with `A[dst][src]` a declared matrix of exact Python `Fraction` or integer coefficients. Floating-point coefficient literals are refused; the builder must choose rational values explicitly. Applied sample arithmetic uses binary64 and `math.fsum` where mixing is required; this does **not** mean the result has exact real precision or physically correct loudness. Identity/reordering one-to-one unit routes copy samples directly to retain signed zero and exact byte-convertible amplitudes.

The linear map never resamples or filters time, so input and output sample clock share exact `epoch_id`, `start_sample`, `end_sample_exclusive`, and frame count. A source sample over ±1 can remain so after mapping; no limiter, automatic level scaling, dither or quantization is performed.

**Opt-in guards** (no unannounced policy):

- `allow_drop` is required when any input column is all zero; report those labels explicitly, especially LFE.
- `allow_silent_outputs` is required when any destination row is all zero; report these labels, without claiming meaningful upmix content.
- `allow_possible_peak_gain` is required when any destination row has `sum_j |A_ij| > 1`. This row sum is a *worst-case coherent amplitude gain factor* relative to bounded source amplitudes. Gain can be higher for deliberately correlated channels even when individual channels are within unity. It is **not** a loudness target, measured clipping, or an automatic normalization recipe.
- `acknowledge_discrete_to_speaker` is required when assigning physically unlabelled discrete source channels to any non-discrete target; the caller must know what each source actually means outside this oracle.

Compute exact rational matrix rank. `rank < source_channel_count` indicates the linear transform cannot be inverted for arbitrary input frames. Even a full-column-rank linear map need not be an acoustically reversible speaker renderer; duplication does not add source information, and physical speaker positioning is not represented by sample values.

## Test-case expectations

| Fixture | Independent interpretation |
| --- | --- |
| WAVE bitmask `0x3`, 2 channels | FL, FR; mask 0 requires explicit unassigned policy |
| WAVE `0x3F` vs `0x60F`, 6 channels | rear BL/BR versus side SL/SR must not be conflated |
| FL/FR stereo swap | permutation rows (0,1), (1,0); preserve sign, time, and amplitudes |
| Stereo downmix to a single FC example | rows (1/2,1/2); antiphase L=1,R=-1 gives 0. Linear rank=1, **irreversible** |
| M/S encode | M=(L+R)/2; S=(L-R)/2. L=R=1 yields M=1,S=0; L=-R=1 yields M=0,S=1 |
| M/S inverse | L=M+S, R=M-S, row coherent gain 2 requiring explicit acknowledgment |
| Manual 5.1 rear downmix (example **not normative**) | yL=FL+0.5 FC+0.5 BL; yR=FR+0.5 FC+0.5 BR; LFE is consciously discarded, coherent gain bound 2 per row |
| Stereo to 5.1 without spatial synthesis | FL and FR copied, other outputs explicitly **silent** after acknowledgment |
| 0.8+0.7 coherent mono sum with unit coefficients | 1.5, never silently clamp; one over-reference output |
| Invalid audio, gaps, matrix shape, unacknowledged loss, numeric overflow | Explicit rejection with no accepted streaming cursor advance |
| Chunk schedules over origin above 2^53 | Identical emitted per-channel frames and exact input/output sample coordinates |

[The regression suite](../../../tests/test_audio_channel_mapping_reference.py) exercises 24 independent analytic and negative cases, including a cross-skill raw PCM pack/unpack fixture. Analytic rational matrix expectations and fixed known WAVE mask values are independent of the implementation's Gaussian-elimination helper. These checks are not a complete externally audited Microsoft/FFmpeg decoding implementation or a certified loudspeaker decoder.

## Stream epochs and interfaces

`ChannelMapStream` retains the current `ChannelMatrix`, a never-reused epoch ID, and the exact next integer sample coordinate. A `push(start_sample, planes)` accepts only contiguous blocks; it validates and renders **before** advancing the stream cursor. A layout/gain/rate/seek discontinuity requires an explicit new epoch and plan via `reset_epoch`. A silent recording pause with no input has no effect on the cursor. This reference does not detect an upstream dropout when the provider falsely supplies contiguous sample indices.

This oracle accepts planar float channel samples and assumes the sample rate is unchanged; PCM packing, arbitrary channel masks, resampling, clock drift and audible loudspeaker latency belong to other modules. Production paths must keep channel mask and history metadata alongside the samples and use a controlled output device calibration. A nonnormative matrix is not made normative by passing unit tests.

## Open risks and future skills

Stereo/binaural/ambisonic/height/bass-management algorithms, LFE low-pass/subwoofer routing, time-delay alignment, unknown-order container adaptation, energy versus amplitude normalization, and loudness-weighted downmix need further engineering and documentation. For actual rendering, separately validate standards edition, frequency-dependent routing, gain, delay, device channel enumeration, visual peak/clipping semantics and audio content; no physical speakers are exercised here.

Sources: [Microsoft WAVEFORMATEXTENSIBLE](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ksmedia/ns-ksmedia-waveformatextensible), [FFmpeg AVChannelLayout](https://ffmpeg.org/doxygen/trunk/structAVChannelLayout.html), [ITU-R BS.775-4](https://www.itu.int/rec/R-REC-BS.775/), [ITU-R BS.2051-3](https://www.itu.int/rec/R-REC-BS.2051/en).
