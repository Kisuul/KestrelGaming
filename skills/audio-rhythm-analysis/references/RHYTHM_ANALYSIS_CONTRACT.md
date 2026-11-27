# Rhythm analysis contract

[Clock](#clock-and-inter-onset-intervals) ·
[Phase](#beat-coordinates-and-readiness) · [Subdivisions](#subdivision-evidence) ·
[Swing](#swing-and-periodicity) · [Reference](#offline-reference)

## Clock and inter-onset intervals

Name the pulse and accepted onset events. Record the voice or mix,
tap, epoch, exact sample rate, and capture intervals. Keep event IDs.
If two observations refer to one musical event, declare the
association before measuring. Apply the measured clock mapping
and tap alignment before comparing channels. Use integer doubled
sample coordinates to preserve half samples and large origins.
[Timebase](../../audio-timebase-sync/SKILL.md) ·
[Onset detection](../../audio-onset-detection/SKILL.md)

For one voice in one continuous capture, sort accepted events by
time. Preserve input order for equal times. For adjacent doubled
coordinates $t_2$ and $s_2$ in increasing order, the inter-onset
interval is $(s_2-t_2)/2$ samples. Divide by the exact rate for
seconds. Distinct simultaneous events give a zero interval. Restart
the succession at a capture gap or changed epoch. A long gap in
beat evidence can still occur within continuous event capture.
Use both events' data boundaries and a known ordering before
reporting an interval in a live system.

## Beat coordinates and readiness

Supply ordered beat anchors, with their source status. Use consecutive
anchors in one beat segment and capture. Bracket an event by
$b_j\le t<b_{j+1}$. The local duration and phase are

$$
\Delta_j=b_{j+1}-b_j,\qquad u=\frac{t-b_j}{\Delta_j}.
$$

The ratio is the same with doubled coordinates. Preserve the event,
both anchor IDs, and the local beat index and duration. An event at
a shared anchor belongs to the interval on its right when that
interval exists. A right anchor can coincide with the end-exclusive
capture boundary and close the preceding interval. Events themselves
lie inside the capture's half-open interval. A final anchor with
no right bracket leaves phase unavailable.

Preserve the beat track's qualified segments. A capture gap
or a break between those segments leaves phase unavailable. For an
inferred anchor, apply the declared policy and keep its source status.
A predicted anchor can support a provisional live estimate. The
confirmed reference retains the prediction's identity and marks
phase unavailable. A supported beat from the tracker means the local
novelty qualified under its gate. Check annotations for metrical meaning.
[Beat path and support](../../audio-beat-tracking/references/BEAT_TRACKING_CONTRACT.md#weak-support-and-gaps)

When all components are known, readiness is the maximum of the
event and both anchors' end-exclusive data boundaries. For an IOI
use the maximum over its two events. A supplied label can already
be available when the run starts. Keep an unknown component
unavailable. Combine observed delivery boundaries only when all
components have a measurement on the same mapped clock. Measure host
dispatch separately.

Use Skill #36's onset estimate and readiness. Its ready boundary
includes the required right flank. Use Skill #37's beat positions and
whole-run boundary together. Its offline analysis can consume data
well after the nominal beat. The beat center identifies the estimated
position in the recording.
[Onset readiness](../../audio-onset-detection/references/ONSET_DETECTION_CONTRACT.md#peak-selection-and-readiness) ·
[Beat readiness](../../audio-beat-tracking/references/BEAT_TRACKING_CONTRACT.md#input-clock-and-readiness)

## Subdivision evidence

For a grid with $q$ subdivisions, calculate exact positions

$$
g_k=b_j+k\Delta_j/q,\qquad k=0,\ldots,q .
$$

Compare the nearest candidates around $q u$. Keep all nearest
positions on a tie. Store signed residual $t-g_k$ in samples and
$(t-g_k)/\Delta_j$ in beat units. Use fractions for grid positions
that fall between sample ticks. Canonicalize $k=q$ as slot zero of
the next anchor. An event just before that anchor retains its
phase in the preceding beat. Its residual to the next slot is
negative.

Use one eligible event set and a common inclusive tolerance in
samples or beats for all grid hypotheses. The reference weights
each accepted event equally. Use a common reference rate when
comparing sample residuals as time across captures. Report the
phase-eligible count, matching count, and residuals. A tie counts
as one event. Keep its
two signed residuals and leave its slot occupancy ambiguous. Count
distinct beat anchors supporting each unambiguous matched slot.
Include the unmatched events when summarizing absolute residuals.

A finer grid can contain every point of a coarser grid. Extra slots
can lower the timing error with sparse evidence. Inspect the
repeated support for each proposed slot and voice before selecting
a grid. State any density preference and keep the alternative
measurements.

## Swing and periodicity

For one labelled interior offbeat in a beat and voice, use
$u/(1-u)$ as the long-to-short ratio. Keep multiple offbeat labels
in the same beat and voice visible as ambiguity. Use the label
convention to qualify near-anchor events. A triplet grid point can
match the long part of a 2:1 subdivision. Check independently
marked offbeats and beat anchors before interpreting a groove.

Let $e_t,e_L,e_R$ be event, left-anchor, and right-anchor errors.
For a positive perturbed interval and unchanged bracket,

$$
\hat u-u =
\frac{e_t-(1-u)e_L-u e_R}{\Delta_j+e_R-e_L}.
$$

Check both event timing and anchor timing. Plot or summarize
ratios by local tempo and voice. A fixed-BPM grid can misrepresent
straight timing across tempo changes. A ratio near the right
anchor is sensitive to small phase changes. Friberg and Sundström
measured variation with tempo and performer role in their jazz
recordings.
[Friberg and Sundström, 2002](https://doi.org/10.1525/mp.2002.19.3.333)

Use short-time autocorrelation or a Fourier tempogram as supporting
evidence. Record the novelty feature rate, analysis interval,
window, and normalization. At feature rate $r$, Fourier frequency
$\nu$ Hz corresponds to $60\nu$ BPM. Autocorrelation lag $p$ gives
$60r/p$ BPM. An autocorrelation can also support multiples of a
lag. Fourier magnitudes can peak at a harmonic of the pulse rate.
Keep unfolded candidates when comparing a cyclic representation
that groups rates a power of two apart. Preserve enough cycles
for the slowest candidate. Evaluate local timing at transitions.
[Beat period evidence](../../audio-beat-tracking/references/BEAT_TRACKING_CONTRACT.md#period-evidence) ·
[Grosche, Müller and Kurth, 2010](https://www.audiolabs-erlangen.de/content/resources/MIR/tempogramtoolbox/2010_GroscheMuellerKurth_TempogramCyclic_ICASSP.pdf)

A pulse grid and its subdivisions can fit more than one meter.
Use independent bar-level accents or other annotated cues to
locate a downbeat. Measure held-out examples by voice and pulse
level when choosing field tolerances.
[Joint beat and downbeat evidence](https://www.cp.jku.at/research/papers/Boeck_etal_ISMIR_2016.pdf)

## Offline reference

Use the [reference](../scripts/reference_rhythm_analysis.py) with the
script directories in the [tests](../../../tests/test_audio_rhythm_analysis_reference.py).
The reference provides bounded numerical measurements on a supplied
grid. Use the [fixtures](../../../tests/fixtures/AUDIO_RHYTHM_ANALYSIS_GOLDENS.md)
to exercise edge cases.

- A `RhythmCapture` names one continuous acquisition interval
  on a comparison `ScopeEpoch`. Within an epoch, use consistent
  mapped provenance and disjoint intervals. Independent epochs can
  share numerical coordinates. Supply `RhythmEvent` with a unique
  ID, voice, timestamp, capture, and any availability and offbeat
  label. The origin of the epoch and its exact rate remain in the
  record.
- A `BeatGridSegment` carries strictly increasing `BeatAnchor`
  records. Neighboring segments can meet at a boundary. Each anchor
  ID identifies one record within a capture. Use `event_from_onset`
  and `beat_segments_from_track` with the merged upstream records
  on the mapped clock. The beat adapter preserves only paths with
  reported beats. Its timing comes from the full upstream run.
  The supplied capture determines beat and event eligibility.
- `analyze_rhythm` returns IOIs, an ordered result per input event,
  evidence for each requested subdivision count, and results for
  explicitly labelled offbeats. The phase result states its
  availability reason and keeps both anchors when the bracket is
  rejected by the source policy. The default profile compares
  two, three, and four subdivisions at exact match tolerance
  and accepts inferred anchors. Choose a tolerance for the task.
- Supply lists or tuples with at most 4096 events and 4096 beat
  anchors per analysis. Each subdivision count is an integer
  from 1 to 64. Use exact rational tolerances when a precise
  boundary matters. Input positions and readiness stay on the
  declared sample clock. Convert residuals and ratios for display
  after the comparisons.

When reviewing a result, include its clock, input support,
subdivision settings, anchor provenance, per-voice evidence, and
unavailable positions. Use explicit labelled examples to evaluate
musical interpretation and any real-time policy.
