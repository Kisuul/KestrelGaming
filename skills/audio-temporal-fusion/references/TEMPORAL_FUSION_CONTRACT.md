# Temporal fusion contract

[Clock mapping](#clock-mapping) ·
[Association and coverage](#association-and-coverage) ·
[Readiness and commitment](#readiness-and-commitment) ·
[Verification](#verification) · [Reference](#bounded-reference)

## Clock mapping

Declare one event definition, one master sample epoch, and
the sources expected for a continuous association run.
Identify the native sample clock, tap, epoch and rate for
each source. Keep the source and event IDs and the revision.
Supply the event position, original half-open input supports,
and exclusive input readiness. Record reported evidence
delivery in its native domain when known.

For a locked source with rate $F_s$, master rate $F_m$,
and a known anchor correspondence $(u_0,m_0)$, use

$$
m(u)=m_0+(u-u_0)\frac{F_m}{F_s}.
$$

Use exact rational positions through association. Apply the
map within its declared validity. An event label must lie
within the half-open validity interval. An input support end
or readiness boundary can equal the interval end. Keep
unmapped evidence visible. A mapped label can have unknown
readiness when its input-ready boundary exceeds the map.
Keep the original anchor when cropping a valid mapping.

A rate ratio gives a nominal coordinate conversion. Keep
the filter support and lookahead used to produce a
resampled observation. Independent devices need measured
anchors, a drift model where applicable, and an alignment
error budget. Calibrate the relative tap delay before
interpreting a timing difference as disagreement. Change
the mapping and begin a new run when its continuity fails.
[Timebase](../../audio-timebase-sync/references/TIMEBASE_CONTRACT.md) ·
[Resampler support](../../audio-resampling/references/RESAMPLING_CONTRACT.md#explicit-filter-and-delay)

PortAudio identifies the first input sample's ADC time,
the callback invocation time, and the first output sample's
DAC time. Use the anchor relevant to the signal path. Keep
the dispatch clock named and establish its relation to the
sample clock before subtracting time values.
[PortAudio timing fields](https://portaudio.com/docs/v19-doxydocs/structPaStreamCallbackTimeInfo.html) ·
[Analysis provenance](../../audio-analysis-provenance/references/PROVENANCE_CONTRACT.md)

| Observation | Evidence to carry |
| --- | --- |
| Measured onset | Use the peak label and its confirmation readiness. Include the comparison and peak-selection dependencies in the support. Keep the observed release when supplied. |
| Offline beat | Keep the beat label and whether novelty supports it or the path infers it. Carry the run readiness and tempo and path dependencies. Mark a live forecast as a prediction. |
| Selected segment cut | Use the exact midpoint and the peak support, readiness, and reported release. Keep the comparison score readiness for diagnosis. |

[Onset readiness](../../audio-onset-detection/references/ONSET_DETECTION_CONTRACT.md#peak-selection-and-readiness) ·
[Beat readiness](../../audio-beat-tracking/references/BEAT_TRACKING_CONTRACT.md#input-clock-and-readiness) ·
[Segmentation timing](../../audio-event-segmentation/references/EVENT_SEGMENTATION_CONTRACT.md#selection-and-timing)

## Association and coverage

Associate observations and estimates of the same declared
event. An envelope attack and an onset peak can estimate
one event under the same definition. A coincident beat
forecast or section cut can describe related evidence.
Keep those labels visible as context. Include only routes
with compatible taps or an explicit alignment into this run.
Use a new run after a shared gap, seek, reset, or epoch change.

Sort the mapped estimates by position, source ID, and event
ID. Take the earliest unassigned estimate as the anchor at
$p_0$. Admit the first eligible estimate from each source in
$[p_0,p_0+G]$, where $G$ is the declared maximum span in
master samples. Keep same-source competitors for later
groups. A group can contain one estimate. Test another
pairing when close events compete. This rule can choose
an earlier pair with a larger residual. Increasing the
gate to hide clock error can join distinct events.

For positive declared weights $w_i$, report the label
$\hat p=\sum_i w_i p_i/\sum_i w_i$ and signed residuals
$p_i-\hat p$. Keep the weights, contributor records,
competitors, and union of mapped support. Merge overlapping
or touching intervals and preserve intervening holes. Use a
common event definition and scale when choosing the weights.

Treat event coverage as a source declaration. The reference
counts a source as covered for a group when its observed
spans cover the gate within the run. The gate includes its
upper edge inside the run. The run's own end is exclusive.
An explicit gap reports missing coverage. An undeclared
interval has unknown coverage. A measured quiet interval
can have observed coverage and no candidate. Keep source
coverage separate from the original support of a detection.

Use residuals to describe disagreement. A statistical
uncertainty needs a model of common errors. For two unbiased
unit-variance estimates with error correlation $\rho$, their
equally weighted mean has variance $(1+\rho)/2$. A value
of 0.9 gives 0.95. With independent errors the variance is
0.5. Detectors on one capture can share substantial error.

## Readiness and commitment

| Time or boundary | Evidence |
| --- | --- |
| Event label | Exact master sample position of the estimate. A prediction can label a future event. |
| Data readiness | Latest mapped exclusive readiness of the contributors used in the estimate. |
| Reported evidence delivery | Latest mapped release of those contributors when each reports a release. |
| Decision readiness | Latest required readiness of contributors, competing evidence, earlier committed assignments, and the source reports that close the gate. |
| Observed dispatch | A supplied timestamp on a named clock. It can include buffering, processing, and scheduling. |

Leave a numeric readiness or delivery field unknown when a
required dependency lacks a comparable sample-clock value.
An offline result can identify the association while its
live commitment and dispatch still need evidence.

For each declared source, a guaranteed frontier $W_i$
excludes subsequent eligible additions below $W_i$ in
the same run. It also excludes revisions and retractions
that would change that prefix. If the inclusive upper
gate edge is $g$, close the group when $g<W_i$ for
every source that has yet to finalize. Use all sources in
the reference's declared set. A source that already
contributed can still have a competing estimate at the
gate edge. A frontier equal to $g$ leaves the group open.

Supply progress reports with their own readiness bounds,
expressed on the master input clock. Their event-time
positions indicate eligibility, and their readiness
describes the evidence for the guarantee. A terminal
report closes that source to eligible changes for the run.
Keep incomplete coverage visible after every source has
advanced or finalized. A timeout or heuristic frontier
permits a provisional snapshot under a declared consumer
policy.
[Event time, processing time, and watermarks](https://research.google/pubs/the-dataflow-model-a-practical-approach-to-balancing-correctness-latency-and-cost-in-massive-scale-unbounded-out-of-order-data-processing/) ·
[Stream buffering](../../audio-stream-buffering/references/STREAM_BUFFER_CONTRACT.md)

In the replay, apply each batch of messages in arrival
order. Apply the batch's frontier reports after its
changes. Use increasing revisions for a stable source and
event key. Reject changes to eligible events below an
earlier guaranteed frontier. Check both the old and new
label when revising an event. Preserve each dispatch and
provisional snapshot. A valid continuation leaves a
committed prefix intact.

## Verification

Compare identical evidence with different arrival orders
and callback partitions. Check which delays affect only
delivery and which change data or decision readiness.
Replay a fractional estimate above a large origin, a
frontier at gate equality, an earlier event arriving late,
and an outage with no event from the affected source.

For labeled evaluation on an exact doubled-sample grid,
reuse the onset matcher on the declared evaluation span.
Compare matched times with signed errors and report
coverage and ambiguous groups. Preserve any finer
rational coordinates until the evaluation defines a
common grid. Measure dispatch on the target path when
the application needs a live latency claim.
[One-to-one event evaluation](../../audio-onset-detection/references/ONSET_DETECTION_CONTRACT.md#evaluate-the-detector) ·
[Fixture values](../../../tests/fixtures/AUDIO_TEMPORAL_FUSION_GOLDENS.md)

## Bounded reference

| Entry point | Contract |
| --- | --- |
| `ClockMap` | Supply the exact locked-rate map, anchors, and validity interval. Use known source and master epochs. |
| `FusionRun` and `SourceRoute` | Declare a half-open master span, event definition, source routes and coverage. A source can declare its mapping unavailable. |
| `Event` | Supply the native position and evidence, source and event ID, role, revision, and positive rational weight. |
| `fuse_offline` | Group a snapshot of current events. Return every group and retain context or excluded records with their reasons. |
| `replay_fusion` | Apply batches of events, retractions, and guaranteed frontiers. Return provisional groups and new commitments at each step, with supplied dispatch stamps. A null frontier position means terminal. |

Use one continuous master run, up to 16 sources, 512 event
or revision records, and 128 replay steps. Each source or
event can carry up to 64 intervals. The reference models
declared sample geometry, association, and causality.
Measure device drift, live scheduling, and confidence
with separate methods.
[Reference](../scripts/reference_temporal_fusion.py) ·
[Executable checks](../../../tests/test_audio_temporal_fusion_reference.py)
