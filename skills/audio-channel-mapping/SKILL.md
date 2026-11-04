---
name: audio-channel-mapping
description: Identify, validate and transform audio channels using explicit speaker/discrete/Mid-Side semantics, WAVE speaker masks, rational routing matrices, conservative headroom and information-loss diagnostics, and independently verified channel/time fixtures.
---

# Audio channel mapping — label the channels before mixing them

## Activate when

Use for channel order or identity, WAVE speaker masks, planar routing, stereo or surround conversion, LFE policy, stereo swap, Mid/Side analysis, multichannel downmix or upmix, and diagnosing cancellation due to misrouted channels. Read [the channel routing contract](references/CHANNEL_MAPPING_CONTRACT.md) before accepting a channel remapping instruction.

Consult [audio-sample-formats](../audio-sample-formats/SKILL.md) for decoded PCM and planar/interleaved representation, [audio-timebase-sync](../audio-timebase-sync/SKILL.md) for stream continuity and origin, [audio-resampling](../audio-resampling/SKILL.md) only when different sample rates are involved, [math-linear-algebra](../math-linear-algebra/SKILL.md) for matrix composition and rank, and [math-numerical-analysis](../math-numerical-analysis/SKILL.md) for cancellation and overflow. Use [math-verification](../math-verification/SKILL.md) for independent numerical test policy. Do not load the whole math core routinely.

## Engineering procedure

1. **Determine what each channel means.** Distinguish a speaker position (FL, FR, FC, LFE, BL, BR, SL, SR, etc.), a discrete/unassigned PCM channel with no known speaker, and Mid/Side *signals* M and S. A two-channel buffer is not inherently stereo FL/FR; it can be dual mono, unspecified, binaural or unrelated signals. Decode the actual file/stream metadata first. Never invent channel assignments from channel count.
2. **Interpret layout specifications precisely.** Microsoft WAVEFORMATEXTENSIBLE `dwChannelMask` enumerates speaker bits in ascending bit order. `0x3F` encodes FL, FR, FC, LFE, BL, BR; `0x60F` encodes FL, FR, FC, LFE, SL, SR. They are not equivalent 5.1 layouts. Mask=0 carries no speaker identity. FFmpeg `AVChannelLayout` distinguishes unspecified, native and custom channel orders. Do not assume WAVE mask ordering is every codec's or platform's ordering.
3. **Require an explicit routing matrix.** Define `y_dst[k] = Σ_src A[dst,src]·x_src[k]`, with each coefficient and source/destination ordering declared. This bounded oracle accepts exact rational coefficients (integers or `Fraction`) to keep normative claims out of floating literal guessing. Different systems and standards may use different coefficients, normalization and gain management. A suggested half-gain center/rear fixture is **not** a standards-approved universal downmix recipe.
4. **Check the map before processing.** Reject wrong matrix dimensions, unknown speaker IDs, nonfinite or ambiguous data, unacknowledged discarded source channels, unacknowledged silent outputs, unacknowledged unknown-to-speaker assignments and any output row whose sum of absolute gains exceeds 1 **without an explicit headroom acknowledgment**. The row sum bounds worst-case coherent output for magnitude-bounded source samples; it is not expected loudness or perceptual balance. Count exact matrix rank to reveal irreversibility when rank < number of source channels. Do not use a rank test to imply psychoacoustic reversibility.
5. **Treat special channels honestly.** LFE is a distinct effects channel: it must not automatically be discarded, copied to both main channels, filtered or bass-managed by a generic matrix. Side/rear and height speaker locations are not interchangeable. The reference has no normative 5.1-to-stereo preset, binaural renderer, ambisonic transform, delay compensation or HRTF. Upmixing to extra speakers does not create genuine spatial information; silence must be an acknowledged output, not a claimed synthesis.
6. **Keep Mid/Side separate from speaker geometry.** Here `M=(L+R)/2` and `S=(L-R)/2` with exact rational half-gains. The inverse is `L=M+S` and `R=M-S` and requires an explicit possible-peak-gain acknowledgment. M/S is a reversible representation transform for aligned channels, not surround virtualization. Anti-phase stereo becomes a pure Side component and can cancel in an ordinary mono downmix; do not hide this under RMS/peak measurements.
7. **Preserve sample clocks and amplitude history.** A memoryless channel matrix maps one input frame to exactly one output frame at the same sample rate and integer sample coordinate. It must not reset stream time, invent samples, resample, quantize, normalize levels, or silently clamp values above ±1. Return any output-over-reference indicators and dropped/silent channel labels; neither counter establishes upstream clipping or true-peak compliance. Handle gaps, overlaps, seek/rate/layout reconfiguration by new unique epochs.
8. **Verify independently and adversarially.** Run [the bounded reference](scripts/reference_channel_mapping.py) and [24 regression tests](../../tests/test_audio_channel_mapping_reference.py). Cases include WAVE masks and 5.1 side-versus-back, exact raw PCM byte interop, a known stereo swap, mono anti-phase collapse, M/S exact roundtrip, explicit nonnormative 5.1 coefficients, LFE discard, strict loss/headroom acknowledgment, output above unity without clipping, large absolute sample origins, fragmented callbacks, overflow and atomic reset errors. These establish the stated tiny oracle's behavior, not host/channel-device correctness.
9. **Make production acceptance contextual.** For a real rendering system, test speaker calibration and gain, channel names from its container/API, actual downmix/height/LFE policy, phase and delay, limiter/PCM stage and perceptual performance. Cite the specific revision of any normative document and do not assume this skill itself implements every standard.

## Verification commands

```sh
python3 tools/validate_seed.py
python3 -m unittest discover -s tests -v
git diff --check
```

The reference uses only Python's standard library and accepts at most **8 channels and 256 frames per block**. Tests run inside the Kestrel repository, not an actual audio playback/device endpoint.

## Acceptance gate

Require declared source/target channel kinds, channel identities and ordering; actual routing/gain matrix, gain/clip/discard policy, LFE and non-speaker semantics, sample-rate/epoch continuity, test evidence and unverified limits. **Do not claim a stereo layout from a raw two-channel count**, or a standardized downmix when only example coefficients have been tested.

## Authoritative sources

- [Microsoft WAVEFORMATEXTENSIBLE channel mask and ordering](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ksmedia/ns-ksmedia-waveformatextensible) — source speaker bits and strict verification implications.
- [FFmpeg AVChannelLayout reference](https://ffmpeg.org/doxygen/trunk/structAVChannelLayout.html) — native, custom, and unspecified channel representations.
- [ITU-R BS.775-4 (2022)](https://www.itu.int/rec/R-REC-BS.775/) — multichannel stereophonic system context; **not** a claim our coefficients implement that specification.
- [ITU-R BS.2051-3 (2022)](https://www.itu.int/rec/R-REC-BS.2051/en) — advanced loudspeaker programmes and layouts; not implemented by this bounded oracle.
