---
name: audio-sample-formats
description: Decode, encode and audit raw PCM integer and IEEE floating sample formats, byte order, valid-bit widths, planar and interleaved channel storage, normalization, saturation and quantization without silently reinterpreting or calibrating the signal.
---

# Audio sample formats — the bytes are part of the measurement

## Activate when

Use for PCM representations, raw data conversion, bit depth, signedness, byte order, 24-bit packing, WAVE valid-bit alignment, float headroom, and per-channel packing. Use [audio-sample-peak](../audio-sample-peak/SKILL.md) for peak measurements, [audio-timebase-sync](../audio-timebase-sync/SKILL.md) for frame timestamps, and [audio-dsp-test-fixtures](../audio-dsp-test-fixtures/SKILL.md) for validation vectors. Consult [math-numerical-analysis](../math-numerical-analysis/SKILL.md) when rounding/finite precision requires attention; leave domain calibration with audio, not generic math.

Read [the bounded PCM reference contract](references/PCM_FORMAT_CONTRACT.md) before coding.

## Procedure

1. **Identify the representation before reading bytes.** A raw PCM buffer is not a WAVE/AIFF header or codec frame. Specify actual file/codec family, container width, valid bits, signedness, byte order, channel count/labels, interleaved or planar layout, frame count, sample rate, signal tap and any prior gain/normalization. A channel count without a channel mask does not identify speaker locations.
2. **Decode integers correctly.** In ordinary WAVE PCM, u8 is unsigned with digital zero at code 128; signed 16-bit and higher use two's complement. Properly sign-extend packed 24-bit values. Explicitly interpret the endianness of the raw container rather than assuming that FFmpeg's native-endian in-memory types describe every file byte order.
3. **Separate valid bits from container size.** WAVEFORMATEXTENSIBLE may store 20 valid bits left-aligned in 24- or 32-bit byte-aligned containers. The reference checks the unused low bits are zero; this is an explicit strict policy consistent with Microsoft guidance. For corrupted or alternate packing, reject rather than silently inventing precision.
4. **State the normalization denominator.** For signed B-bit PCM, use x=q/2^(B-1): negative full scale maps exactly to -1 and positive maximum to 1-2^-(B-1). For u8, x=(u-128)/128. Do not claim both extrema have magnitude 1 or assume another application's positive-end convention is identical.
5. **Preserve float data honestly.** IEEE f32/f64 may contain valid finite samples outside [-1,1] before integer conversion/limiting. A >1 reading is not automatic proof of clipping. Validate NaN/Infinity and binary32 overflow; preserve negative zero and flag tiny nonzero values rounded to zero where relevant.
6. **Choose output quantization policy explicitly.** This oracle encodes normalized integer PCM with nearest/ties-to-even at the specified 2^(B-1) scale and either saturates nonrepresentable codes or fails. +1.0 requires saturation under this signed scale; -1.0 is exact. Never mistake code-range saturation for proven ADC overload. There is no dither, noise shaping, resampling or limiter; production bit-depth reduction may require separate audio engineering.
7. **Keep channels independent.** Interleaved frame storage alternates channel samples; planar storage has separate contiguous planes. Do not silently reorder, sum or downmix channels, particularly anti-phase channels. Preserve labels/masks as provenance without guessing absent speaker assignments.
8. **Verify byte-level fixtures.** Run the [reference converter](scripts/reference_pcm.py) and [regression tests](../../tests/test_audio_sample_formats_reference.py). Check u8 center, signed endpoint asymmetry, s24 little/big sign extension, 20-in-24 left justification, malformed padding, float headroom, quantization ties, exact channel packing and independent Python struct/wave byte checks. Run the Kestrel full suite and structural validator; distinguish executed tests from broader file/codec/device compatibility.

## Acceptance gate

A converted signal declares the kind, sample width, valid bits, reference scale, byte order, frame count, channel layout/identity, float-invalid policy, and any quantization or clipping decisions. Sample timestamps and channel identities must not disappear in a production pipeline merely because sample storage changed. The bounded pure-standard-library oracle does **not** parse WAVE metadata, perform real-time processing, certify AES17/ITU, or implement device/codec integration.

## Authoritative sources

- [Microsoft WAV PCM byte representation](https://learn.microsoft.com/en-us/windows/win32/multimedia/devices-and-data-types) — u8 and s16 sample values.
- [Microsoft WAVEFORMATEXTENSIBLE](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ksmedia/ns-ksmedia-waveformatextensible) — valid bits, container bits, left justification and channel masks.
- [FFmpeg sample formats](https://ffmpeg.org/doxygen/trunk/group__lavu__sampfmts.html) — native-endian decoded samples, planar/packed and float values above nominal full volume.
- [libsndfile conversion notes](https://github.com/libsndfile/libsndfile/blob/master/docs/api.md) — conversions depend on selected API normalization policy.
