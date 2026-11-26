# Beat tracking contract

[Clock](#input-clock-and-readiness) · [Period](#period-evidence) ·
[Path](#beat-path) · [Weak support](#weak-support-and-gaps) ·
[Evaluation](#evaluation) · [Reference](#offline-reference)

## Input clock and readiness

A beat is a position in a recurring pulse. Tempo gives the pulse rate.
Phase gives its alignment to the recording. State the metrical level
and the listener's task before selecting or scoring a track. A
syncopated onset can fall between beats. An inferred beat can fall
inside a pause. Use meter evidence to identify the first beat of a bar.
[Ellis, ``1–2](https://doi.org/10.1080/09298210701653344) ·
[Böck, Krebs and Widmer](https://zenodo.org/records/1415836)

Start with continuous positive spectral flux from Skill #36. Record
the tap, channel or mix, units, epoch, frame geometry, calibration, and
novelty settings. Preserve the original frame indices when a region is
cropped or split. A supported zero gives evidence of a weak change.
An unavailable point marks a break in the sequence used for alignment.
[Onset frames and scoring](../../audio-onset-detection/references/ONSET_DETECTION_CONTRACT.md#frames-and-clock) ·
[Timebase and epochs](../../audio-timebase-sync/SKILL.md)

For sample rate $f_s$ and hop $H$, the feature rate is $r=f_s/H$.
A period of $P$ frames gives $60r/P$ BPM. For frame start
$s_t=s_0+tH$ and length $M$, keep the exact center $2c_t=2s_t+M-1$.
Convert the difference from the chosen origin to seconds when displaying
elapsed time. For fixed-tempo scheduling, accumulate the exact period
before converting each ideal position to a discrete grid. Record the
rounding rule. A sequence of rounded intervals can drift.

Report the center estimate and the end-exclusive data boundary used to
make the decision. The novelty for a causal comparison can use the
frame end. A picked onset can require additional right-flank frames.
The offline reference analyzes the whole supplied run, so its ready
boundary is the last supplied frame end. Any observed delivery boundary
comes from the caller. For live use, declare whether each beat is
predicted, committed after observing it, or revised. Test a shared
prefix with different future audio. Measure acquisition and dispatch on
the target host.
[Onset readiness](../../audio-onset-detection/references/ONSET_DETECTION_CONTRACT.md#peak-selection-and-readiness) ·
[Audio buffering](../../audio-stream-buffering/SKILL.md)

## Period evidence

Take a contiguous sequence of $T$ valid novelty values. Choose a
preprocessing rule and call its output $u[t]$. The reference uses
a rectangular observation interval and optional removal of its mean.
Measure the linear autocorrelation at positive lag $p$.

$$
R[p]=\sum_{i=0}^{T-1-p}u[i]u[i+p].
$$

Keep both the raw sum and the mean product $R[p]/(T-p)$. A steady
floor can contribute to every lag. Compare centered evidence when the
floor dominates. A short overlap can give a large mean from few
pairs. Require enough valid pairs and observation time for the
longest retained period. If FFT evaluation is needed, pad the length
to at least $2T-1$ and compare the result with direct sums.
[Müller, autocorrelation tempogram](https://www.audiolabs-erlangen.de/resources/MIR/FMP/C6/C6S2_TempogramAutocorrelation.html) ·
[Linear correlation verification](../../audio-cross-correlation/SKILL.md)

For $B_{\min}\le B\le B_{\max}$, search integer lags from
$\lceil60r/B_{\max}\rceil$ through $\lfloor60r/B_{\min}\rfloor$.
Keep lags between one and $T-1$. The reference qualifies each lag
using its pair count and $\lfloor(T-1)/p\rfloor$ complete intervals
in the grid. The interval count describes available support. Inspect
the measured products before interpreting sparse evidence.

Expose eligible positive peaks of the chosen score. Retain the
members of a peak plateau and inspect search-boundary peaks. Keep
half-rate, double-rate, and other plausible periodicities when they
appear. Leave tempo unavailable for a flat input, flat positive lag
curve, missing usable evidence, or unresolved top tie. If a prior
breaks an evidence tie or promotes a different candidate, record
that decision. For candidate evidence $E>0$, maximum evidence
$E_{\max}$, prior center $B_0$, and width $\sigma$ octaves, the
reference ranks with

$$
\log(E/E_{\max})-\tfrac12(\log_2(B/B_0)/\sigma)^2.
$$

Without a prior, it ranks by the chosen autocorrelation score. Keep
that score with the prior-weighted rank.

Period evidence can agree between two different phases. For a trial
integer period $P$, sum each offset's novelty on a common number of
cycles. The reference uses the leading complete cycles of the
supplied interval. When comparing phase positions, add the original
frame address of the interval. At a tempo change, report the bounds
of each period-estimation window. A longer window gains repetitions
and can mix both tempos. A shorter window can respond faster and lose
support.
[Müller, local tempo](https://www.audiolabs-erlangen.de/resources/MIR/FMP/C6/C6S2_TempogramAutocorrelation.html#short-time-autocorrelation) ·
[Time-varying beat tracking example](https://librosa.org/doc/0.11.0/auto_examples/plot_dynamic_beat.html)

## Beat path

For one valid array with nonnegative novelty $v[t]$, use a specified
period $P_t$ in frames at the arriving node. It can be fixed, chosen
from period evidence, or supplied for each frame. Keep only positive
steps $t-s$ from $\lceil P_t/2\rceil$ through $\lfloor2P_t\rfloor$.
With a nonnegative penalty weight $\lambda$, compute

$$
D[t]=v[t]+\max\!\left(0,\ \max_{s\text{ admissible}}
       \left[D[s]-\lambda\log^2\!\left(\frac{t-s}{P_t}\right)\right]\right).
$$

Use the natural logarithm. The zero option restarts the path. Save the
earliest predecessor among equal positive continuations. Backtrack
from the earliest maximum endpoint with positive score. A zero
maximum gives an empty path. Treat equality in the represented scores
as an exact tie. This chooses a maximum of the stated objective for
the supplied period model and eligible edges.
[Ellis, ``2–3](https://doi.org/10.1080/09298210701653344) ·
[Müller, dynamic programming](https://www.audiolabs-erlangen.de/resources/MIR/FMP/C6/C6S3_BeatTracking.html)

The weight has the same scale as the novelty reward. Scale it with
the input when testing a uniform gain change. Scale any strength
gates that operate on that novelty as well. Path sums can favor
dense beat grids because each selected node adds reward. Compare
tempo evidence on common support. A fixed-period path illustrates
phase alignment. A supplied period change tests interval fitting
across a known transition. Test automatic transition detection
separately with an interval and tempo-estimation policy.

When comparing to librosa, record its supplied or estimated tempo,
onset normalization, local score smoothing, interval cost, edge
trimming, and frame-to-time mapping. For an implementation
differential, match those choices before comparing beat positions.
[librosa 0.11.0 beat tracker](https://librosa.org/doc/0.11.0/generated/librosa.beat.beat_track.html) ·
[librosa 0.11.0 implementation](https://librosa.org/doc/0.11.0/_modules/librosa/beat.html)

## Weak support and gaps

Use a novelty gate in the input's units. The reference calls an
observation supported when its score exceeds the gate. Within a
contiguous valid run, split between consecutive supported observations
when their sample distance exceeds the declared cap. Equality stays in
one span. Start and end each admitted span at its first and last
supported observation. Exclude missing records and unavailable features
from the spans. A changed epoch, grid or feature profile starts a
new call.

Keep the distinction between a measured supported beat and an
inferred position from interval fitting. One missed pulse can be a
valid interpolation. A long allowed edge can jump across silence
with zero weak nodes in the path. Check elapsed support as well as any
limit on the count of inferred beats. Preserve isolated observations
as diagnostics. Require two supported nodes on the selected path to
report a track. A large selected novelty identifies local change.
Verify its metrical meaning against the label convention.

| Observation | Engineering check |
| --- | --- |
| Correct BPM and beats that fall between the intended pulses. | Compare candidate phases and the clock origin. Check offbeat annotations. |
| Repeated tempo changes by a factor of two. | Inspect alternate-period evidence, support windows, and prior weight. |
| A beat is missing during syncopation. | Inspect competing phase paths and the evidence-to-penalty scale. |
| The grid continues through a pause. | Check the longest time between supported observations and the interval limit. |
| The estimate fits offline and arrives late in use. | Report the frame support, tracker lookahead, delivery boundary, and dispatch separately. |

## Evaluation

Declare the eligible intervals and a target pulse level before matching.
Keep misses inside those intervals in the evaluation. Use a uniform
inclusive tolerance and match beats one-to-one. Retain reference
and estimate identities and signed error, estimate minus reference.
Report true positives, extra beats, missed beats, and $F_1$ alongside
tempo and timing error. Use exact doubled sample coordinates on a
shared clock. For tolerance $\tau$ seconds, use integer tolerance
$\lfloor2f_s\tau\rfloor$ on that grid.

Report correct-metrical-level and alternate-metrical-level continuity
when half-rate or offbeat behavior matters. The mir_eval F-measure
default is 70 ms. Its separate startup-trim function defaults to
5 seconds. State the trim and score startup when a consumer needs
a lock-time assessment. Use held-out annotated audio to evaluate
field settings. Include ambiguous annotations, tempo changes,
and weak and sustained inputs.
[Exact event matching](../../audio-onset-detection/references/ONSET_DETECTION_CONTRACT.md#evaluate-the-detector) ·
[Beat metrics and continuity](https://mir-eval.readthedocs.io/latest/api/beat.html)

## Offline reference

The [reference](../scripts/reference_beat_tracking.py) and
[fixtures](../../../tests/fixtures/AUDIO_BEAT_TRACKING_GOLDENS.md) use
the repository's merged onset records. Use the script directories shown
in the [tests](../../../tests/test_audio_beat_tracking_reference.py).

- Use `estimate_tempo` with a contiguous score array and feature rate.
  `TempoSearch` names the BPM band, preprocessing, aggregation, support
  thresholds, and optional `TempoPrior`. The default band is 60–240 BPM,
  with at least eight pairs and two complete intervals. The default
  score is the uncentered mean product. Each lag retains its raw and
  overlap-normalized evidence. The output gives candidate peaks and
  an explicit status.
- Use `phase_scores` to compare phase sums on equal complete-cycle
  support. Use `align_beats` to check the unrestricted objective on
  one contiguous array. It takes a scalar period or one period per
  frame. Its path indices are relative to the supplied array.
- Use `track_beats` with continuous `NoveltyPoint` records and a
  `BeatProfile`. Set the maximum observation gap in samples. The
  default gate is zero and interval weight is eight. Each admitted
  segment has its original first and last frame indices, a path from
  that segment's first frame, and a tempo result when estimated.
  A supplied period array follows the input records, including
  unavailable records. The output keeps its continuous input and
  reports qualified beat positions with their source frames,
  target periods, and support flags. An isolated or unqualified
  segment remains in the result with its status.
- Supply at most 4,096 frames per call. Periods range from one to
  4,096 frames. The reference uses exact rational coordinates,
  scalar input values, correlations, and score arithmetic where
  the operations permit it. Natural log evaluations introduce
  binary64 precision. Original frame indices are relative to the
  declared grid's first start. Frame readiness is end-exclusive.

Use the fixture results to check the numerical and timing contracts.
Field priors, beat accuracy on annotated audio, and live delivery
timing need their own evidence.
