---
schema: 1
id: 2026-11-21-audio-beat-tracking-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-21
updated: 2026-11-21
sources: "Audio branch 327ca13df3cef9193599762685f1350ae4df6900, Skill 36 research at 61d5114311f41c3016ab8fafb3fb857ef1a31b19, Ellis (2007), Mueller FMP, Boeck et al. (2016), librosa 0.11.0, mir_eval beat metrics, and executed synthetic, differential, and exhaustive checks."
---

# Skill 37 research for audio beat tracking

## Summary

**Task outcome:** COMPLETE

For `audio-beat-tracking`, use a clocked onset-strength curve to estimate
plausible beat periods and align a sequence of beat positions. Start
with a bounded offline reference at an explicit tempo. Then test joint
tempo selection, changes in tempo, and the policies for weak evidence.
The same 120 BPM estimate can support several beat phases. An interval
penalty can recover a missed beat and also extend a grid through
silence. Keep the measured evidence for each position with the track.
[Skill #36 onset research](https://github.com/Kisuul/KestrelGaming/blob/61d5114311f41c3016ab8fafb3fb857ef1a31b19/memory/projects/kisuul/kestrelgaming/handoffs/2026-11-21-audio-onset-detection-research-r01.md) ·
[Curriculum ledger](2026-11-17-audio-curriculum-status-r01.md)

## Evidence

### Define the beat and map its time

A beat is a position in the pulse a listener could tap along to.
Tempo is its rate, and phase locates that pulse within the recording.
An onset marks a local acoustic event. A syncopated accent can fall
between beats, and an inferred beat can fall in a pause. The downbeat
is the first beat of a measure. Choose the annotated pulse level
before evaluating and record which pulse levels an application accepts.
[Ellis (2007), §§1–2](https://doi.org/10.1080/09298210701653344) ·
[Böck, Krebs and Widmer (2016), beat and downbeat model](https://zenodo.org/records/1415836)

Use continuous novelty $v[t]$ with a declared analysis tap, epoch,
sample rate $f_s$, and frame hop $H$. Preserve the interval and exact
time coordinate of each input frame, including unavailable frames.
At feature rate $r=f_s/H$, a period of $P$ frames gives tempo $60r/P$ BPM.
If $c_0$ is the first
feature frame's nominal center then $c_t=c_0+tH$. Use Kestrel's twice-center
integer field for half-sample centers and large time origins. Retain
the origin change if analysis uses a cropped or resampled tape. Keep
event time and data readiness from the feature stage through to the
beat result.
[STFT frame geometry](../../../../../skills/audio-spectrogram-waterfall/references/STFT_WATERFALL_CONTRACT.md#frame-geometry) ·
[Sample clocks and epochs](../../../../../skills/audio-timebase-sync/SKILL.md)

If scheduling a fixed BPM on a sample grid, accumulate the fractional
period before converting each event to its output sample or frame.
Repeatedly adding a rounded period introduces a different tempo.
The timing fixture below quantifies this drift at 137 BPM.
[Audio numerical stability](../../../../../skills/audio-numerical-stability/SKILL.md)

### Estimate candidate periods

For $T$ consecutive valid features, choose a preprocessing rule and call
its output $u[t]$. A baseline on nonnegative novelty uses the raw linear
autocorrelation

$$
R[p]=\sum_{i=0}^{T-1-p}u[i]u[i+p],\qquad 0<p<T.
$$

State the units, window, and any centering, normalization, or weighting.
A steady floor contributes across lags. Mean removal is one way to
test whether apparent periodicity comes from variation around that
floor. A mean product $R[p]/(T-p)$ removes the pair-count factor.
It can be noisy when few pairs remain. Keep the valid overlap and
number of cycles with the score. Inspect a lag search that has enough
support for the slowest candidate. For an FFT implementation, pad to
at least $2T-1$ points, transform, square the complex magnitude,
and inverse transform. Compare the nonnegative lags to the direct sum
before adopting it. [Müller, autocorrelation tempogram](https://www.audiolabs-erlangen.de/resources/MIR/FMP/C6/C6S2_TempogramAutocorrelation.html) ·
[Kestrel linear correlation checks](../../../../../skills/audio-cross-correlation/references/CROSS_CORRELATION_CONTRACT.md#verify-fft-and-refinements)

For allowed $B_{\min}\le B\le B_{\max}$, consider integer lags from
$\lceil60r/B_{\max}\rceil$ through $\lfloor60r/B_{\min}\rfloor$, with
positive lag and overlap. Keep the candidate peaks and their half-rate
or double-rate neighbors when eligible. Rank the score and any tempo
prior explicitly. An octave choice determined by the prior has different
evidence from a unique peak with sustained support. Periodic subdivisions
and alternating accents can favor different metrical levels. Low energy,
a flat score, or too little support can make the period unavailable.

Time-local autocorrelation gives tempo evidence for each declared window.
A longer window includes more cycles and mixes more of a nearby tempo
transition. A shorter one reacts faster and may have too few repetitions.
Retain the time bounds and edges of each window. Causal tracking needs
windows available at the decision and a declared rule for switching or
retaining a tempo. [Müller, local tempo and windowing](https://www.audiolabs-erlangen.de/resources/MIR/FMP/C6/C6S2_TempogramAutocorrelation.html) ·
[librosa 0.11.0, time-varying tempo example](https://librosa.org/doc/0.11.0/auto_examples/plot_dynamic_beat.html)

### Align the beat sequence to the evidence

For a rigid integer trial period, scores summed at each grid phase
$\varphi$ over supported times $\varphi+jP$ give a simple phase check.
Use equal support or a declared weighting so one phase gains no advantage
from the record edges. A phase shift of the entire pulse train can leave
the autocorrelation unchanged. Use the positions or a phase-sensitive
representation to align beats.

An Ellis-style reference balances onset evidence and interval cost.
A bounded form on a contiguous valid run is

$$
D[t]=v[t]+\max\left(0,\max_{s\in \mathcal P(t)}
  \left[D[s]-\lambda\log^2\!\left(\frac{t-s}{P_t}\right)\right]\right),
\qquad
\mathcal P(t)=\{s<t:\lceil P_t/2\rceil\le t-s\le\lfloor2P_t\rfloor\}.
$$

Here $P_t>0$ is fixed for the run or a supplied period at the current node,
and $\lambda\ge0$ has the scale of the local novelty score. Use the natural
logarithm. The zero
option starts a new path. Declare a start and end policy and how ties
are broken. Save the selected predecessor at each node. Backtrack from
the best admissible endpoint. With predeclared $P_t$, this recurrence
optimizes the stated offline path objective on its allowed edges.
For tempo estimated jointly with the path, carry period in the state
and price specified tempo changes. The fixtures below use the plain
novelty values as the local term and the configured period as a target.
Ellis uses a smoothed local observation and other practical start
and end details. [Ellis (2007), §§2–4](https://doi.org/10.1080/09298210701653344) ·
[Müller, beat tracking by dynamic programming](https://www.audiolabs-erlangen.de/resources/MIR/FMP/C6/C6S3_BeatTracking.html)

An evenly spaced beat with no onset can carry the path across a missed
event. At exact target spacing a zero-valued frame adds zero to the
score. A stretch of neutral beats through silence can therefore win
if it connects two supported sections. Set a duration or count limit
on weakly supported beats, and declare how beats resume after that
limit. A capture gap ends the valid run. Retain an indication of which
beats had a nearby supporting observation and which came from the
interval model. Inspect near competitors before presenting a stable
sequence as a confident pulse.

Multiplying all novelty scores by $g>0$ without rescaling the interval
cost changes the cost relative to the evidence. Multiplying $\lambda$
by the same $g$ scales all path scores equally in this objective.
Comparing the unnormalized path totals of two tempos can favor the
one with more beat nodes. Use the periodicity score and stated prior
to rank tempo hypotheses on common support. For a comparison of
whole paths across tempos, declare how the objective accounts for beat count
and duration. For comparison with librosa 0.11.0, account for its supplied BPM or
tempo estimation, onset normalization and smoothing, search bounds,
edge trimming, and frame-to-time mapping.
[librosa 0.11.0 beat tracking](https://librosa.org/doc/0.11.0/generated/librosa.beat.beat_track.html) ·
[librosa 0.11.0 implementation](https://librosa.org/doc/0.11.0/_modules/librosa/beat.html)

### Qualify online delivery and evaluation

Two recordings with the same available prefix can favor different
phases once the suffix arrives. A streaming tracker should have an
explicit commitment policy. It can confirm a beat after hearing it,
wait for bounded additional evidence, or predict a future beat from
previous observations. Record the estimated beat, the newest sample
used, and when it was emitted. A later correction needs a declared
revision policy. Bound predictions through weak evidence and reset
timing state on a discontinuity. In a live consumer, report acquisition
time, prediction horizon or confirmation latency, timing error, and
the runtime needed to dispatch the event. An offline backtrack provides
a comparison for musical alignment.
[Real-time beat tracking study](https://transactions.ismir.net/articles/189/files/66fc0db587be3.pdf) ·
[Audio buffering and latency](../../../../../skills/audio-stream-buffering/SKILL.md)

Evaluate a tempo estimate separately from the time sequence. Match beats
one-to-one in an inclusive time window at the declared pulse level.
Report true positives, false positives, missed beats, signed timing
errors, and continuity. `mir_eval.beat.f_measure` defaults to a 70 ms
window. CMLc summarizes the longest continuously correct run at the reference
metrical level, and CMLt summarizes its total correct coverage. AMLc and AMLt
allow metrical alternatives such as half rate, double rate, or offbeat phase.
Use both kinds when octave or offbeat ambiguity matters. Record any
startup trim and score startup separately when the application cares
about lock time. `mir_eval.beat.trim_beats` defaults to removing events
before 5 s. Use explicit tuning and evaluation sets when claiming
performance on music. [mir_eval beat metrics](https://mir-eval.readthedocs.io/latest/api/beat.html) ·
[Davies, Degara and Plumbley, beat evaluation methods](https://citeseerx.ist.psu.edu/document?doi=4f8ad740cd13c705c7456cd19eb2bf748554800a&repid=rep1&type=pdf)

### Executed checks and portable fixtures

Except as specified, the following sequences are zero-based novelty
frames at 100 Hz ($f_s=48$ kHz and $H=480$). Indices not listed have
zero novelty. A listed pulse has strength 1 unless marked otherwise.
The path fixture uses $\lambda=8$, the bounded lags in the equation,
start bonus 0, strict positive continuation bonus, and the earliest
endpoint on a score tie. Its synthetic quiet spans represent valid zero novelty.
These tests exercise the evidence and timing rules on synthetic data.

| Fixture | Observed or exact result |
| --- | --- |
| In two length-800 tapes place pulses every 50 frames, starting at 7 and 31 respectively. | Direct autocorrelations are identical at lags 1–129. The period search on 25–100 selects 50 in both. Phase sums select 7 and 31. Both tempos are 120 BPM. |
| Length 800. Place equal pulses at $7+25j$. Compare lags 25, 50, and 100. | Raw sums are 31, 30, and 28. Pair-count means are all exactly 0.04. With a log2-Gaussian prior of width 0.5 octaves, centers of 240, 120, and 60 BPM choose their respective candidates. |
| Length 1600. Place pulses at $20+50j$ and alternate strengths 1 and 0.25. | Pair-count means at 50 and 100 frames are 0.005 and 0.010625, respectively. An accent every other beat can favor the slower interpretation. |
| Length 400. Start with pulses at $20+50j$. Set the pulse at 170 to zero, and add strengths 0.8 at 145 and 0.7 at 245. | With $P=50$ the best path retains all eight nominal beats and gives score 7. The beat at frame 170 is inferred from its neighbors. Scaling the input by 10 at the original penalty replaces 170 with 145. Scaling both input and penalty by 10 restores the path at score 70. |
| Length 400. Give pulses only at 20, 70, 120, 320 and 370. Also test a tape of all zero. | The same $P=50$ path fills 170, 220, and 270 during the longer quiet run. All-zero input has no positive path. A coast limit needs its own verification. |
| Two length-300 tapes share a 200-frame prefix with pulses at $10+25j$. Add further pulses at 210 and 260 to the first tape, and at 235 and 285 to the second. | At 120 BPM the whole-tape phase sums prefer phase 10 in the first and 35 in the second. A decision made within the shared prefix has the same evidence in both cases. |
| At 137 BPM use $P=6000/137$ frames. Start at frame 7 and generate 100 beats. | Repeating the rounded 44-frame step drifts +202.3358 ms at beat index 99. Rounding each ideal phase to the nearest frame gives maximum absolute error 4.9635 ms. With a 960-sample window and origin $2^{60}+37$, frame 20 is exactly $20159/2$ samples relative to the origin. |

**Tempo change.** Use a length-1200 tape. Before frame 600 put pulses at
$20+60j$. From frame 600 put pulses at $600+40j$. Raw autocorrelation
over the two 600-frame intervals and lags 30–100 selects periods 60 and
40 (100 and 150 BPM). With a known boundary and those two periods supplied
at the candidate frames, the path matches all 25 reference beats. Holding
the first target period gives 15 matches, 5 extra beats, and 10 misses
at 70 ms tolerance, or $F_1=2/3$. The supplied-period result uses the
known segmentation and exercises the path stage on this controlled change.

**Scoring.** The reference is 16 beats at $25+50j$. Also score every
second reference beat, 32 beats at $25+25j$, and all reference beats
shifted later by 25 frames. One-to-one matching at 70 ms gives
$F_1=1,2/3,2/3,0$ for the exact, half-rate, double-rate, and offbeat
cases. A tempo-only check accepts the offbeat rate.

**Differential and exhaustive checks.** Use NumPy PCG64 seed
370020 and draw uniform $[0,1)$ values for each length. Compare direct
autocorrelation with a real FFT for $(T,N_{\mathrm{FFT}})$ equal to
$(31,64),(64,128),(67,256),(257,513)$. Across 419 nonnegative lags the
maximum absolute difference was $2.843\times10^{-14}$ in squared
synthetic feature units. SciPy 1.17.0 direct correlation differed by
at most $2.132\times10^{-14}$. For 48 nine-frame cases with NumPy PCG64
seed 370037, draw novelty as integers 0–7 divided by 4, then independent
per-frame periods as integers 2–4. Use $\lambda=3$. Enumerate all
feasible nonempty beat subsets and the zero score of an empty path.
The returned score and the independently re-scored path both matched the
exhaustive optimum to $8.882\times10^{-16}$ score units. These were numerical and
synthetic checks using NumPy 2.3.5, with library behavior referenced
from the published documentation.

## Next action

Implement a bounded offline period and beat-path reference that preserves
the input clock, accepted period hypotheses, and per-beat evidence.
Review the equal-tempo shifted tracks, prior-driven octave tie, one
missed pulse, and prolonged quiet span before using the path in a live
consumer. Check gaps, brief clips, dense syncopation, weak evidence,
clock changes, and rate or chunking invariance. Add streaming phase
commitment and resynchronization with explicit tests on a shared prefix.
Score phase, continuity, and signed timing on annotated music before
selecting production priors or confidence thresholds.

## Revisit when

The feature clock, normalization, tempo range or prior, period model,
metrical target, weak-evidence policy, or delivery latency changes.
