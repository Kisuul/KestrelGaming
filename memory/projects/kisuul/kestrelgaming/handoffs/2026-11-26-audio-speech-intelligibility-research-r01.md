---
schema: 1
id: 2026-11-26-audio-speech-intelligibility-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-26
updated: 2026-11-26
sources: "Audio branch a435c790546b7aefc8ba35ba18be1d7c235f916f; IEC 60268-16:2020; Taal et al. (2011); NIST OpenASR21 evaluation plan; executed edit distance, modulation transfer, and envelope correlation checks."
---

# Skill 62 research for speech intelligibility

## Summary

**Task outcome:** COMPLETE

Measure how much of a speech message listeners can recover
in a declared condition. Select evidence for the decision.
A listening test measures listener responses. An automatic
speech recognizer measures its own transcription errors.
Speech Transmission Index (STI) and Short-Time Objective
Intelligibility (STOI) estimates have distinct inputs,
methods, and validity conditions. The fixtures check edit
counts and two mechanisms that affect prediction.
[IEC 60268-16](https://webstore.iec.ch/en/publication/26771) ·
[Taal et al. (2011)](https://sps.ewi.tudelft.nl/pubs/Taal2011_1.pdf)

## Evidence

### Decide what a score means

Record talkers, text or word list, language, presentation
level, listener population, acoustic condition, and
scoring rules. In a transcription study, fix the scoring
units and rules for a correct response. Report counts and
uncertainty by condition. Use independent listeners or
utterances as appropriate to the study design. Repeated
frames of one utterance share evidence.

For recognizer evaluation, pin the model, language, text
normalization, and scoring protocol. After normalization
and word tokenization, use the minimum edit distance between
the reference and hypothesis. Word error rate is

$$
\mathrm{WER}=\frac{S+D+I}{N_{\mathrm{ref}}},
$$

where $S,D,I$ are substitutions, deletions, and insertions
and $N_{\mathrm{ref}}$ is the number of reference words.
For one corpus rate, pool the counts and denominators
before division. Mark the ratio unavailable when its
reference denominator is zero. Keep any insertion count on
those utterances under the corpus scoring policy.
[NIST OpenASR21 evaluation plan, §3.1](https://www.nist.gov/system/files/documents/2021/08/31/OpenASR21_EvalPlan_v1_3_1.pdf)

### Select a prediction that fits the path

For an electroacoustic speech path, STI concerns the
transfer of speech-like intensity modulations across
frequency bands. Use the applicable edition, method, and
measurement setup, including level and noise conditions.
Check eligibility for the path. The IEC summary lists
limits associated with fluctuating noise, echoes, and
speech processing such as vocoders.
[IEC 60268-16:2020 and corrigendum](https://webstore.iec.ch/en/publication/26771)

For a matched clean/degraded pair, the original STOI method
uses local correlations of time-frequency envelopes with
specific analysis, normalization, clipping and support rules.
Pin the implementation and version. A score needs the
reference, the time alignment, and the scored support.
Track input delay and dropouts before applying the method's
analysis rules. Keep omitted reference words visible in
listener or recognizer scoring if they belong to its target
utterance. Report a prediction in the method's own scale.
[Taal et al. (2011)](https://sps.ewi.tudelft.nl/pubs/Taal2011_1.pdf) ·
[Voice activity](2026-11-26-audio-voice-activity-research-r01.md) ·
[Room acoustics](2026-11-26-audio-room-acoustics-research-r01.md) ·
[Loopback latency](2026-11-26-audio-loopback-latency-research-r01.md)

### Executed checks and portable fixtures

In a simplified single-band model, a normalized causal
exponential energy kernel with time constant $\tau$
attenuates intensity modulation at $f_m$ by
$[1+(2\pi f_m\tau)^2]^{-1/2}$. Constant mean power from
independent, unmodulated noise further reduces the
relative modulation depth by $P_s/(P_s+P_n)$ in that band.
The replay checks this model and basic envelope correlation.

| Probe | Verified result |
| --- | --- |
| Use `reference="turn on the light"` and `hypothesis="turn on a light now"`. Split on whitespace with no other normalization. | One substitution and one insertion give WER `2/4 = 0.5`. |
| Use `reference="light"` and `hypothesis="light then keep reading"` under the same rules. | Three insertions give WER `3/1 = 3`. Clipping at 1 would discard observed errors. |
| Use $\tau=0.10$ s and $f_m=4$ Hz. Sum the first 32,000 impulse weights $(1-a)a^n$ against $\exp(-j2\pi f_m n/f_s)$, with $f_s=16000$ Hz and $a=\exp[-1/(f_s\tau)]$. | The continuous magnitude is `0.36969785`. The infinite discrete value is `0.36969789`. The finite sum agrees with the discrete value within `3e-9`. |
| Add independent, unmodulated noise with $P_s/P_n=4$ to the continuous example. | Relative modulation transfer falls to `0.29575828`. |
| Correlate the envelope `[1,3,2,4]` with twice itself and then with its own reversal. | The correlations are `+1` and `−1`. The two versions have different effects even though a level change alone leaves this correlation unchanged. |

The checks cover arithmetic. Measurement of listener
responses and verification of complete STI or STOI
implementations are future validation steps.

## Next action

Provide a reference and condition record that separates
listener, recognizer, and predicted scores. Give Gauge
known errors, zero reference words, cross-tap delay,
missing target words, and invalid predictor support.
Choose a pinned predictor and a listening or benchmark
dataset that represents the intended distortions before
setting any score threshold.

## Revisit when

The test language, listener population, acoustic path,
alignment, reference, scorer, or type of degradation changes.
