---
schema: 1
id: 2026-11-26-audio-denoising-evaluation-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-26
updated: 2026-11-26
sources: "Audio branch a435c790546b7aefc8ba35ba18be1d7c235f916f; ITU-T P.835 (07/2026); Microsoft DNS Challenge; Reddy et al. (2022); executed noise attenuation, speech gain, SI-SDR and error checks."
---

# Skill 67 research for denoising evaluation

## Summary

**Task outcome:** COMPLETE

Evaluate noise reduction and preservation of the wanted
signal on common support. Keep output level, timing,
speech quality, and intelligibility visible when they
matter to the application. The fixture shows how the
strongest noise attenuation can coincide with a weaker
speech result.
[ITU-T P.835](https://www.itu.int/rec/T-REC-P.835-202607-I/en) ·
[Microsoft DNS Challenge](https://github.com/microsoft/DNS-Challenge)

## Evidence

### Run paired conditions

Use the unprocessed input as the baseline. For controlled
tests, retain the clean target, added noise, mixture and
output with a shared clock and known gain. Record target
activity and the rule used to set the input SNR. Use
multiple noise types and levels, including stationary and
intermittent noise, low-level target activity, and short
events. Treat cross-tap gain and alignment as independent
measurements. Preserve reported processing delay when
a reference-based score compensates for that delay.
Keep missing samples and damaged speech on the declared
support. Report real-time lookahead, readiness or
dropouts separately if the application uses live audio.
[Noise and SNR](2026-11-26-audio-noise-snr-sinad-research-r01.md) ·
[Voice activity](2026-11-26-audio-voice-activity-research-r01.md) ·
[Loopback latency](2026-11-26-audio-loopback-latency-research-r01.md)

On real recordings with no clean reference, collect
listener evidence or evaluate a predictor qualified for
that domain. For speech with background noise, P.835
defines separate ratings for the speech signal, background
noise, and overall quality. Document the listening method
and edition. A model such as DNSMOS P.835 predicts ratings.
Record its version and domain and report its results as
predictions with evidence of agreement in the intended
conditions. Pair quality with intelligibility evidence
if speech understanding is a requirement.
[ITU-T P.835 (07/2026) summary](https://www.itu.int/dms_pubrec/itu-t/rec/p/T-REC-P.835-202607-I%21%21SUM-HTM-E.htm) ·
[Reddy et al. (2022), DNSMOS P.835](https://resourcecenter.ieee.org/conferences/icassp-2022/spsicassp22vid1659) ·
[Speech intelligibility](2026-11-26-audio-speech-intelligibility-research-r01.md)

### Executed checks and portable fixtures

Use the orthogonal vectors $s=$ `[1,−1,1,−1]`
and $v=$ `[1,1,−1,−1]` as a synthetic target and
noise basis. Input $x=s+v$ gives 0 dB SNR over the
four samples. Each vector has mean square 1. For
output $y=a s+b v$ with positive gains, component
projections recover $a$ and $b$ exactly for these
vectors. For example, $b=\langle y,v\rangle/\|v\|^2$.
Use $20\log_{10}a$ for target gain, $-20\log_{10}b$
for noise attenuation, and $\operatorname{mean}((s-y)^2)$
for mean square error.

| Output | Noise attenuation | Target gain | SI-SDR | Mean square error |
| --- | --- | --- | --- | --- |
| $s+v$ (input) | 0 dB | 0 dB | 0 dB | 1 |
| $s+0.25v$ | 12.0412 dB | 0 dB | 12.0412 dB | 0.0625 |
| $0.25s+0.125v$ | 18.0618 dB | −12.0412 dB | 6.0206 dB | 0.578125 |
| $0.5s+0.5v$ | 6.0206 dB | −6.0206 dB | 0 dB | 0.5 |

The second processed output removes more noise power
and loses much of the target. The third reduces both
components by the same factor. Its SI-SDR stays at
the baseline. These projections depend on the known
orthogonal components and specified output form. Real
enhancement can add distortion or mix components. Report
any unexplained output residual when the test permits
such a decomposition. The numbers verify the arithmetic
with a deterministic signal. Listener and DNSMOS results
require their own validation.
[Source separation and SI-SDR](2026-11-26-audio-source-separation-research-r01.md)

## Next action

Give Gauge the three outputs, constant gain, mute,
quiet speech, inactive reference support, intermittent
noise, and processing delay. Record the source and
scope of each score. Run comparisons with held-out
speakers and noise recordings after selecting the
target use conditions.

## Revisit when

The deployment mode, clean reference, gain or alignment
policy, noise distribution, or rating method changes.
