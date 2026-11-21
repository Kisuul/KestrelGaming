# Audio scope triggering fixtures

Check crossing pairs, fractions, dispositions, release indices, completion
order, and PCM bounds exactly. Unless specified, use rising direction,
level 0, hysteresis 1/2, origin zero, normal mode, and zero pretrigger,
posttrigger, and holdoff counts.

## Edges and capture timing

| Prepared input | Expected result |
| --- | --- |
| Origin 100, $P=2,Q=1$. Trigger plane `[-1,-1/4,3/4,1/2]`, display plane `[9,8,7,6]`. Split before 3/4 and before 1/2. | Accept at 102 with left index 101 and fraction 1/4. Complete `[100,104)` after sample 103, with both planes intact. |
| `[-1,1,-1,-1,1,-1]` or `[-1,1,-1,-1,-1,1]`, $H=4$. | Accept at 1 and release at 5. Suppress the edge at 4 in the first tape. Accept at 5 in the second. |
| `[-1,1,-1,1,-1/4,1,-1,1]`, $H=4$. | Accept 1, suppress 3 for holdoff, report 5 unarmed, accept 7. The edge at 3 uses the arm. |
| `[-1,1,-1,1,-1,1,-1,-1]`, $Q=2$. | Accept 1. At sample 3, report busy and then complete `[1,4)`. Accept 5 and complete `[5,8)`. With $Q=1$ and the first four samples, accept 3 and leave `[3,5)` pending. |
| The same alternating tape with $Q=2,H=4$. | The edge at 3 reports holdoff while the old span is pending. Complete `[1,4)` on that sample. A fresh edge at 5 is eligible. |
| `[-1,1,-1,1]`, $P=2,H=10$. | At 1 report missing prehistory. Release is unset. At 3 accept and complete `[1,4)`. |
| `[-1,0,0,-1/4,0,-1,0]` and its sign reverse with a falling trigger. | Accept at 1 and 6. Report the edge at 4 as unarmed. Arrival at the level has fraction 1. |
| `[0,1,0,-1,0,0]` with $h=0$. | The source side first arms at 3. One edge arrives at 4. |

## Numerical boundaries and state

| Prepared condition | Expected result |
| --- | --- |
| $T=1$, $h=5\cdot2^{-55}$, and `[1−2⁻⁵³,1,1−2⁻⁵²,1]`. | Crossing 1 is unarmed. Crossing 3 is accepted. Rounding $T-h$ to binary64 falsely qualifies the first crossing. |
| From $-M$ to $M$ at zero, for the largest finite binary64 $M$. From zero to $M$ at the smallest positive binary64 threshold with $h=0$. | Fractions are $1/2$ and a strictly positive fraction below the smallest positive binary64 value, respectively. |
| Left index $2^{53}+1$, samples $-1/4$ and $3/4$, with $h=0$. | Use the exact left index and fraction $1/4$. Rounding their sum to binary64 gives $2^{53}+2$. |
| Origin $B-2$, $B=2^{256}-1$, tape `[-1,1]`, $Q=1$. | The input block ends at $B$. The requested end is $B+1$. Report span out of range and leave release unset. |
| Single-shot with `[-1,1]` while disabled. Arm at 2, ingest `[-1,1,-1,1]`, arm at 6, ingest `[-1,1]`. | Accept 3 and 7. Report single disarmed at 1 and 5. Preserve holdoff on a later arm. |
| Insert an invalid final channel sample into a block during posthistory. Retry the correct block. Repeat with a gap and with an overlap. | Rejection leaves the previous state intact. The valid retry reproduces the clean sequence. |
| Reset during posthistory, then send an old block at the same numeric start. | One abort identifies the old edge. The stale block is rejected. Wait for an arming sample and a local crossing in the fresh epoch. |

Use a whole-tape oracle that checks the interval since the previous raw
crossing for arming evidence. Compare chronological event sequences and
direct tape slices with the streaming result. Partition short tapes at
each subset of callback boundaries, including the crossing and the
final posttrigger sample.

## Review tasks

1. Give an agent a scope that appears to miss a crossing when the
   callback splits. Ask for the expected sample pair, state at that
   instant, and the first complete capture interval.
2. Give it separate trigger and display channels with a visible pulse
   that differs from the trigger edge. Ask what data would locate the
   actual source of the capture.
3. Give it a crossing on the last sample of a pending span. Ask for the
   order of the acquisition decision and the completion report.

Record observed agent decisions separately from reference test results.
