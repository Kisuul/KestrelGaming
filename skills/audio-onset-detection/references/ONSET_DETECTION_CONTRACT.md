# Onset detection contract

[Frames](#frames-and-clock) · [Novelty](#novelty) ·
[Peaks](#peak-selection-and-readiness) · [Evaluation](#evaluate-the-detector) ·
[Reference](#offline-reference)

## Frames and clock

Define the event and the label convention at the measured tap. An
onset is a point on the time axis. Its attack can span many samples.
For a synthetic signal, use its first active sample. For annotated
music, record how the labels describe an attack, pitch change, or
overlap. Record the tap location relative to routing, gain, and other
processing. Name the analyzed channel or document the mix recipe.
[Bello et al., 2005](https://doi.org/10.1109/TSA.2005.851998) ·
[Analysis provenance](../../audio-analysis-provenance/SKILL.md)

Use window length $M$, hop $H$, and real DFT length $N\ge M$. Use
$1\le H\le M$. Frame $t$ covers $[s_t,s_t+M)$, where $s_t=s_0+tH$.
Supply complete frames on that grid. Preserve the center as the exact
integer $2c_t=2s_t+M-1$. Divide by $2f_s$ for seconds from clock sample
zero. Subtract twice the chosen origin first for elapsed seconds.

The frame interval is $H/f_s$. The bin spacing is $f_s/N$. The
window shape and length control time support and leakage. Increasing
$N$ by zero-padding samples the same windowed spectrum on a denser
grid. For a comparison at lag $L$, frame centers are $LH/f_s$ apart.
[STFT geometry](../../audio-spectrogram-waterfall/references/STFT_WATERFALL_CONTRACT.md#frame-geometry) ·
[Clock and epoch handling](../../audio-timebase-sync/SKILL.md)

Copy the originating clock, epoch, exact rate, units, and analysis
channel into the frame provenance. Make a new run after a gap, seek,
or incompatible input or profile change. Clear the lag, the trailing
scores, and the last accepted peak together. A callback partition
changes when data arrive. The declared frame grid stays fixed.
[Stream buffering](../../audio-stream-buffering/SKILL.md)

## Novelty

With signed real PCM $x$ and window $w$, form the one-sided
peak-amplitude bins $A_{t,k}=d_k|X_{t,k}|/\sum_j w_j$. Here $X_{t,k}$
is the DFT of the windowed frame. Use $d_k=1$ at DC and at even-$N$
Nyquist. Double all paired positive bins, including the highest bin
for odd $N$. Require a positive coherent sum. Preserve the same
calibration and bin grid across compared frames.
[STFT ordinate](../../audio-spectrogram-waterfall/references/STFT_WATERFALL_CONTRACT.md#spectral-ordinate-and-visualization)

Use $S=A$ for the plain amplitude profile. For compression use
$S=\log(1+A/A_0)$ with one declared $A_0>0$ in amplitude units
for the entire run. At lag $L\ge1$, positive flux is

$$
V_t=\sum_{k=0}^{\lfloor N/2\rfloor}u_k [S_{t,k}-R_{t-L,k}]_+,
\qquad [z]_+=\max(0,z).
$$

Use fixed nonnegative weights $u_k$. Start with unit weights and
$R_{j,k}=S_{j,k}$. For radius $r$, set $R_{j,k}$ to the maximum of
$S_{j,q}$ for $|q-k|\le r$ on the available bin grid. Clip at DC
and the highest bin. Keep each positive weighted contribution before
the sum. Bin count, weights, lag, radius, calibration, and compression
affect the scale. Tune each score threshold in its own units.

The radius includes the current bin of the earlier spectrum. When
the other settings agree, the filtered score is at most the plain
score at each supported frame. In the reference, the maximum can
act on amplitudes because compression is monotone. For an increase
above earlier amplitude $A_\mathrm{ref}$, the log difference is
$\log(1+(A-A_\mathrm{ref})/(A_0+A_\mathrm{ref}))$. Use this form to
avoid subtracting two nearly equal logarithms.
[Dixon, 2006](https://www.dafx.de/paper-archive/2006/papers/p_133.pdf) ·
[Böck and Widmer, 2013](https://www.cp.jku.at/research/papers/Boeck_Widmer_DAFx_2013.pdf)

Calculate weighted RMS on the same frame.

$$
E_t=\sqrt{\frac{\sum_{j=0}^{M-1} w_j^2x[s_t+j]^2}{\sum_{j=0}^{M-1} w_j^2}},
\qquad D_t=[E_t-E_{t-L}]_+ .
$$

Keep both $D_t$ and $V_t$ in the novelty curve. Mark the first $L$
frames unavailable for comparison. Measured silence after warm-up
has supported zero novelty. Compare only after the full earlier
frame exists. A uniform gain change between runs scales plain
amplitude flux and RMS rise. Frame-by-frame peak normalization can
erase an amplitude attack. Use a level control with a known gain
to check the units and gain response.
[Spectral-descriptor flux conventions](../../audio-spectral-descriptors/references/SPECTRAL_DESCRIPTORS_CONTRACT.md#frame-to-frame-flux)

## Peak selection and readiness

Select one score $z_t$ from $V_t$ or $D_t$. Use left flank $a\ge1$,
right flank $b\ge1$, and a background of $B\ge1$ preceding scores.
Use margin $\delta\ge0$ in the selected score's units. Require
every score in the flanks, background, and candidate to be available
in one run. Apply these conditions to the calculated scores.

- Require $z_t$ to exceed every score in the $a$ left frames.
- Require $z_t$ to equal or exceed every score in the $b$ right frames.
  These two flank rules select the first eligible point of a plateau.
- Require $z_t$ to exceed the median of the preceding $B$ scores
  plus $\delta$. For an even count, average the middle two. The
  candidate is outside the background span.
- Accept peaks in order. Require $2c_t-2c_\mathrm{last}\ge2R$ for
  minimum separation $R$ samples from the last accepted peak.

For $T$ complete frames, the zero-based candidate index must satisfy
$L+\max(a,B)\le t\le T-1-b$. Keep unavailable or pending intervals in
the evaluation record. The first ready input boundary for a candidate
is the exclusive end of its last right-flank frame.

$$
r_t=s_t+M+bH.
$$

The nominal event estimate is $c_t$. The wait from that estimate to
earliest readiness is $(r_t-c_t)/f_s$. Compare readiness with the
label when measuring the delay from the event itself. A callback
can deliver the final required sample in a later block. Save the
observed sample-domain boundary when known. Processing and dispatch
latency need their own measurements. Declare any lookahead used to
produce features. If a later editing step moves the event estimate,
preserve the original peak center and readiness and record the
adjustment method.
[Peak-picking conventions](https://librosa.org/doc/0.11.0/generated/librosa.util.peak_pick.html) ·
[Stream timing](../../audio-stream-buffering/SKILL.md)

## Diagnose errors

| Observation | Check | Engineering choice |
| --- | --- | --- |
| Flux rises and RMS stays steady. | Check the bins that gained amplitude and the label convention for pitch changes. | Use spectral flux if a new spectral component qualifies. |
| Vibrato gives repeated peaks. | Compare plain and filtered flux on measured steady notes and weak added notes. | Set the radius and lag from pitch movement in bins. Retune the threshold on the filtered curve. |
| Filtered flux misses a quiet attack. | Compare the quiet bin with the strongest earlier neighbor inside the radius. | Test a smaller radius, different band weights, or RMS rise on the target channel. |
| A slow attack peaks late. | Compare first active sample, steepest rise, and readiness. | Declare which point the task needs. Validate any correction against slow and fast attacks. |
| A center appears before the first active sample. | Check which full window contained the impulse and when its right flank completed. | Keep the estimate and the readiness boundary in the record. |
| A mixed onset disappears. | Compare source channels, polarity, and the delivered mix. | Select an input where the event exists. Record the channel selection. |
| A release, splice, or gain jump gives a peak. | Inspect the signal before and after the change for new components and gain changes. | Use the event definition and representative labeled examples to tune qualification. |

When magnitude is steady through a phase reset, both curves can be
quiet. If such a reset qualifies, evaluate a phase-prediction feature
with reliable phase history and sufficient bin level. Record its
support and check discontinuity handling.
[Mid/Side and mono retention](../../audio-mid-side-analysis/SKILL.md) ·
[Phase-based alternatives](https://www.dafx.de/paper-archive/2006/papers/p_133.pdf)

## Evaluate the detector

Declare each eligible interval and a uniform inclusive tolerance.
Use one clock and one eligible interval for each match. Supply labels
and estimates within the interval. Keep separate coverage for data
gaps, warm-up, and incomplete right flanks. State the annotation
policy and the tolerance in samples or seconds. For tolerance $\tau$
seconds, use $\lfloor 2f_s\tau\rfloor$ for an integer doubled-sample
tolerance. An event at integer sample $s$ has coordinate $2s$.

Sort labels and detections by exact time with input order for ties.
Discard the earlier event if it is outside tolerance of the other
list's first remaining event. Otherwise pair them and advance both.
The earlier event in a discarded pair has no feasible later partner.
For a feasible pair of earliest events, any feasible crossed matches
can be uncrossed within the same tolerance. If only one earliest
event has a match, pair the two earliest events in its place. The
rule gives maximum cardinality and fixes a deterministic timing
tie rule.

Return pair identities and signed error, estimate minus label. Count
one true positive (TP) per match, one false positive (FP) per unmatched
detection, and one false negative (FN) per unmatched label. Report
precision $TP/(TP+FP)$, recall $TP/(TP+FN)$, and
$F_1=2TP/(2TP+FP+FN)$. A zero denominator gives an unavailable metric.
Report the timing errors and the readiness delays alongside these scores.

Choose settings on different audio from the final set. Include
percussive, gradual, quiet, pitched, and mixed attacks. Report the
errors by event type when the overall score obscures the failure mode.
Preserve the novelty grid for downstream beat tracking.
[Maximum event matching](https://mir-eval.readthedocs.io/latest/api/util.html#mir_eval.util.match_events) ·
[Onset evaluation](https://mir-eval.readthedocs.io/latest/api/onset.html)

## Offline reference

The [reference module](../scripts/reference_onset_detection.py) uses
the repository's [scope epoch](../../audio-oscilloscope/scripts/reference_oscilloscope.py),
[exact RMS rounding](../../audio-stereo-correlation/scripts/reference_stereo_correlation.py),
and [shared STFT](../../audio-spectrogram-waterfall/scripts/reference_stft.py).
Make the four script directories available for imports as in the
[regression tests](../../../tests/test_audio_onset_detection_reference.py).

- Use `OnsetGrid` for one channel or mix. Supply the actual window
  coefficients. Set the first start to the epoch origin or an explicit
  later sample. Set lag, radius, weights, optional log reference, score
  source, and peak parameters in `OnsetProfile`. The defaults use
  lag one, unit weights, plain flux, radius zero, left and right flanks
  of one, four preceding scores, zero margin, and no separation.
- Supply each `OnsetFrame` with an exact start and end, calibrated
  amplitudes, and weighted RMS. All values come from that complete
  frame. The producer is responsible for calibration and valid input
  support. Supply frames serially to `OnsetDetector.push` in grid order.
  The return value gives the current novelty and any peak confirmed
  by that submission. The novelty retains the frame, detection
  profile, and earlier frame start when supported. Add a known
  release boundary to the confirming submission. Supplied boundaries
  must be nondecreasing and at least
  the submitted frame's end. `reset` requires a new epoch ID.
- Feature frames allow $2\le N\le4096$. Lag and each context
  span are at most 128 frames. The radius can extend across the
  nonnegative bin grid. Frame coordinates are bounded by the scope
  sample-index convention. The detector retains bounded history across
  an iterable run. Absent lagged scores are `None`.
- Inputs use finite binary64 values or exactly representable integers.
  Plain differences, weighted products, sums, and threshold
  comparisons use exact rationals from those represented values.
  Logarithmic differences round to binary64 before weighting.
  Positive log changes that round to zero produce a range error.
  Invalid input leaves detector state available for a corrected retry.
- Use `analyze_pcm_chunks` for short mono fixtures. Give contiguous
  nonempty blocks as pairs of start sample and PCM. It uses the shared
  STFT's limits of 512 transform points and 128 complete frames, and
  derives weighted RMS from precisely the same samples and window.
  It maps each confirmed peak to the callback end that first delivers
  its full right flank. Nonfinite amplitudes and weighted nonzero frames
  that collapse to a zero spectrum or zero RMS raise an error. Binary64
  bins near cancellation retain the shared STFT's numerical floor.
  Use calibrated feature frames from a separate FFT for wider fixtures.
- Pass exact doubled sample times to `match_onsets` with an inclusive
  doubled tolerance and a half-open eligible interval. It returns
  original indices in the match and unmatched records. The caller
  aligns clocks and defines valid intervals before matching.

The reference is for offline procedures and deterministic tests. Field
thresholds, annotated-audio accuracy, host scheduling, and deployment
timing require separate measurement.
