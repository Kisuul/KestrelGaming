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
sources: "Audio branch 3d65d0ddb88fead8d8a067e6abb8877ae5609d7b; RFC 7845 §§4–5, FFmpeg codec documentation, ITU-R BS.1116-3 and BS.1534-3; executed FFmpeg 7.1.5 PCM, Opus and AAC fixtures below."
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

Use a mono 48 kHz signed 16-bit WAV of 48,000 samples. Set
samples at 12,000 and 36,000 to +24,576 and −24,576 respectively,
with zero elsewhere. The lossless decode yields exact normalized
peaks of ±0.75 at those coordinates and length 48,000.

The following FFmpeg 7.1.5 runs decoded the stream into
64-bit float PCM with no extra manual trim. Both libopus
encodes used `-application audio -frame_duration 20 -vbr off`
with the stated `-b:a`. The AAC encode used the native AAC
encoder in M4A and `-b:a 64k`. Pre- and post-event numbers
are $10\log_{10}$ of the mean squared error relative to
unit square in intervals `[11760,12000)` and `[12001,12241)`.

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
