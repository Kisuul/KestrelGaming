# Audio event segmentation fixtures

[Reference](../../skills/audio-event-segmentation/scripts/reference_event_segmentation.py) ·
[Contract](../../skills/audio-event-segmentation/references/EVENT_SEGMENTATION_CONTRACT.md) ·
[Executable checks](../test_audio_event_segmentation_reference.py)

Use zero-based feature indices. At cut $b$, frame $b$ is
the first frame on the right. Unless specified, compare two
frames on each side, use peak radius one, and set the
minimum squared score to one. Compare exact rational
features and sample coordinates exactly.

## Feature and score checks

| Probe | Expected evidence |
| --- | --- |
| Abrupt step `[0,0,0,0,2,2,2,2]`. | Scores at cuts 2 through 6 are $[0,1,4,1,0]$. Cut 4 qualifies at threshold 4. Its signed change is 2. Reverse the step for change $-2$ with the same score. |
| Gradual step `[0,0,0,1,2,3,3,3]`. | At the same indices the scores are $[1/4,9/4,4,9/4,1/4]$. Cut 4 also qualifies at threshold 4. |
| Four repeats of $(1,0)$ followed by four of $(0,1)$. | The signed change at cut 4 is $(-1,1)$ and the score is 2. |
| `[1,-1,2,-2]` as signed values, then as squared values. | The complete comparison at cut 2 gives scores 0 and 9. Its peak neighborhood is incomplete in both cases. |
| `[0,0,NA,1,1,1,1]` and the same grid with slot 2 omitted. | At cuts 2 through 5 the scores are `[NA,NA,NA,0]`. Preserve slot 2 as unknown, with no selected cut. In a separate run with a fabricated zero at slot 2, scores are $[1/4,1,1/4,0]$ and cut 3 is a false detection. |
| Two values at $2^{40}$ and two at $2^{40}+1/4$. | The exact score at cut 2 is $1/16$. An uncentered binary64 Gram calculation can return zero. Subtract the common level before forming the Gram matrix and compare both results with the exact score. |

For a transform replay, use eight rectangular frames at
3,520 Hz with $M=H=64$. In each frame, generate
$x[n]=A\cos(2\pi kn/64)$ for $n=0,\ldots,63$. The first
four use $k=8$ and $A=0.5$. Compute the merged PSD and
normalize admitted chroma to unit sum. Measure RMS from
the same frames. Check both squared scores at cut 4.

| Last four frames | Chroma score | RMS score |
| --- | ---: | ---: |
| $k=12$, $A=0.5$ | About 1.961664388369 | Less than $10^{-26}$ |
| $k=16$, $A=0.5$ | Less than $10^{-26}$ | Less than $10^{-26}$ |
| $k=8$, $A=0.25$ | Less than $10^{-26}$ | About $1/32$ |

## Peak decisions

| Probe | Expected evidence |
| --- | --- |
| Eight zeros, three twos, nine zeros. | Width one selects cuts 8 and 11. Width four selects 7 and 11. With width four, scores at 7, 8, 11 and 12 equal $9/4$. Threshold $9/4$ admits the earlier point on each plateau. Threshold 3 admits neither. |
| Six zeros, two twos, six zeros at width one. | Radius one selects cuts 6 and 8. Radius two selects cut 6 only. |
| First six and first seven slots of the abrupt step. | Both give cut 4 a score of 4. With six slots, its right flank is unavailable. The seventh slot confirms cut 4. |
| Shared prefix `[0,0,0,0,2,2,2]` and five more frames of either 2 or 32. | The confirmed cut 4 and all of its evidence agree. The second continuation also selects cut 7. |
| Set the analysis start to the cut 4 position in the abrupt step. | Its raw score remains 4. The position is an imposed coverage endpoint and the boundary list is empty. |

To isolate the peak rule, use scores `[0,0,2,0,3,0,0,0,0]`
with radius two. In a second run set the score at index 6
to 4. Both runs reject index 2 under the local rule.
Strongest-first suppression admits index 2 in the second
run because the new peak removes the competitor at index 4.

## Sample clock and coverage

Use origin $O=2^{60}+37$, 48 kHz, window length 960, and hop 240.
Place the abrupt step at cut 4. The neighboring centers are
$O+1199.5$ and $O+1439.5$. The doubled cut position is
$2O+2639$. Preserve that integer when comparing cuts.

| Quantity | Expected evidence |
| --- | --- |
| Raw input supports at cut 4 | Left $[O+480,O+1680)$, right $[O+960,O+2160)$. |
| Raw peak support and ordinary readiness | $[O+240,O+2400)$. The score is ready at $O+2160$ and the peak is ready at $O+2400$. |
| Feature 1 ready at $O+2800$ | The peak needs $O+2800$ and the score is still ready at $O+2160$. On simulated blocks of 1,024 samples, the evidence arrives at $O+3072$. With feature 1's delivery report omitted, peak delivery is unknown. |
| Eight slots with the abrupt step, across the raw input span | Available feature cells occupy $[O+359.5,O+2279.5)$ with a cut at $O+1319.5$. Peak eligibility is $[O+959.5,O+1679.5)$. Outside the available cells, coverage is unknown. |
| Seven slots with slot 2 missing | $[O+839.5,O+1079.5)$ is unknown in the middle. The raw input windows of neighboring frames can overlap that interval. |
| Eight measured zeros, one missing slot, eight measured zeros | Peak eligibility in doubled offsets from $2O$ is $[1919,3359)$ and $[6239,7679)$. The threshold excludes all cuts. |

## Evaluation

In an eligible span, use sample offsets $[100,104]$ for
reference cuts and $[96,101]$ for estimates. Double these
sample positions and pass tolerance 8 to the onset matcher.
Expect two matches with signed errors of $-4$ and $-3$
samples. Pairing the nearest remaining points first gives
one match.

For a label check, use three consecutive spans of length
ten with reference labels A, B, A and estimated labels
B, A, B. The interior cuts agree exactly. Semantic
agreement is zero for shared names, and the partitions
agree after relabeling. Use the evaluation that matches
the meaning of the labels.
