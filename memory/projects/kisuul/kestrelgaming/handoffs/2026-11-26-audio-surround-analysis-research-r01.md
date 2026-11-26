---
schema: 1
id: 2026-11-26-audio-surround-analysis-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-26
updated: 2026-11-26
sources: "Audio branch 3d65d0ddb88fead8d8a067e6abb8877ae5609d7b; Microsoft WAVEFORMATEXTENSIBLE, ITU-R BS.775-4 and BS.2051-3, Kestrel channel mapping; executed channel-identity, matrix, and routing fixtures below."
---

# Skill 58 research for surround analysis

## Summary

**Task outcome:** COMPLETE

Start with explicit channel identity and verify the complete
route from the stream to the measured tap. Preserve input
and rendered channel levels, timing, and any signal removed
or combined along the way. Test the LFE content channel and
redirected main-channel bass separately. The fixtures check
two six-channel layouts and one declared downmix.
[Channel mapping](../../../../../skills/audio-channel-mapping/SKILL.md)

## Evidence

### Resolve the input and output labels

Record the format version, ordered source identities, clock,
validity and tap. Identify decoded channel labels before
assigning speaker positions. Use the format's own ordering
rule. A WAVEFORMATEXTENSIBLE bitmap puts channels in increasing
set-bit order. A stream from another format may have a
different order. Preserve unknown channels with their
available identifiers until a placement is established.
[WAVEFORMATEXTENSIBLE channel mask](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ksmedia/ns-ksmedia-waveformatextensible) ·
[Kestrel channel mapping contract](../../../../../skills/audio-channel-mapping/references/CHANNEL_MAPPING_CONTRACT.md)

Name the rendering layout or profile and the measured
speaker or device output. For loudspeaker layouts, refer to
the edition used by the project. A number such as 5.1
communicates channel counts, while the applicable layout
identifies positions and reference geometry. A decoded bed,
a render bus, the amplifier feeds and the acoustic field
are different measurement boundaries.
[ITU-R BS.775-4](https://www.itu.int/rec/R-REC-BS.775/) ·
[ITU-R BS.2051-3](https://www.itu.int/rec/R-REC-BS.2051-3-202205-I/en)

### Measure routing, power and headroom

Start with one active source channel at a time. Check its
destination, sign, gain, clock offset and any unexplained
leakage. Use a distinctive probe through different frequency
bands if filters or delays affect the route. For a simple
matrix $y=Ax$, each unit input reveals a column of $A$.
Keep matrix row/column labels. A row's $\sum_j |A_{ij}|$
bounds its peak when all inputs have magnitudes at most one.
Output power also depends on input correlation. For real
zero-mean signals and covariance $\Sigma_x$, it is
$A_i\Sigma_x A_i^\mathsf T$ for row $i$.

The LFE channel carries separate content. A subwoofer feed
can also include low-frequency portions of main channels
from the playback system's bass management. Check a
main-only low-frequency probe and an LFE-only probe
at the rendered output. Record the cutoffs, routing and
any LFE gain prescribed by the specific profile at each
stage. Apply gain once. Test any intended stereo or mono
fold-down separately. Kestrel's programme loudness rule
owns its own channel weights and exclusions.
[BS.775-4, Annex 7](https://www.itu.int/dms_pubrec/itu-r/rec/bs/R-REC-BS.775-4-202212-I%21%21PDF-E.pdf) ·
[Programme loudness](../../../../../skills/audio-program-loudness/SKILL.md)

### Executed checks and portable fixtures

For the teaching downmix, use the side layout with
$L'=\mathrm{FL}+\mathrm{FC}/2+\mathrm{SL}/2$ and
$R'=\mathrm{FR}+\mathrm{FC}/2+\mathrm{SR}/2$. This chosen
matrix discards LFE and provides a portable exact check.
For the separate bass-path fixture, at an admitted low
frequency use $\mathrm{Sub}=\mathrm{LFE}+
(\mathrm{FL}+\mathrm{FR})/2$ as the stated linear model.

| Probe | Verified result |
| --- | --- |
| Decode WAVE masks `0x3F` and `0x60F`, both with six channels. | The first yields FL, FR, FC, LFE, BL, BR. The second yields FL, FR, FC, LFE, SL, SR. The Kestrel mapper agrees with the bit-order calculation. |
| Run the six unit input vectors through the stated downmix in the side-layout order. | The output pairs are $(1,0)$, $(0,1)$, $(0.5,0.5)$, $(0,0)$, $(0.5,0)$ and $(0,0.5)$. |
| Drive all channels coherently with unit amplitude. Contrast equal-power uncorrelated channels. | Each output can reach amplitude 2 and has power four times one input's power in the coherent case. The uncorrelated power factor is 1.5 by the sum of squared coefficients. |
| Drive FL and FR with values +1 and −1. Test the bass model separately with unit FL alone, then unit LFE alone. | Averaging the stereo outputs gives zero. The bass model gives 0.5 for FL and 1 for LFE. |

These are routing and power identities. Electroacoustic
calibration and verification of a delivery or rendering
standard need evidence from the actual system and profile.

## Next action

Build the analysis around the existing labeled channel mapper.
Add one-channel probes, layout mismatch, summing headroom,
and audible-path evidence as separate review checks. Have
Gauge distinguish the LFE source from the subwoofer output
and compare pure routing with the actual renderer.

## Revisit when

The container layout, renderer, speaker geometry, bass
management, fold-down, or programme measurement profile changes.
