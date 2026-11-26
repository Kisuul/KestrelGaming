---
schema: 1
id: 2026-11-26-audio-clipping-detection-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-26
updated: 2026-11-26
sources: "Audio branch 3d65d0ddb88fead8d8a067e6abb8877ae5609d7b; Kestrel PCM, sample-peak and true-peak contracts; ITU-R BS.1770-5 Annex 2; executed rail, soft-saturation and intersample fixtures below."
---

# Skill 49 research for clipping detection

## Summary

**Task outcome:** COMPLETE

Measure contact with the declared numeric rails and preserve
the observed pattern. A flat peak supports a hard-clipping
diagnosis under a specified signal model. Source history
requires further evidence. Keep sample-rail observations,
floating-point headroom and reconstructed peaks in their
respective domains.
[PCM format contract](../../../../../skills/audio-sample-formats/references/PCM_FORMAT_CONTRACT.md) ·
[ITU-R BS.1770-5, Annex 2](https://www.itu.int/rec/R-REC-BS.1770-5-202311-I)

## Evidence

### Define the boundary of interest

Identify the tap, encoding, valid bits, scale and any known
clamp. Signed 16-bit PCM codes range from −32,768 through
+32,767. With division by 32,768, the most negative code is
−1 and the most positive code is just below +1. Test the two
rails separately. Use the valid-code domain after unpacking
when PCM has fewer valid bits than container bits.

A float tap may intentionally preserve values above its
nominal full-scale reference. Label those values as reference
exceedances at that tap. A later integer export can saturate
them if its quantization policy clips. Compare upstream and
downstream captures or a known conversion function before
attributing the change to a specific stage.
[Sample formats](../../../../../skills/audio-sample-formats/SKILL.md) ·
[Sample peak](../../../../../skills/audio-sample-peak/SKILL.md)

### Preserve sample evidence and limits

- Count exact rail contacts per channel and polarity. Report
  contiguous runs as half-open sample intervals with code,
  length and epoch. A declared minimum run length can
  distinguish a plateau candidate from an isolated rail hit.
  Preserve both observations.
- If using near-rail runs or repeated extrema in float data,
  declare the tolerance units, local model, and whether the
  plateau is at a known ceiling. Silence, a constant signal,
  a rectangular waveform, or legitimate repeated quantized
  values can yield a flat region. A clean reference, nearby
  waveform shape, and co-located distortion help test a
  clipping diagnosis.
- Keep detector state across contiguous callbacks. End or
  mark a partial run at a gap or epoch change. State when a
  run can be reported and when its end can be confirmed.
  [Timebase](../../../../../skills/audio-timebase-sync/SKILL.md)
- Distinguish soft saturation from contact with the numeric
  ceiling. A nonlinear path can change the waveform and
  create harmonics while every sample remains far from a
  declared rail. Compare levels and the spectrum against an
  appropriate reference before inferring the cause.
  [Distortion research](2026-11-26-audio-thd-thdn-research-r01.md)

### Keep intersample peaks separate

An observed sample peak is the maximum of captured samples.
An estimated true peak concerns a reconstruction between
samples. A reconstructed waveform can exceed the reference
even if no PCM code reaches it. State the reconstruction,
bandwidth, boundaries and error when making a true-peak
claim. Use Kestrel's true-peak evidence for that measurement.
Both measures describe their tap. A downstream clipping event
requires evidence from the downstream stage or its defined
conversion.
[ITU-R BS.1770-5, Annex 2](https://www.itu.int/rec/R-REC-BS.1770-5-202311-I) ·
[True-peak contract](../../../../../skills/audio-true-peak/references/TRUE_PEAK_CONTRACT.md)

### Executed checks and portable fixtures

| Probe | Verified result |
| --- | --- |
| Use codes `[0,32767,32767,32767,0,-32768,-32768,0,32766,32767,32766,0]` at origin 0. Compare one block to splits of 2, 3, 1 and 6. | Positive runs are `[1,4)` and `[9,10)`. The negative run is `[5,7)`. With a two-sample plateau rule the isolated hit remains a contact only. The partition gives identical runs. |
| Supply one positive rail contact at sample 10 and then one at 12 with missing sample 11. | The two known runs are `[10,11)` and `[12,13)`. There is no observed two-sample plateau. |
| Sample the ideal periodic sine $1.1\sin(\pi n/2+\pi/4)$ with no further processing. | The maximum sample magnitude is 0.77781746. The continuous sine in this fixture reaches 1.1. |
| At 48 kHz for 4,800 samples let $y=0.8\tanh(2\sin(2\pi1000n/48000))$. | The sample peak is about 0.771222 and the 3 kHz component has peak amplitude about 0.150994. A ±1 rail rule finds no contact. |

These checks verify sample evidence, one analytical
intersample example and a known nonlinear model. Actual
analog saturation, perceptual impairment, and prior signal
history need additional observations.

## Next action

Implement a bounded rail-run measurement with explicit
unpacked-code and float-reference policies. Show Gauge
asymmetric rails, isolated hits, a gap inside a run, and a
sub-rail nonlinearity. Keep a suspect clipping label tied to
the evidence that produced it.

## Revisit when

The tap, format, level reference, tolerance, reconstruction,
or diagnosis policy changes.
