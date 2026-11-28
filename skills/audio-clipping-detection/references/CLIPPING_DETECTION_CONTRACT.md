# Clipping detection contract

## Inputs and profiles

Select one tap and one sample clock per epoch. Record the tap ID,
clock domain, rational sample rate, epoch and origin, units, and
ordered channel IDs. Use full-rate samples. Peak holds, display
values, or downsampled points can lose the evidence for a run.
[Sample timebase](../../audio-timebase-sync/SKILL.md) ·
[Sample peak](../../audio-sample-peak/SKILL.md)

| Profile | Boundary | Evidence |
| --- | --- | --- |
| Signed PCM with $B$ valid bits | $q_-= -2^{B-1}$, $q_+=2^{B-1}-1$ | Count exact contacts at each rail. Keep maximal contiguous same-rail runs, including single contacts. Apply the declared minimum plateau length to each run. |
| Floating-point PCM | Finite signed references $r_-<0<r_+$, default $(-1,+1)$ | Count exact equality at each reference. Count strict exceedance separately with $x<r_-$ or $x>r_+$. Keep maximal contiguous excess runs of the same polarity. |

With normalization by $2^{B-1}$, the signed negative rail is $-1$.
The positive rail is $1-2^{1-B}$. Determine $B$ from the decoded
format. For left-aligned valid bits, inspect the unpacked code
after validation of the padding. The PCM decoder centers unsigned
8-bit codes at 128. In the reference, the decoder's integer PCM
outputs are exact dyadic values. Multiply them directly by
$2^{B-1}$ to recover the centered code without error. Keep the
signed valid bits and byte-level format with the observation.
[PCM format contract](../../audio-sample-formats/references/PCM_FORMAT_CONTRACT.md) ·
[WAVE valid-bit alignment](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ksmedia/ns-ksmedia-waveformatextensible)

Float equality has its own counters. An equality ends any active
excess run at that index. Values above a nominal reference can be
valid float headroom. A separate near-rail policy needs a tolerance
in declared units and a model for the expected ceiling.

## Run evidence

Use exact indices and half-open spans $[s,e)$. Report the epoch,
channel, evidence kind, polarity, boundary, start, exclusive end,
length $e-s$, and extreme. Use the minimum value for a negative
run and the maximum for a positive run. Each integer run has a
constant code. A float excess run can contain different values.

Keep one open run per channel. At each accepted sample, extend
a matching run. A change of polarity closes the previous run and
can start a new run at the same index. An in-range sample, or a
reference equality in float PCM, closes an excess run.

| Condition | Report |
| --- | --- |
| A signed run starts at $s$ and has at least $L$ observed samples | Set `plateau_ready_sample_exclusive` to $s+L$. Keep this first qualifying frontier if the run grows. The default rule uses $L=2$. |
| A contiguous sample at $n$ first breaks a run | Set the end to $n$, `close_reason` to `observed_break`, and `end_confirmed_sample_exclusive` to $n+1$. |
| A run is still open after a callback | Report its observed prefix with the current exclusive end. The close reason and end confirmation are absent. |
| A gap, epoch change, or end of input closes the observation | Report its observed exclusive end and the boundary cause. End confirmation stays absent because the observation has no breaking sample. |

The first qualifying frontier measures data availability. Delivery
also depends on block arrival and processing time. Preserve exact
indices through the accumulator and convert to nominal epoch time
with $(n-o)/F_s$, where $o$ is the epoch origin. A run touching
$o$ can have unobserved samples before its recorded start.

## Continuity and boundaries

Validate the epoch, shape, channels, finite values, and code range
for the whole block before accepting any samples. Require the
start to equal the next expected index. Reject a gap or overlap
with no change to the clock, counts, or open runs. Accept the
missing contiguous block if it becomes available.

For a declared gap, seek, tap or channel change, or changed
measurement profile, finalize the old support and start an
unused epoch. For a gap, preserve the missing interval in the
coverage record. Two contacts across a gap are two observations.
The new epoch starts with zero counts and no open runs.
[Discontinuities and epochs](../../audio-timebase-sync/references/TIMEBASE_CONTRACT.md#discontinuities-and-epochs)

The [offline reference](../scripts/reference_clipping_detection.py)
takes a `ScopeEpoch` and a `SignedPcmProfile` or
`FloatReferenceProfile`. Call `ingest` with one equal-length
list or tuple per channel. The bounds are 1 to 8 channels and
1 to 256 frames per block. Signed codes use 2 to 32 valid bits.
Float mode takes finite Python floats or signed 32-bit integers.
The maximum exclusive index is $2^{256}-1$.

For encoded integer PCM, call `ingest_pcm` with the accepted
decoder's `PCMFormat`. The valid bits and channel count must
match the profile and epoch. If labels are present, match the
declared order. The update carries the format of that block.
Preserve earlier block formats when a run spans blocks.

Each update carries the observed frontier, cumulative epoch
counts, open snapshots, and newly completed runs. Completed runs
use ascending exclusive end order with channel order for ties.
Call `finish()` to emit the remaining runs once. Call
`reset_epoch` to receive the finalized report for the old epoch
and begin the new one. Archive outputs at the caller. The
reference keeps one open run and counters per channel, temporary
storage bounded by the current block, and the timebase's set of
used epoch IDs.

## Diagnose the stage

- **Hard clipping.** A plateau at a verified ceiling supports a
  clipping hypothesis. Compare the waveform and its slope near the
  boundary. An authored rectangle or repeated quantized extrema
  can produce the same contacts. Use aligned taps or a verified
  conversion policy with saturation counts to locate a clamp.
- **Soft saturation.** Measure the drive response and compare
  matched clean and suspect captures. Look for gain compression
  and harmonics or residuals. A nonlinear path can stay below
  both sample references. Keep distortion evidence tied to the
  test stimulus and tap.
  [THD and THD+N](../../audio-thd-thdn/SKILL.md)
- **Intersample exceedance.** Measure the reconstructed peak with
  the stated bandwidth, boundary model, support, and error. A
  reconstructed peak can exceed the reference while all captured
  samples remain inside it. Use the standard's procedure and
  calibration evidence for a conformance claim. Measure the
  downstream tap or verify its clamp to attribute clipping there.
  [True-peak contract](../../audio-true-peak/references/TRUE_PEAK_CONTRACT.md) ·
  [ITU-R BS.1770-5, Annex 2](https://www.itu.int/rec/R-REC-BS.1770-5-202311-I/en)

Use the [fixture values](../../../tests/fixtures/AUDIO_CLIPPING_DETECTION_GOLDENS.md)
to check what each type of evidence supports.
