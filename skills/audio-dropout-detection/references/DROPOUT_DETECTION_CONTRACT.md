# Audio dropout detection contract

[Source coverage](#source-coverage) ·
[Playout provenance](#playout-provenance) ·
[Quiet-window evidence](#quiet-window-evidence) ·
[Reference limits](#reference-limits)

## Source coverage

Identify the tap, clock domain, channel IDs, units, epoch, origin
$o$, and rational sample rate $F_s$. Use half-open sample intervals
$[s,e)$. An interval has $e-s$ frame positions across the declared
channel set and nominal duration $(e-s)/F_s$. Use source positions
or exact loss metadata for source coverage. A cursor built by
counting delivered frames describes the delivery timeline.
[Timebase contract](../../audio-timebase-sync/references/TIMEBASE_CONTRACT.md)

Let $h$ be the next expected source frame. An offered block has
start $s$ and length $N$. Within this continuous epoch, the
accepted source span is $[o,h)$.

| Offer | Evidence and action |
| --- | --- |
| $s=h$ | Accept $[s,s+N)$ and advance $h$ to $s+N$. |
| $s>h$ | Keep provisional gap $[h,s)$. Reject the offer atomically. Confirm missing support once the source positions and delivery policy establish it. |
| $s<h$ | Record signed start delta $s-h$. Intersect $[s,s+N)$ with $[o,h)$ to measure actual overlap. Reject the whole offer. Resolve ordering or submit the unseen contiguous suffix explicitly. |

A short early block can have fewer overlapping frames than its
early offset. An offer before the epoch can share no accepted
frames. If the missing block arrives before the delivery cutoff,
retry in source order. Keep the original playout record after
the cutoff even if offline recovery later obtains those samples.

For a confirmed gap on the same source clock, report its exact
interval and begin a fresh continuous epoch at the next covered
position. For a seek, restart, or rate change, preserve the
discontinuity and begin a new timing record. Derive missing
prefix or suffix coverage only from an expected source boundary
that the caller can verify.

The reference `SourceCoverage.ingest` accepts metadata on a
`ScopeEpoch`. It returns the accepted, early, or provisional
gap report and advances the cursor only on acceptance.
`reset_epoch(new, confirm_gap=True)` records the confirmed
gap between the old frontier and new origin. The caller supplies
the confirmation. This call requires the same clock, rate, tap,
units and channel order. A plain reset begins the new epoch
without a gap estimate. Use a fresh ID for either transition.
[Timebase discontinuities](../../audio-timebase-sync/references/TIMEBASE_CONTRACT.md#discontinuities-and-epochs)

## Playout provenance

Record what was available by the presentation deadline and what
was delivered. An overrun can discard samples already supplied to
a producer-side tap. An underrun can fill positions where input
missed the deadline. Map each record to the frame positions of
the affected tap. Related reports of the same loss span contribute
one interval to its missing-frame total.
[Buffer contract](../../audio-stream-buffering/references/STREAM_BUFFER_CONTRACT.md)

Use `summarize_playout` with one ordered, complete partition of the
requested output interval. Each segment declares `original`,
`zero_fill`, `repeat`, `other_concealment`, `unrendered`, or
`unknown`. Use `unknown` for rendered data with unknown
provenance. Original, replacement, unrendered, and unknown
lengths sum to the request length. The original and replacement
lengths describe playout. Source gaps require their own timing
evidence and a verified mapping to the playout spans.

Acquire telemetry at the point that provides it.

- PortAudio `paInputOverflow` reports a discard. Its position
  semantics depend on the stream's callback buffer setting.
  Use source or driver evidence for exact length.
  [PortAudio callback status](https://files.portaudio.com/docs/v19-doxydocs/portaudio_8h.html)
- WebRTC `concealedSamples` counts local substitution for
  unavailable media, including late packets. The
  `silentConcealedSamples` subset can include comfort noise.
  Use changes in the same stream's counters to describe a
  polling interval. Event placement needs a timed record.
  [WebRTC receiver statistics](https://www.w3.org/TR/webrtc-stats/#dom-rtcinboundrtpstreamstats-concealedsamples)
- In RTP, resolve sequence wrap, duplicate delivery, and reorder
  deadlines before classifying packet loss. Use media time and
  payload duration to infer source frame positions. Opus
  discontinuous transmission can omit quiet data by design.
  Its loss concealment can produce nonzero output.
  [RTP timing](https://www.rfc-editor.org/rfc/rfc3550.html#section-5.1) ·
  [Opus discontinuous transmission](https://www.rfc-editor.org/rfc/rfc7587.html#section-3.1.3) ·
  [Opus concealment](https://www.rfc-editor.org/rfc/rfc6716.html#section-4.4)

## Quiet-window evidence

Use full-rate samples at the named tap. Declare the level units,
conditioning, and window grid. The reference uses unweighted
RMS on nonoverlapping $W$-frame windows anchored at the epoch
origin. For each channel set a quiet ceiling $Q$, active floor
$A$, minimum quiet duration in frames, and ratio limit $R$.
Require $0\leq Q<A$ and $0\leq R\leq1$.

1. Label a full window quiet at RMS $\leq Q$ and active at RMS
   $\geq A$. End quiet runs at the first complete nonquiet
   window. Require both immediately adjacent windows to be
   usable and active.
2. For a maximal quiet run $[s,e)$, require the minimum
   duration and $q/\min(a,b)\leq R$. Here $q$ is the largest
   quiet-window RMS, and $a,b$ are the adjacent active levels.
   The reference compares a rational ratio of the reported
   binary64 RMS values.
3. Report the interval on the window grid, with support
   $[s-W,e+W)$ and earliest ready frontier $e+W$. The final
   required sample is at $e+W-1$. Runtime delivery also depends
   on callback arrival and processing.
4. Carry a partial window and the open quiet run through
   contiguous blocks. A gap or epoch change breaks the context.
   Mark known synthetic or unusable frames in the eligibility
   mask. An ineligible frame makes its whole window unusable.
   Keep the quiet span and available left context when right
   context is unavailable. Leave readiness absent.

Speech pauses, fades, edits, gates, and intentional mutes can
satisfy the same rule. For source attribution, compare aligned
taps and inspect status and replacement metadata. Repeated
nonzero audio can also be a genuine periodic waveform.
[RMS](../../audio-rms-crest-factor/SKILL.md) ·
[Sample-aligned capture](../../audio-oscilloscope/SKILL.md)

## Reference limits

Use the [reference script](../scripts/reference_dropout_detection.py)
with the shared timebase, oscilloscope, and RMS script directories
on the Python import path. It accepts one to eight channels and
one to 256 frames per block. The maximum exclusive index is
$2^{256}-1$. The quiet profile uses one to 256 frames per window,
finite floats or signed 32-bit integer samples, and at most one
pending quiet run per channel. A nonzero window is unusable if its
RMS rounds to zero. The shared timebase retains used epoch IDs.

Call `QuietDetector.ingest` with planar samples and an optional
Boolean per frame. Use the mask to reflect which samples support
the intended observation. Use `finish()` or `reset_epoch` to collect
incomplete quiet runs once. A reset anchors the grid at the new
origin and retains the profile's frame counts. Keep callback
scheduling, transport reordering, and clock mapping in the host.
[Fixture values](../../../tests/fixtures/AUDIO_DROPOUT_DETECTION_GOLDENS.md)
