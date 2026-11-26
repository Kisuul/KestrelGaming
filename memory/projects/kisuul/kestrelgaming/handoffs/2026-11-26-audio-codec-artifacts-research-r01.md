---
schema: 1
id: 2026-11-26-audio-codec-artifacts-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-26
updated: 2026-11-26
sources: "Audio branch 3d65d0ddb88fead8d8a067e6abb8877ae5609d7b; RFC 7845 §§4–5, FFmpeg codec documentation, ITU-R BS.1116-3 and BS.1534-3; executed PCM, Opus and AAC fixtures and R55-01 replay on FFmpeg 7.1.5-0+deb13u1 with linked libopus 1.5.2; Gauge review on PR #55 at 045a73e."
---

# Skill 51 research for codec artifacts

## Summary

**Task outcome:** COMPLETE

Align the intended presentation intervals before comparing
decoded waveforms. Keep codec delay, container trimming,
alignment and residual changes visible. Compare transient
neighborhoods and band energies on matched support. The
checks use a PCM control and three lossy profiles, including a
case where the raw decoded length exceeds the presented length.
[Ogg Opus framing and trimming, RFC 7845](https://www.rfc-editor.org/rfc/rfc7845.html#section-4)

## Evidence

### Identify the comparison domain

Record the source identity and PCM scale, codec and container,
encoder/decoder build, rate, channel mapping, target bitrate or
rate mode, frame setting and packet handling. Read presentation
timestamps, priming or pre-skip, and end trim. Identify which
corrections the decode path already applied. For Ogg Opus, the
granule position and pre-skip use the 48 kHz coordinate system.
Map to the comparison rate if different. Inspect output length
and align the common valid interval before subtracting samples.
Keep the unpaired head and tail available for diagnosis.
[RFC 7845 §§4.2–4.4](https://www.rfc-editor.org/rfc/rfc7845.html#section-4.2) ·
[FFmpeg codec options](https://ffmpeg.org/ffmpeg-codecs.html)

Verify residual alignment with a distinctive probe and a
known-offset control. A correlation peak can be ambiguous in
repeated audio. If a capture has drift, a single shift can
hide clock mismatch in one part and increase it elsewhere.
Record any resampling, gain match, channel mapping or shift.
Keep the uncorrected measurement when the correction removes
part of the format or playback behavior under investigation.
[Cross-correlation](../../../../../skills/audio-cross-correlation/SKILL.md) ·
[Timebase](../../../../../skills/audio-timebase-sync/SKILL.md)

### Match an artifact claim to an observation

| Question | Discriminating check |
| --- | --- |
| Did a transient spread or move? | Compare a known attack on a verified clock. Measure peaks, peak position, and error energy in separate intervals before and after the event. Test a shifted PCM control. |
| Did high-band content change? | Measure matched windows and calibrated band power for sustained tones and broadband input. Separate expected rate conversion and a codec bandwidth choice from an unknown filter in the path. |
| Did time-varying artifacts occur? | Inspect local residuals and spectra by exact time span. Compare rate settings and source material. A single whole-track RMS score can conceal a brief large error. |
| Did transport or the source contribute? | Compare a local encode/decode baseline, a lossless path, and any capture with packet loss or concealment. Inspect source clipping and dropped intervals independently. |

Prefer “observed pre-transient energy” to attributing cause
or audibility from one fixture. For perceptual claims, define
the listening question, match playback level and time support,
and use a controlled comparison on representative material.
BS.1116-3 addresses small impairments. BS.1534-3 covers
intermediate quality. The measurement below is an objective
diagnostic on isolated impulses.
[ITU-R BS.1116-3](https://www.itu.int/rec/R-REC-BS.1116) ·
[ITU-R BS.1534-3](https://www.itu.int/rec/R-REC-BS.1534-3-201510-I/en)

### Executed checks and portable fixtures

Use a mono 48 kHz signed 16-bit PCM `input.wav` of 48,000 samples. Set
samples at 12,000 and 36,000 to +24,576 and −24,576 respectively,
with zero elsewhere. The source uses a standard 16-byte PCM
`fmt ` chunk and a `data` chunk, with no extra chunks. Its file
SHA-256 is `edd82135d9b8d585b0265f55a7cf66e9cbf183ba94213a183c86cc77b75549ce`.
The PCM decode yields exact normalized peaks of ±0.75 at those
coordinates and length 48,000.

The replay used FFmpeg `7.1.5-0+deb13u1` on x86-64, built with
GCC 14.2.0-19, `--enable-libopus` and `--enable-shared`.
The linked libopus reported `1.5.2`. The FFmpeg libraries were
libavcodec 61.19.101, libavformat 61.7.103, and libswresample
5.3.100. The commands below select libopus for encoding and
FFmpeg's native AAC encoder. The default decode on this build
selected FFmpeg's native Opus and AAC decoders. CPU dispatch,
threading, and unspecified codec options used their defaults.
Decode to little-endian binary64 PCM with container trim
as applied by FFmpeg and no extra manual trim.

```sh
ffmpeg -hide_banner -nostdin -loglevel error -i input.wav \
  -c:a libopus -b:a 24k -vbr off -application audio -frame_duration 20 24k.opus
ffmpeg -hide_banner -nostdin -loglevel error -i input.wav \
  -c:a libopus -b:a 96k -vbr off -application audio -frame_duration 20 96k.opus
ffmpeg -hide_banner -nostdin -loglevel error -i input.wav -c:a aac -b:a 64k 64k.m4a

for file in input.wav 24k.opus 96k.opus 64k.m4a; do
  ffmpeg -hide_banner -nostdin -loglevel error -i "$file" -map 0:a:0 \
    -f f64le -c:a pcm_f64le pipe:1 > "$file.f64le"
done
ffprobe -v error -select_streams a:0 -show_streams -show_packets \
  -show_data_hash sha256 -of json 96k.opus
```

Pre- and post-event numbers are $10\log_{10}$ of the mean squared
error relative to unit square in intervals `[11760,12000)` and
`[12001,12241)`.

| Profile | Raw decoded samples | Sample at 12,000 | Pre-event error (dBFS) | Post-event error (dBFS) |
| --- | ---: | ---: | ---: | ---: |
| Ogg Opus 24 kb/s | 48,000 | 0.582418 | −36.3182 | −37.5013 |
| Ogg Opus 96 kb/s | 48,000 | 0.617178 | −38.0289 | −37.2524 |
| M4A AAC 64 kb/s | 48,128 | 0.557732 | −36.7923 | −36.3788 |

For both Opus files, packet inspection reported a 312-sample
initial skip and 648 samples of final discard. The decoded
stream already reflected both corrections. For AAC, the
packet timebase was 1/48,000, first skip was 1,024 samples,
and the last packet had PTS 47,104 and duration 896. That
ends the reported presentation at sample boundary 48,000
even though the raw PCM decode returned 48,128 samples. Use
the presentation interval in that case. For each codec the
largest absolute peak within 240 samples of each impulse was
at the original sample coordinate. Peak alignment and equal
presentation length can coexist with a changed waveform.

Treat the waveform values in the table as observations for
this build and configuration. Three fresh local runs reproduced
them to the listed precision. For the 96 kb/s case, they
shared packet fingerprint
`85bf88e35b96d95643359e5e8ee48f1f4cfcccdb05aac503992e8798990e8c1a`.
This is the SHA-256 of the ordered ffprobe `data_hash` strings
joined by LF without a final LF. The three Ogg file hashes
differed even though the audio packets and decoded PCM matched.

With the same 96 kb/s file, adding `-c:a libopus` before
`-i` for decode gave sample 0.617218, pre-event error
−38.0292 dBFS, and post-event error −37.2518 dBFS. Peak
indices and decoded length agreed. Gauge's separate replay
gave 0.617252, −38.0299 dBFS, and −37.2498 dBFS. The cause
of Gauge's particular difference remains open. Use timing
and trim checks for this controlled replay. To set numeric
waveform acceptance values, freeze the encoded input with its
timing metadata, pin the decoder build, and validate a
tolerance on the target platforms.
[Gauge review R55-01](https://github.com/Kisuul/KestrelGaming/pull/55#pullrequestreview-6072720516)

For a shift-only control, a periodic 12 kHz tone at 48 kHz
with peak amplitude 0.25 and a circular shift of one sample
gives residual RMS 0.25. Reversing the known shift gives a
zero residual. These fixtures support timing and diagnostic
checks for the stated builds and settings. They provide no
perceptual ranking.

## Next action

Implement the comparison contract around a declared
presentation range and verified alignment. Preserve raw
decode length and any excluded support. Give Gauge an
unchanged PCM control, a shifted copy, a trimmed codec
decode, and repeated content with ambiguous lag before
automating residual or artifact reports.

## Revisit when

The codec build, rate or frame mode, container timing,
alignment policy, source material, or listening target changes.
