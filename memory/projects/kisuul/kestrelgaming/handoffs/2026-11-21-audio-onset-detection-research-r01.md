---
schema: 1
id: 2026-11-21-audio-onset-detection-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-21
updated: 2026-11-21
sources: "Audio branch e98036399451a4c76f251a79e85a3ca8aa30ad99, Bello et al. (2005), Dixon (2006), Boeck et al. (2012), Boeck and Widmer (2013), librosa 0.11.0 documentation, mir_eval matching guidance, MIREX 2013 and executed synthetic, sample-clock, and differential checks."
---

# Skill 36 research for audio onset detection

## Summary

**Task outcome:** COMPLETE

For `audio-onset-detection`, start with positive spectral flux and a
positive RMS-change baseline on complete, sample-clocked frames. Specify
which change counts as a new event. Preserve the novelty curve, selected
peak, estimated event time, and first time at which the decision can use
all required audio. A magnitude-change peak can precede an impulse when
labelled by frame center. The peak from a gradual attack can fall well
after its physical start.

Frequency-neighbor filtering can help when pitch motion triggers false
onsets. The checks below also show a quiet new tone disappearing beside
a stronger held tone. Make the filtering radius and its effect on soft
events observable. This skill starts the temporal and music structure
section. Its novelty curve is an input to the planned beat-tracking skill.
[Curriculum ledger](2026-11-17-audio-curriculum-status-r01.md)

## Evidence

### Define the event and the clock

