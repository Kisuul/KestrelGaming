# Raw PCM sample format and numerical interpretation contract

Companion to [audio-sample-formats](../SKILL.md). See [math numerical analysis](../../math-numerical-analysis/SKILL.md) only for extra rounding/conditioning guidance.

## Bounded reference

The [standard-library oracle](../scripts/reference_pcm.py) supports raw `u8`, `s16`, packed `s24`, `s32`, IEEE `f32` and `f64`; explicit little/big endianness; planar/interleaved 1–8 channel data; and 1–256 complete audio **frames**. One frame consists of one sample per channel. No file headers, codec, channel mask parser or alignment/stride padding are processed. Channel labels are preserved if supplied, never invented or used to remix.

Signed PCM of B valid bits uses code range [-2^(B-1), 2^(B-1)-1] and the declared normalized mapping x=q/2^(B-1). The most negative value maps to -1; the greatest positive value is 1-2^-(B-1), **not 1**. For unsigned u8 only, x=(u-128)/128, with silence at 128 and positive maximum 127/128. Reference amplitude 1 is a scale convention, not proof of positive full-scale code or a calibrated physical level.

Under WAVEFORMATEXTENSIBLE, `wValidBitsPerSample` can differ from the byte-aligned container size. This oracle treats signed valid bits as **left-aligned** and requires unused lower container bits to be zero, choosing strict validation consistent with Microsoft's recommended value. For 20 valid bits inside signed 24-bit PCM, arithmetic shift right by four after sign extension yields the actual 20-bit code. Formats other than this described WAVE-style packing need their own handling.

## Encoding policy

For finite normalized input x, compute ideal code q=round_ties_even(x*2^(B-1)). In particular, +1 overflows the signed positive code range and -1 maps to its minimum. `integer_overflow=saturate` clips unrepresentable *codes* and increments per-channel saturation counts; `integer_overflow=error` rejects them. These counters differ from per-channel `over_reference_samples` counting values whose magnitude exceeds 1 strictly. Signed codes with fewer valid bits are left-shifted in the stored container; u8 adds bias 128 after signed-code rounding.

**No dithering or noise shaping** is performed. Roundtrip code consistency only validates this stated reference convention. Alternate decode libraries may use different positive-end normalization; lossy quantization, clipping, ADC overload and intersample true peak are separate questions.

IEEE f32/f64 samples are not clamped to [-1,1]. Nonfinite data is rejected; encoding fails on unrepresentable float32 overflow, and counts when a nonzero float rounds to zero. Negative zero may remain encoded. These choices do not establish instrument compliance, physical headroom or an output limiter policy.

## Independently checkable fixtures

| Raw input / action | Expected result |
| --- | --- |
| u8 `00 80 FF` | -1, 0, 127/128 |
| s16 LE `00 80 FF 7F` | -1, 32767/32768 |
| s24 LE `00 00 80`; s24 BE `80 00 00` | -1 in either declared order |
| s24 with 20 valid bits `F0 FF FF` | valid signed code -1 (stored -16); `F0 FF 7F` is max20 and `00 00 80` is min20 |
| s24/20 with low padding bit 1 | Reject, not silently treat low padding as real signal |
| s32 with 24 valid bits `00 FF FF 7F` | max24; minimum `00 00 00 80` |
| Stereo s16 LE L=[0.5,-0.5], R=[-0.5,0.5] | packed bytes `00 40 00 C0 00 C0 00 40`; planar has distinct per-channel buffers |
| Quantize ±0.5 and ±1.5 code-step values | nearest/ties-even produces 0 and ±2 respectively |
| Encode normalized +1 to signed PCM | Saturate to positive maximum, count one saturation, strict over-reference count zero |
| Finite f32 values +1.25 and -1.5 | Preserved when binary32 representable; no integer saturation; two over-reference samples |
| Encode f32 -1e-50 | Negative zero output with one nonzero-to-zero underflow flag |
| NaN/Inf, malformed lengths, ambiguous channel format, nonzero valid-bit padding | Reject before publishing an interpreted measurement |

The [regression cases](../../../tests/test_audio_sample_formats_reference.py) use fixed expected bytes and independent Python `struct`/`wave` checks. They do not certify all WAVE files, broadcast-grade quantization, codec compatibility, hardware capture or realtime throughput.

## Integration boundaries

Keep sample-rate/epoch metadata and channel labels from the originating signal; this raw converter returns channel data and conversion diagnostics, not a full streaming media object. Future channel-remapping, resampler-delay, alignment-stride, audio-file parsing, TPDF dithering and format-specific calibrated measurement require separate implementation and tests.

References: [WAVEFORMATEXTENSIBLE](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ksmedia/ns-ksmedia-waveformatextensible), [Microsoft PCM data](https://learn.microsoft.com/en-us/windows/win32/multimedia/devices-and-data-types), [FFmpeg sample formats](https://ffmpeg.org/doxygen/trunk/group__lavu__sampfmts.html).
