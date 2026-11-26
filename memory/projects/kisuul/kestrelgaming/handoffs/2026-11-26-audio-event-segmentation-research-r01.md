---
schema: 1
id: 2026-11-26-audio-event-segmentation-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-26
updated: 2026-11-26
sources: "Audio branch 327ca13df3cef9193599762685f1350ae4df6900; Foote (2000), Muller FMP novelty-based segmentation, mir_eval segment documentation; executed boundary, support and linear-kernel checks below."
---

# Skill 42 research for event segmentation

## Summary

**Task outcome:** COMPLETE

Define the boundary that the application needs before choosing its
features. Start with a bounded test of how those features change
across a proposed cut. Keep the boundary label, required input
span, and first decision time. Measure boundary retrieval and
segment labels separately. The checks show how a feature gap can
masquerade as change if filled with zeros, and how a gradual
transition can produce a strong novelty peak.
[Foote novelty segmentation](https://doi.org/10.1109/ICME.2000.869637) ·
[FMP novelty-based segmentation](https://www.audiolabs-erlangen.de/resources/MIR/FMP/C4/C4S4_NoveltySegmentation.html)

## Evidence

### Choose the boundary and the features

A cut can represent a timbre change, a harmonic change, silence
entering or leaving a passage, or a section change. Choose the
semantic scale and the relevant observations first. Use
band-energy shape for a timbre comparison, chroma for some
harmonic changes, or a declared envelope for transitions in
activity. A constant-RMS change may be visible in one feature and
have zero score in another. Level normalization can suppress
desired changes in activity as well as irrelevant gain steps.
Report the units, normalization scope, feature frame geometry,
and treatment of quiet input. If the labels must be available
online, compute preprocessing only from the allowed input span.
[Spectral descriptors](../../../../../skills/audio-spectral-descriptors/SKILL.md) ·
[Chroma and harmony research](2026-11-26-audio-chroma-harmony-research-r01.md)

### Compare support on both sides

Let $b$ be the first feature index after a candidate cut. Use
$L$ complete, compatible features on each side, from $b-L$
through $b+L-1$. With left and right means $\bar x_-$ and
$\bar x_+$, the bounded linear baseline is

$$
D(b)=\lVert\bar x_+-\bar x_-\rVert_2^2 .
$$

For $S_{ij}=x_i^\top x_j$, this equals $v^\top S v$, where the
left entries of $v$ are $-1/L$ and the right entries are $+1/L$.
Expanding this expression gives the two within-side similarities
and subtracts the cross-side similarities. It is the box
checkerboard case with a linear similarity and this
normalization. The mean form can run with two finite windows.
Other similarity functions or kernels need their own calculation
and negative tests. This score can miss a distributional change
that leaves both means unchanged.
[Foote (2000), §II](https://citeseerx.ist.psu.edu/document?doi=ad9065b889987b2578bc33a8272b34b42d15fb98&repid=rep1&type=pdf) ·
[FMP checkerboard](https://www.audiolabs-erlangen.de/resources/MIR/FMP/C4/C4S4_NoveltySegmentation.html)

Declare $L$ in frames and the corresponding span in time.
Small support can respond to individual attacks. Large support
can blur nearby cuts or combine independent changes. Compare
two scales on the same observed input. Require all features to
be finite and compatible in tap, epoch and profile. A gap
removes every candidate whose comparison crosses it. If coverage
of a recording includes a gap, report that interval explicitly.

### Label, select and evaluate cuts

For the baseline put the boundary label halfway between the
centers of features $b-1$ and $b$, and preserve both centers.
Use the exact midpoint. In a complete-frame STFT, score $D(b)$
becomes ready when the last required feature is ready. A peak
picker, block dispatch, or smoothing with future frames can
increase that delay. State the threshold units, minimum
separation, plateau tie rule and lookahead. Treat a capture
endpoint as a coverage boundary unless an independently detected
event justifies it as a change. Return disjoint half-open segments
within each valid run. Label uncertain or unknown spans explicitly.
[Frame geometry](../../../../../skills/audio-spectrogram-waterfall/references/STFT_WATERFALL_CONTRACT.md#frame-geometry) ·
[Onset timing research](2026-11-21-audio-onset-detection-research-r01.md)

For boundaries, use one-to-one maximum-cardinality matching
within a declared tolerance. Report precision, recall, the signed
timing errors, and whether imposed endpoints were trimmed.
For structural labels, compare coverage and temporal extents
over the same valid spans. State whether labels are semantic or
arbitrary group IDs. A good boundary score can coexist with poor
label assignment. Tune novelty scale and thresholds on sources
separate from the evaluation recordings.
[mir_eval segmentation](https://mir-eval.readthedocs.io/latest/api/segment.html) ·
[MIREX Music Structure Analysis](https://music-ir.org/mirex/wiki/2025%3AMusic_Structure_Analysis)

### Executed checks and portable fixtures

For the scalar examples use $L=2$ and list scores at every legal
position in ascending order. `NA` denotes an unavailable feature
or comparison.

| Probe | Verified result |
| --- | --- |
| Compare `[0,0,0,0,2,2,2,2]` and `[0,0,0,1,2,3,3,3]`. | Abrupt scores are `[0,1,4,1,0]`. Gradual scores are `[1/4,9/4,4,9/4,1/4]`. There is an equal peak at $b=4$ with different neighboring evidence. |
| Use `[0,0,NA,1,1,1,1]`, then replace the missing frame with zero. | Original scores at $b=2,\ldots,5$ are `[NA,NA,NA,0]`. The fabricated zero produces `[1/4,1,1/4,0]`, including a peak over unsupported input. |
| Use `[1,-1,2,-2]`. | Both means are zero and $D(2)=0$ despite the change in squared magnitude. |
| At 48 kHz use frame length 960 and hop 240, a common origin, and the cut $b=4$ in the first example. | The label is at offset 1,319.5 samples. The score first needs the exclusive input boundary 2,160. A right flank requiring $D(5)$ needs 2,400 instead. |

For a second arithmetic check use NumPy 2.3.5 PCG64 seed
420042 and draw an 88-by-5 standard normal feature array. With
$L=3$, the mean separation and the explicit Gram-matrix
checkerboard agreed within `3.56e-15` squared feature units at
83 positions. The checks exercise the boundary calculation and
timing. Listener judgment, segmentation labels and selected
thresholds need separate evidence.

## Next action

Implement a bounded two-window comparison and peak selection
that exposes both input supports, candidate readiness, and
unavailable intervals. Verify a change across equal-level feature
vectors, a gradual transition, two adjacent cuts, and an
interrupted capture before selecting the feature profile.

## Revisit when

The boundary definition, feature or similarity function, lookahead,
segment label vocabulary, or evaluation tolerance changes.
