# Audio dropout detection goldens

[Executable checks](../test_audio_dropout_detection_reference.py) ·
[Contract](../../skills/audio-dropout-detection/references/DROPOUT_DETECTION_CONTRACT.md)

## Source frame evidence

Use two channels at 48 kHz with origin 1000. Repeat the gap and
quiet-window fixtures at origin $2^{60}+1000$ by adding $2^{60}$
to each position. Frame counts and nominal durations agree.

| Offer after accepting $[1000,1004)$ | Expected evidence |
| --- | --- |
| $[1008,1012)$ | Provisional gap $[1004,1008)$, signed delta $+4$, and frontier 1004. Confirm only when the caller declares the gap, then resume at 1008 on a fresh epoch. The four frames have nominal duration $1/12000$ s. |
| $[1001,1002)$ | Signed delta $-3$ and one frame of overlap on $[1001,1002)$. |
| $[1002,1006)$ | Two frames of overlap on $[1002,1004)$ and a rejected suffix $[1004,1006)$. A contiguous append at 1004 still succeeds. |
| $[998,1001)$ | Signed delta $-6$ and one frame of overlap on $[1000,1001)$. |
| $[1008,1012)$ offered early, then $[1004,1008)$, then another offer at 1008 | The ordered retry covers all twelve source frames and confirms no gap. |
| Reset to sample 10 at 44.1 kHz | Nominal time starts at zero on the new clock. The old and new indices give no cross-epoch duration. |

## Playout provenance

| Probe | Expected evidence |
| --- | --- |
| Acquire four zero frames between two four-frame active blocks. In a second trace, fill missing positions $[1004,1008)$ with zeros. | The delivered stereo PCM is identical. The acquired trace has twelve original frames. The second has eight original frames and four zero-fill frames. A late push beginning at 1004 leaves the presented spans unchanged. |
| In a four-frame ring, push four frames and then two more under `drop_oldest`. Pull six frames with silence fill. | Both the producer discard and the consumer overrun fill refer to $[1000,1002)$. The consumer presents two replacement frames ahead of four original frames. |
| Use three periods of $(1/4,-1/2,1/2,-1/4)$. In the second trace, repeat the first period on missing positions $[1004,1008)$. | The delivered PCM agrees and stays nonzero. The second trace has four replacements identified by the source and playout records. The waveform quiet detector emits no candidate. |

## Quiet-window timing

Set $W=4$, minimum duration four frames, quiet ceiling $Q=1/16$,
active floor $A=1/4$, and ratio limit $R=1/16$. These values
define the fixture. The left channel has four samples at $1/2$,
four at zero and four at $1/2$. The right channel stays at
$1/2$. Repartition the same samples across callbacks.

| Probe | Expected evidence |
| --- | --- |
| Accept both channels through exclusive frontier 1012. | The left candidate is $[1004,1008)$, with ratio zero and support $[1000,1012)$. It is ready at 1012. The right channel has no candidate. |
| Stop at exclusive frontier 1011. | Retain $[1004,1008)$ as incomplete. Its final active-context window is incomplete. |
| Mark any frame of the left run or an adjacent context window ineligible. | The affected full window is unusable. No candidate qualifies on that run. |
| Use quiet RMS $1/64$ between active windows at $1/4$. | The ratio equals $1/16$ and qualifies. With quiet RMS $1/32$, the ratio is $1/8$ and fails while both absolute gates pass. |
| Increase the minimum duration to five frames. | The four-frame quiet run fails the duration gate. |
| Use two quiet windows at $1/32$ and $1/128$ in either order with active neighbors $1/2$ and $1/4$. | Use the larger quiet level and the smaller active level. The quiet interval is $[1004,1012)$ and its ratio is $1/8$. The candidate qualifies at 1016 when $R=1/8$. |

The identical-sample fixtures exercise source and playout logs
as well as PCM. The window test enumerates all 2,048 callback
partitions of each twelve-frame record at both origins.
