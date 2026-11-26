---
schema: 1
id: 2026-11-26-audio-voice-activity-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-26
updated: 2026-11-26
sources: "Audio branch a435c790546b7aefc8ba35ba18be1d7c235f916f; WebRTC VAD interface and pinned core 5bb3ccb; Kestrel timebase and temporal fusion; executed framed hysteresis and scoring fixtures below."
---

# Skill 60 research for voice activity detection

## Summary

**Task outcome:** COMPLETE

Define which speech the detector should preserve. Use a
frame score and a separate decision state. Record both the
labelled interval and when the available input justified
each decision. The fixtures show a missed quiet speech tail,
a false trigger from sustained noise, and a gap during onset
confirmation.
[Temporal fusion timing](2026-11-26-audio-temporal-fusion-research-r01.md)

## Evidence

### Define the observation and target

Record the tap, stream identity, sample rate, epoch, window
support, hop, channel combination and any resampling.
Distinguish observed silence, observed nonspeech, and
unavailable audio. Define the target for overlapping speakers,
singing, breath, whisper and distant speech. A speech activity
label answers a different question from periodic voicing or
speaker identity. Use annotations that cover unvoiced consonants
if they belong to the target.
[Timebase](../../../../../skills/audio-timebase-sync/SKILL.md) ·
[Pitch tracking](2026-11-26-audio-pitch-tracking-research-r01.md)

Start with a transparent energy or band-energy contrast
against a declared noise estimate. Keep the reference
power, attack and release thresholds, floor adaptation,
and means of freezing or resetting that adaptation.
Music and a machinery transient can have high energy.
A trained activity model can bring other evidence. Pin
its model, preprocessing, supported rates, operating
mode, and score units. The WebRTC implementation provides
an example of a framed voice detector with transition
hysteresis. Check the constraints of the version in use.
[WebRTC VAD interface](https://webrtc.googlesource.com/src/+/refs/heads/main/common_audio/vad/include/vad.h) ·
[Pinned WebRTC core](https://webrtc.googlesource.com/src/+/5bb3ccb3e2d3b4b8c50a3ad3c127b114a80a2eed/common_audio/vad/vad_core.c) ·
[Noise power](2026-11-26-audio-noise-snr-sinad-research-r01.md)

### Define confirmation and scoring

A bounded decision rule can require consecutive qualifying
frames at onset and a different threshold and count at
release. Label a confirmed onset at the first candidate
frame, with availability at the end of the last required
frame. Declare whether the release marker is backdated,
whether hangover is a retained label or only a delivery
delay, and how pending candidates end at a gap. A downstream
consumer needs to know if a decision or its timestamp can
be revised.
[Event segmentation](2026-11-26-audio-event-segmentation-research-r01.md) ·
[Dropout and coverage](2026-11-26-audio-dropout-detection-research-r01.md)

Score on a declared common timeline. Use disjoint cells
or interval intersection for duration totals when analysis
windows overlap. Report missed-speech duration divided by
reference speech duration and false-alarm duration divided
by reference nonspeech duration. State those denominators
and any boundary exclusion. Give separate onset and release
errors, support and reporting delay. Preserve tail clipping
and long false activations in the audit. Set operating
thresholds on validation recordings and evaluate on held-out
speakers, sessions and noise.

### Executed checks and portable fixtures

Use 12 disjoint 20 ms cells at 16 kHz. Scores in order are
`[1,5,6,3,1,1,1,9,8,1,1,1]`. Open after two consecutive
scores at least 4 and close after two consecutive scores
below 2. Use the first cell of each pair as its event
boundary. Assume only cells 1 through 4 are reference
speech. Indices are zero-based.

| Probe | Verified result |
| --- | --- |
| Process the complete score sequence. | The two labelled spans are cells `[1,4)` and `[7,9)`. The first starts at 20 ms and ends at 80 ms. The evidence is available at 60 ms for onset and 120 ms for release. |
| Compare the spans with the stated labels. | True positive, false positive, false negative and true negative durations are 60, 40, 20 and 120 ms. Miss and false-alarm rates are both 25% using their respective denominators. F1 is $2/3$. |
| Split delivery after cells 1 and 9 while retaining decision state. | The labelled spans and readiness coordinates agree with the whole sequence. |
| Mark cell 2 missing and clear the pending onset. In a separate probe set cell 8 to 1. | The gap suppresses confirmation of the first span. The shorter isolated noise burst in the second probe fails the two-cell onset rule. |

These checks qualify the decision and scoring arithmetic.
They use supplied scores. Actual discrimination of speech
from noise requires labelled audio and an evaluated scorer.

## Next action

Implement the score-to-decision reference before choosing a
model or threshold default. Give Gauge a quiet speech tail,
a noise burst, a pending onset interrupted by a gap, and
different callback partitions. Measure real operating error
and delivery time on representative recordings.

## Revisit when

The speech definition, frame layout, noise estimate, model,
threshold, gap policy, or delivery endpoint changes.
