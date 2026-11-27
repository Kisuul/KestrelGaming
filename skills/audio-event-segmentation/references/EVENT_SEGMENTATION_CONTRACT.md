# Event segmentation contract

[Features](#feature-selection) · [Score](#score-and-support) ·
[Timing](#selection-and-timing) · [Coverage](#coverage-and-evaluation) ·
[Reference](#bounded-reference)

## Feature selection

A boundary is a transition at a declared scale. Choose the
changes that qualify. Use band shape for changes in spectral
balance, chroma for changes in pitch-class content, or an
envelope for level and activity. A change of source can leave
RMS steady. A gain step can leave normalized chroma steady.
Compare representative signals before setting a threshold.
[Chroma and harmony](../../audio-chroma-harmony/SKILL.md) ·
[Spectral descriptors](../../audio-spectral-descriptors/SKILL.md)

Specify a tap, epoch, unit per dimension, frame length $M$,
hop $1\le H\le M$, and feature profile. Record normalization,
component weighting, frequency support, and any tuning grid
in the profile. Combine dimensions on a declared scale.
A change in calibration or tuning can look like a signal
change. Begin a new run when these assumptions become
incompatible. Retain the original indices when cropping.
Declare preprocessing support. Global normalization or
a later tuning fit can use samples after the nominal frame.

Use finite, complete features on a common grid. An
unavailable feature or an omitted slot breaks the run.
Represent observed silence as an available zero feature
when the feature's definition admits it. Carry the actual
frame support and all available readiness metadata. A
feature that uses future context needs a later ready
boundary even when its nominal center stays in place.
[STFT frame geometry](../../audio-spectrogram-waterfall/references/STFT_WATERFALL_CONTRACT.md#frame-geometry) ·
[Timebase and epochs](../../audio-timebase-sync/SKILL.md)

## Score and support

For a cut before frame $b$, compare $L$ available frames on
each side. Use indices $[b-L,b)$ and $[b,b+L)$. For left and
right means $\mu_-$ and $\mu_+$, keep the vector change and
squared score.

$$
\Delta(b)=\mu_+-\mu_-,\qquad
D(b)=\sum_k \Delta_k(b)^2 .
$$

Retain the separate sample supports. Analysis windows can
overlap even though the feature indices are disjoint. Record
which windows were compared. A missing frame makes the
comparison unavailable. A change in variance can leave
both means equal. Choose and test another feature when
that change qualifies as a cut.

With inner-product similarity $G_{ij}=x_i^\top x_j$, set
$v_i=-1/L$ on the left and $v_i=+1/L$ on the right.
Then $D(b)=v^\top Gv$. Subtracting the two split
sum-of-squares costs from the unsplit cost gives
$(L/2)D(b)$ for equal support. Account for that factor
when comparing thresholds. A different similarity or
kernel changes the statistic. This reference sums the
represented values exactly. Check large common offsets
when using binary64 prefix sums or the Gram identity.
[Foote, self-similarity novelty](https://doi.org/10.1109/ICME.2000.869637) ·
[Müller, checkerboard kernels](https://www.audiolabs-erlangen.de/resources/MIR/FMP/C4/C4S4_NoveltySegmentation.html) ·
[Window split cost](https://dev.ipol.im/~truong/ruptures-docs/build/html/detection/window.html)

## Selection and timing

Choose a positive threshold in squared feature units and a
peak radius $R\ge1$ in feature steps. Require every score in
$[b-R,b+R]$ to be available. Admit threshold equality.
Require $D(b)$ to exceed every left score and equal or
exceed every right score. This selects the first eligible
point of a plateau. Two selected cuts are at least $R+1$
steps apart, or $(R+1)H$ samples. The reference keeps the score when a peak
flank is unavailable, the threshold fails, or a neighbor
wins. Choose $L$ and $R$ with nearby changes and delayed
features in view.

A strongest-first selection over an entire recording can
change an early decision when a later peak suppresses a
closer competitor. For a fixed readiness claim, replay the
same available prefix with different continuations. Use a
local test with the declared radius for this reference.
[Onset peak selection](../../audio-onset-detection/references/ONSET_DETECTION_CONTRACT.md#peak-selection-and-readiness)

Let $c_j=s_j+(M-1)/2$ be the center of frame $j$. Label
the cut at $B_b=(c_{b-1}+c_b)/2$. Keep both doubled centers
and compute their mean on the exact grid. With constant
$M$ and integer hop, $2B_b$ is an integer.

| Quantity | Evidence boundary |
| --- | --- |
| Score readiness | Latest feature readiness in $[b-L,b+L)$. |
| Peak readiness | Latest score readiness in $[b-R,b+R]$. Its feature union is $[b-R-L,b+R+L)$. |
| Observed score or peak delivery | Latest reported delivery for the used features. If any used feature lacks this value, leave the aggregate delivery unknown. |

With ordinary complete frames, the last raw window for
the score ends at $s_{b+L-1}+M$. Peak confirmation needs
$s_{b+R+L-1}+M$. Feature processing can move the ready
boundary later, even for a feature on the left. These
sample addresses describe data availability. Measure
callback scheduling, processing, and dispatch on the
target path. A finalized segment also needs a confirmed
end or known end of coverage.
[Sample clock and stream buffering](../../audio-stream-buffering/SKILL.md)

## Coverage and evaluation

In the declared analysis span, use disjoint representative
cells $[c_j-H/2,c_j+H/2)$ for feature coverage. Keep their
original overlapping input windows. Clip the cells to the
analysis span. Mark missing cells and uncovered edges as
unknown. Partition available runs at selected interior
cuts. The imposed start and end and the edges of a gap are
coverage boundaries. They define intervals independently
of change detection.

Report peak eligibility as well as feature coverage. The
reference assigns each fully testable interior cut a cell
of width $H$ centered on its estimate. It clips these cells
to the analysis span and joins adjacent cells. Retain these
intervals even when the score fails the threshold. They
describe where the method could test an interior cut under
the declared support. Establish the labeled evaluation
span before scoring and report its coverage.

On each compatible eligible interval, match boundary estimates
and reference labels one-to-one with an inclusive tolerance.
The merged onset matcher uses integer doubled-sample
coordinates and gives a maximum-cardinality pairing with
stable tie handling. Report matches, precision, recall,
F1, signed errors (estimate minus reference), and the
endpoint policy. Use a declared
secondary objective when minimum total timing error matters.

Compare labels on common valid durations. Use agreement
for shared semantic names and a partition metric for
arbitrary group IDs. A perfect boundary match can coexist
with a wrong activity label. Fit feature choice, scale,
and threshold on recordings independent of the evaluation.
[Exact event matching](../../audio-onset-detection/references/ONSET_DETECTION_CONTRACT.md#evaluate-the-detector) ·
[mir_eval segment metrics](https://mir-eval.readthedocs.io/stable/api/segment.html)

## Bounded reference

[Reference](../scripts/reference_event_segmentation.py) ·
[Fixture definitions](../../../tests/fixtures/AUDIO_EVENT_SEGMENTATION_GOLDENS.md) ·
[Executable checks](../../../tests/test_audio_event_segmentation_reference.py)

| Entry point | Contract |
| --- | --- |
| `FeatureGrid` | Bind the feature profile, units, epoch, window, hop, and first frame start. Number frames from that start. |
| `FeatureFrame` | Supply the original index and exact support using `TuningSupport`. Supply a tuple of feature components or mark the values unavailable. |
| `SegmentationProfile` | Set frames per side, peak radius, and positive threshold. Default widths are two per side and one peak neighbor per side. |
| `analyze_segments` | Supply a requested index range and analysis span in doubled samples. Omitted indices are missing. Return every internal comparison, selected boundaries, and known and unknown intervals. |

The reference accepts up to 4,096 feature slots and 64
components. Each side and peak radius can use up to 128
frames. Input records must belong to one grid. Use separate
calls for incompatible epochs or feature profiles. The
analysis is offline and computes exact represented-value
means and decisions. Preserve the resulting original
supports and readiness when passing cuts to temporal fusion.