An **onset** is one time used to mark an event. An attack and a transient
can each span an interval. Agree on the reference point first, such as
the first active sample of an injected probe, a listener's marked start
of a note, or the point for cutting a source sample. For a slow attack,
the start and the largest change can be far apart. Decide whether a
pitch change without rearticulation, a release, or simultaneous events
in a mix qualify under the task. Review representative ambiguous labels.
[Bello et al. (2005), §§I–III](https://doi.org/10.1109/TSA.2005.851998)

Use Kestrel's complete-frame convention. Frame $t$ begins at
$s_t=s_0+tH$, covers $[s_t,s_t+M)$, and has nominal center
$c_t=s_t+(M-1)/2$. Store $2c_t=2s_t+M-1$ exactly. Here $M$ is window
length, $H$ is hop in samples, $N\ge M$ is the DFT length, and $f_s$ is
the sample rate in Hz. The frame grid spacing is $H/f_s$. The window
shape and length control how an attack spreads across frames. Zero
padding samples each frame's spectrum on a denser frequency grid.
A comparison at lag $L$ uses $LH/f_s$ of frame-center separation.
[STFT timing contract](../../../../../skills/audio-spectrogram-waterfall/references/STFT_WATERFALL_CONTRACT.md#frame-geometry)

Record the input tap, epoch, channel mix, and exact support. A mono sum
can cancel an inverted pair, including its transients. Compare the
measured downmix with the input channels when an expected event is
missing. Reset frame comparison, threshold history, and peak state
across a gap, seek, or incompatible profile change. The first $L$
complete frames in a new run have unavailable lagged novelty. Distinguish
an observed silent baseline from intentional boundary padding. A short
capture end can leave a candidate awaiting its right flank.
[Timebase](../../../../../skills/audio-timebase-sync/SKILL.md) ·
[Mid/Side and mono retention](../../../../../skills/audio-mid-side-analysis/SKILL.md)

### Measure positive change

Let $A_{t,k}$ be a nonnegative, declared spectral ordinate on a fixed
grid. For a peak-amplitude STFT, divide magnitudes by the window's
coherent sum and double the paired positive frequencies. Leave DC and
even-length Nyquist unpaired. The isolated-tone calibration gives
consistent comparisons across matched frames. An onset detector's sum
over bins is a score on the chosen grid. Declare the bin selection,
weights, and any compression, such as $S_{t,k}=\log(1+A_{t,k}/A_0)$ for
a fixed amplitude $A_0>0$. If using filterbank powers, state how integration
and compression define each band. Declare any change in the FFT grid,
band weights, or amplitude reference when comparing scores.
[STFT spectral scaling](../../../../../skills/audio-spectrogram-waterfall/references/STFT_WATERFALL_CONTRACT.md#spectral-ordinate-and-visualization)

For positive flux at lag $L\ge1$ use nonnegative weights $u_k$ and sum

$$
V_t=\sum_k u_k[S_{t,k}-R_{t-L,k}]_+,\qquad [z]_+=\max(0,z).
$$

The plain reference is $R_{j,k}=S_{j,k}$. Specify sum, weighted mean,
or another aggregation and calibrate the peak threshold in those same
score units. This half-wave operation selects increases. Kestrel's
spectral descriptors measure frame-to-frame power and shape differences
with their own conventions. Their symmetric flux can respond to both a
rise and a fall. Even a positive-flux detector can respond to a release
that creates new spectral components. [Spectral descriptor flux](../../../../../skills/audio-spectral-descriptors/references/SPECTRAL_DESCRIPTORS_CONTRACT.md#frame-to-frame-flux) ·
[Dixon (2006), §2](https://www.dafx.de/paper-archive/2006/papers/p_133.pdf)

| Feature | Start here | Failure to check |
| --- | --- | --- |
| Positive envelope change | Use $E_t=\sqrt{\sum_j w_j^2x[s_t+j]^2/\sum_j w_j^2}$ and $[E_t-E_{t-L}]_+$ with window $w$. Useful for a strong amplitude attack and a simple comparison. | Equal-RMS spectral changes can yield zero. Gradual attacks shift the maximum rise later. |
| Positive spectral change | Compare each bin or band to the same band in the earlier frame before aggregation. Keep the contributing bins for diagnostics. | A sustained pitch change, clip splice, or gain step can resemble a new event. |
| Neighbor-filtered flux | Set $R_{j,k}=\max_{q\in\mathcal N(k)}S_{j,q}$ with a fixed frequency neighborhood containing $k$. | A strong neighbor can mask a quieter new component. The frequency spacing, lag, and radius determine which movements are suppressed. |
| Complex prediction residual | For complex STFT bins $X_{t,k}$, predict $\lvert X_{t-1,k}\rvert\exp(i(2\phi_{t-1,k}-\phi_{t-2,k}))$ and measure its complex distance from $X_{t,k}$. | Phase can become unreliable in weak bins. A phase reset can be a new attack or a discontinuity. Validate the phase history, level, and any rectification. |

The maximum filter raises the reference or leaves it equal. With the
same nonnegative weights the filtered score is bounded above by plain
flux at every frame. Lower scores on a held note can come with lower
scores on a new attack. Böck and Widmer's SuperFlux applies this idea to a
log-frequency filtered representation. The tests below use a simpler
linear-frequency neighborhood. Compare both curves and retune the peak
threshold for each profile. [Böck and Widmer (2013), §2.2](https://www.cp.jku.at/research/papers/Boeck_Widmer_DAFx_2013.pdf)

With $S=A$ in amplitude units, uniform gain $g>0$ on both frames
scales plain flux by $g$. Log compression changes that relationship.
Independently normalizing each frame
by its own peak can erase a gain-only attack. Report the compression,
level gate, and normalization horizon. For a streaming detector,
estimate any adaptive level or background from the input available
at the decision. librosa 0.11.0 documents mean positive flux with a
frequency-axis maximum reference and an optional frame shift tied to
the FFT length and hop. Match its input representation, lag, aggregation,
padding, and timestamp shift before using it as a comparator.
[Böck et al. (2012), §§2.1 and 2.3](https://www.cp.jku.at/research/papers/Boeck_etal_ISMIR_2012.pdf) ·
[librosa 0.11.0 onset strength](https://librosa.org/doc/0.11.0/generated/librosa.onset.onset_strength.html)

### Turn scores into timed events

A reproducible first peak picker needs a finite history and explicit
boundaries. For the bounded-preview reference below, require the whole
neighborhood. Use a left flank of $a\ge1$ frames, a right flank of
$b\ge1$ frames, a background span $B\ge1$ of preceding novelty frames, and
margin $\delta\ge0$. Accept a candidate if it is strictly higher than
each score in the left flank, at least as high as each score in the
right flank, and strictly above the trailing median plus $\delta$.
Apply the conditions to unrounded values. This selects the first frame
of an eligible equal-valued plateau. For the first-qualifying policy,
require at least $R$ samples from the previous accepted peak, inclusive.
Stronger-peak replacement needs a stated wait or a revision policy.
[Böck et al. (2012), §2.3](https://www.cp.jku.at/research/papers/Boeck_etal_ISMIR_2012.pdf) ·
[librosa 0.11.0 peak-pick conditions](https://librosa.org/doc/0.11.0/generated/librosa.util.peak_pick.html)

With causal novelty and a trailing threshold, a peak at frame $t$ with
a $b$-frame right flank has earliest data-readiness boundary
$r_t=s_t+M+bH$. This is the end-exclusive input boundary. The time
difference from nominal peak center is $(r_t-c_t)/f_s$. Compare
$r_t$ to the reference event time when measuring how long a live
consumer must wait. Actual dispatch adds block and processing timing.
Include any additional lookahead in preprocessing, thresholding, or
peak selection. A past-only picker can act when the current score is
available. Give it a threshold-crossing and rearm rule. A backward
search to an earlier energy minimum can give a slice boundary for editing.
Preserve the
original peak and readiness when returning that boundary.
[Audio stream timing](../../../../../skills/audio-stream-buffering/SKILL.md) ·
[librosa 0.11.0 onset backtracking](https://librosa.org/doc/0.11.0/generated/librosa.onset.onset_backtrack.html)

### Evaluate detection and timing

Match labelled and estimated events **one-to-one** within a declared
inclusive tolerance. Find a maximum-cardinality match before counting
true positives. A greedy nearest-first assignment can miss a second
valid pair. Count unmatched estimates as false positives and unmatched
labels as false negatives. Keep sample positions exact when testing
a tolerance boundary. The match gives precision, recall, and
$F_1=2\,TP/(2\,TP+FP+FN)$ when the denominator is positive. State the
empty-set convention and the eligible time intervals. Define an
assignment tie rule if using the pairings to measure timing errors.
The `mir_eval` onset metric defaults to 50 ms. Choose tighter tolerances
as needed for editing or interactive timing and report them alongside
the matched signed errors and data readiness.
[mir_eval onset metric](https://mir-eval.readthedocs.io/latest/api/onset.html) ·
[mir_eval maximum matching](https://mir-eval.readthedocs.io/latest/api/util.html#mir_eval.util.match_events) ·
[MIREX 2013 onset evaluation](https://www.music-ir.org/mirex/wiki/2013%3AAudio_Onset_Detection)

Use known digital boundaries for sample-clock tests and annotated audio
for musical onset performance. Tune on different sources from the final
evaluation. Keep percussive, gradual, pitched, and mixed events visible
in the scores. Check quiet sustained passages, repeated near hits, and
the frequency range and level of missed events. Annotator variation sets
a practical limit on interpreting small timing differences. The checks
below exercise synthetic cases, including deliberately chosen failures.

### Executed checks and portable fixtures

All PCM examples use 48 kHz. For the first five rows use two complete
rectangular frames of length and hop 480, DFT length 480, and peak
amplitude on all nonnegative bins. A tone at bin $k$ and gain $a$
means $a\cos(2\pi kn/480)$ for $n=0,\ldots,479$ within each frame.
Use lag 1, unit weights, and radius 1 for the filtered form. Suppressed
synthetic scores in those rows were zero within $3.1\times10^{-15}$
normalized amplitude units.

| Fixture | Observed or exact result |
| --- | --- |
| Bin 8 at gain 0.5 changes to bin 9 at gain 0.5. | RMS rise is zero. Plain flux is 0.5. Filtered flux is zero within rounding. |
| Bin 8 at gain 0.5 changes to bin 12 at gain 0.5. | RMS rise is zero. Both flux scores are 0.5. |
| Bin 8 stays at gain 0.6 and bin 9 begins at gain 0.2. | RMS increases by about 0.02295. Plain flux is 0.2. The neighbor filter masks the new tone. |
| Bin 8 holds its frequency while gain drops from 0.5 to 0.25. | Both positive differences and RMS rise are zero. |
| Bin 8 holds its frequency while gain rises from 0.5 to 0.75. | RMS rise is about 0.17678. Both flux scores are 0.25. |
| At one complex bin take $X=(1,1,1)$, then test $X=(1,1,-1)$. | Magnitude novelty is zero for both. The final complex residual is 0 for the steady case and 2 for the phase reset. |
| Novelty in order is $[\mathrm{NA},0,0,4,4,1,0,5,0,0,0]$. Use $H=240$, $a=1$, $b=2$, $B=2$, and $\delta=0.5$. | Choose frame 3 on the plateau. Frame 7 is accepted at $R=960$ and suppressed at 961. Truncate the final two entries and frame 7 lacks a complete right flank. |
| With 25 ms tolerance, labels $[100,140]$ ms and detections $[125,160]$ ms. Then use label $[1000]$ ms, detections $[990,1010]$ ms and 20 ms tolerance. | Maximum matching gives two true positives in the first case. Nearest-first assignment of 125 to 140 can lose the second match. The second case gives $TP=1,FP=1,FN=0$ and $F_1=2/3$. |

**Vibrato.** Over two seconds, use
$x[n]=0.5\cos(2\pi(1000)t+(28/5)(1-\cos(2\pi(5)t)))$ at $t=n/f_s$.
This has a sinusoidal instantaneous-frequency excursion of 28 Hz at
5 Hz modulation. Use a periodic Hann with $M=N=2048$, $H=240$, and
lag 1 on the linear bin grid. Across 391 comparisons, the 95th percentile
of plain flux was 0.097353. With radius 1 it was 0.031076, about a 68%
reduction with residual novelty. Radii 2 and 3 left that percentile
near 0.031075 and gave the same peak as radius 1 to the reported
precision (0.038825). The quiet-tone case above shows the tradeoff on
a deliberately added onset.

**Timing.** Put a unit impulse at sample 4440 of a 7200-sample tape.
With periodic Hann $M=N=960$, $H=240$, lag 1, and plain flux, use
$a=1$, $b=2$, $B=4$, and $\delta=0.01$. The peak is frame 16 with center
4319.5. The first readiness boundary is sample 5280. The peak label is
2.5104 ms early and the decision is ready 17.5 ms after the known impulse.
These coordinates also held at origin $2^{60}+37$ with one full block,
single-sample blocks, and pseudo-random block sizes from 1 to 600
using NumPy PCG64 seed 360036. For a second tape, multiply a 1 kHz cosine
by $0.5\sin^2(\pi u/2)$, where
$u=\min(1,\max(0,(n-4440+1)/3840))$, for 12,000 samples. With the same
frame geometry, the largest weighted RMS rise was at center 6479.5,
42.4896 ms after the first active sample of the 80 ms attack.

**Differential and reuse check.** With NumPy PCG64 seed 360020, draw
uniform $[-1,1)$ samples for each profile in order
$(M,N,H,L,r)=(24,32,12,1,0),(25,33,9,2,1),(31,31,31,1,2),(18,40,7,3,1)$.
Use seven complete frames plus a three-sample tail and a periodic Hann.
Compare a direct DFT with a real FFT and apply $S=\log(1+20A)$ with unit
weights. The 497 amplitudes matched within $1.444\times10^{-15}$ against the
direct DFT and $1.111\times10^{-16}$ against SciPy FFT. The 21 supported
novelty scores matched a direct per-bin comparison and sum within
$1.155\times10^{-14}$. The existing Kestrel STFT matched the 497 amplitudes
within $1.638\times10^{-15}$ and preserved all 28 exact center coordinates
at a large origin under a different chunk partition. The environment
used NumPy 2.3.5 and SciPy 1.17.0. Library documentation above gives
the expected conventions for additional comparisons.

## Next action

Use Kestrel's frame and amplitude conventions for an offline reference
with positive RMS rise, plain flux, and an explicit peak picker.
Preserve frame readiness and the optional adjusted event timestamp.
Give a reviewer the held tone with a quiet neighbor, the impulse,
the 80 ms attack, and the inclusive separation case. Check silence,
clip boundaries, gap reset, invalid samples, and callback partitioning
before treating results as portable. Compare a labeled music set and
record the operating threshold before using a frequency filter or phase
feature as the default. Keep the continuous novelty curve and exact
sample clock available to subsequent timing skills.

## Revisit when

The event definition, input tap, frame grid, spectral compression,
frequency neighborhood, threshold horizon, timing budget, or intended
instrument mix changes.
