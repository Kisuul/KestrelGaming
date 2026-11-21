# Audio oscilloscope fixtures

Check sample intervals, channel values, extrema, and indices exactly. Use
half-open intervals on one epoch clock.

## Display geometry

| Prepared window | Expected projection |
| --- | --- |
| 256 samples at start zero. Set index 119 to `1` and index 123 to `-0.75`. Set every other sample to zero. Use width 16. | Bucket 7 owns `[112,128)`. It retains minimum `-0.75` at 123 and maximum `1` at 119. A stride-16 sample pick returns 16 zeros. |
| `[10,0,0,-6,0,0,0,4,0,0,12]` at start 100 and width 3. | Supports `[100,103)`, `[103,107)`, `[107,111)`. Min/max pairs with indices are `(0@101,10@100)`, `(-6@103,0@104)`, and `(0@108,12@110)`. |
| `[-1,2,-1,2]` at start 100 and width 1. | The extrema use indices 100 and 101. With width 4, each bucket has one sample. With a wider display, return four measured points. |
| `[-1,0.25,0.75,1]` and `[-1,0.75,0.25,1]` with the same epoch and bounds at width 1. | Identical buckets with the same winning indices. The underlying traces still differ. |
| Left `[0.75,0,1.25,-1.5]` and the negated right plane at start 100 and width 1. | Left extrema `(-1.5@103,1.25@102)` and right extrema `(-1.25@102,1.5@103)`. Both planes cover `[100,104)`. A separate equal-weight mono mix yields zeros. |

An independent position-based oracle assigns relative sample $i$ to
$\lfloor((i+1)W-1)/L\rfloor$ for $1\le W\le L$. This is the largest $j$
with $jL < W(i+1)$, so the bucket's left edge is at or before $i$. Using
$\lfloor iW/L\rfloor$ assigns sample 3 of the 11-to-3 case to the wrong
bucket. Compare absolute bounds and first extrema from the position-based
assignment against the bucket implementation.

## Capture timing and state

| Input | Expected capture behavior |
| --- | --- |
| Left `[0,1,2,3,4,5,6,7,8]` with the negated right plane in one block at 100. Set window 4, hop 2, and history 4. | Complete captures `[100,104)`, `[102,106)`, and `[104,108)`. Their left planes are `[0,1,2,3]`, `[2,3,4,5]`, and `[4,5,6,7]`. Right values are the corresponding negatives. The cursor becomes 109 and the next scheduled end is 110. |
| Split the same tape at arbitrary callback boundaries. Change which frames are painted and the width used for each. | The capture sequence and raw values match the one-block result. Painting the latest frame twice at different widths gives the same capture bounds. |
| A 14-sample tape starting at 100 with window 3, hop 7, and history 3. | Complete supports `[100,103)` and `[107,110)`. The next scheduled end is 117. |
| Start a four-frame window above $2^{53}$ at $o=2^{53}+1$, with a rational rate. | Start and end are $o$ and $o+4$. The doubled center is $18014398509481989$. Nominal duration and first-to-last timestamp span are $4/f_s$ and $3/f_s$. |
| Leave three valid samples pending. Send a block with a late NaN in the last channel, then retry with a valid block at the expected cursor. | The entire invalid block is rejected. The retry produces the same frames as a clean replay, with the original pending values. Gap, overlap, and mismatched metadata have the same atomicity requirement. |
| Reset after a partial window. Change the origin, clock metadata, or channel layout. | The new window warms up from the new origin. An old block is rejected even when its start matches the new cursor. An old published snapshot keeps its original data. |

Use a direct slice of the full input tape as the independent capture
oracle. Enumerate all cuts between the 12 sample frames in a short tape.
Run overlapping, one-frame, and spaced window schedules as separate cases.

## Review tasks

1. Give the agent a waveform that loses a short pulse at some widths.
   Ask it to localize the fault and specify the raw sample and bucket checks
   that distinguish capture loss from display loss.
2. Give the agent a flat trace from stereo input with equal and opposite
   channel values. Ask which tap, channel planes, and exact bounds it
   needs to establish what the zero trace measures.
3. Give the agent a callback larger than the retained history. Ask which
   windows finish, which samples survive a naive batch write, and how to
   verify the proposed fix with callback splits.

Record the agent's actual decisions and evidence separately from the
reference test results.
