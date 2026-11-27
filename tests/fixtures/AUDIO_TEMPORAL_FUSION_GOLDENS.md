# Audio temporal fusion fixtures

[Reference](../../skills/audio-temporal-fusion/scripts/reference_temporal_fusion.py) ·
[Contract](../../skills/audio-temporal-fusion/references/TEMPORAL_FUSION_CONTRACT.md) ·
[Executable checks](../test_audio_temporal_fusion_reference.py)

Use exact sample coordinates, a 48 kHz master, and
positive weights. Use one declared run and compatible
event types unless the case changes them.

## Clock and support

| Probe | Expected evidence |
| --- | --- |
| Map locked 44.1 kHz offsets 1,470 and 1,470.5 to 48 kHz at $O=2^{60}+37$. | The positions are $O+1600$ and $O+235280/147$. Their distance is $80/147$. A half-sample gate excludes the pair. A gate of $80/147$ admits it. Both positions round to the same binary64 coordinate. |
| Map 24 kHz source span $[0,10)$ to 48 kHz with aligned zero anchors. Supply position $19/2$, support $[8,10)$, ready at 10 and release at 11. | Label 19, mapped support $[16,20)$, readiness 20 and unknown mapped release. An event at native position 10 is outside the validity interval. |
| Capture position 100 and delayed tap position 112 with a one-sample gate. | The measured 12-sample offset aligns both labels at 100 and gives one group. Nominal zero offset gives two groups. |
| Supports $[0,4)$, $[8,10)$ and $[6,8)$. | Preserve the original intervals and report union $[0,4),[6,10)$. The hole remains. |
| Selected Skill #42 boundary with $O=2^{60}+37$, $M=960$, $H=240$ and a delayed left feature. | Relative to $O$, use label $2639/2$, peak support $[240,2400)$, peak readiness 2,800 and reported release 3,072. Record score readiness 2,160 for diagnosis. |

## Association

| Probe | Expected evidence |
| --- | --- |
| Distinct sources at 0, 9 and 18, arriving as 18, 0, 9. Gate 10. | Groups `[0,9]` and `[18]`. A proximity chain would include all three. |
| Source A at 0, 2 and 7. Source B at 6. Gate 6. | A0 joins B6 at equality. A2 competes for this group and remains for the next. The selected groups are `[0,6]`, `[2]` and `[7]`. |
| Source A sends IDs `second` and `first` at time 5. Source B also sends an event at 5. Gate zero. | The first group uses A's `first` and B's event. A's `second` anchors the next group. Reversing arrival order preserves both groups. |
| Compatible estimates at 4,800 and 4,848, weights 2 and 1, and ready boundaries 5,280 and 5,520. | Label 4,816, residuals −16 and +32, and data readiness 5,520. Lag from label to data readiness is $44/3$ ms. |
| Predict a beat at 7,200 with input ready at 6,000. Supply a measured onset at 7,200. | The forecast evidence is ready 25 ms before its label. Retain the forecast as context in the onset run. |
| Source B reports no event in a gate around sample 5. Mark the sampled interval observed quiet, then replay with B's gap $[4,9)$. | The observed replay has coverage from B. The gap replay reports B incomplete. A candidate from B inside the declared gap is excluded. |
| Two equal-weight estimates have unit error variance and positive correlation 0.9. | The mean has variance $19/20$, compared with $1/2$ when the errors are independent. |

## Replay and commitment

| Probe | Expected evidence |
| --- | --- |
| With inclusive gate end 4,848, set source frontiers to 4,900 and 4,848. Then advance the second to 4,850. | The group stays provisional at equality. A record at 4,848 can still arrive and compete. It closes once both frontiers clear the gate. |
| The weighted example has closure evidence ready at 5,760. Deliver it at the next boundary of blocks of 240 or 1,024 samples from zero. | Both runs retain label 4,816 and data readiness 5,520. Decision readiness is 5,760, or $59/3$ ms after the label. The block delivery boundaries are 5,760 and 6,144. |
| Gate 6 with A9 and B14. Replay with earlier C4 arriving in the next batch while the result is provisional. | Keep the first snapshot `[9,14]`. The next snapshot gives `[4,9]` and `[14]`. |
| Gate 2 with A0, A1, B2 and B8. Data readiness of A1 is 120 and both terminal reports are ready at 110. | Groups `[0,2]`, `[1]` and `[8]` have data readiness 3, 120 and 9. A1 is a competitor in the first group. All three decisions need sample boundary 120 because of the competing evidence and earlier assignments. |
| Source B cannot map into the master. Replay a group from A and finalize B. | Keep B's unmapped record. Finalization can commit A's group with B still incomplete. |
| Commit a prefix ending at 6 with three frontiers at 9. Continue with events at 9 and 13, or at 9 and 28. | The committed prefix agrees. Only later association changes. Revising, moving, or retracting an eligible event below a guaranteed frontier fails the replay. |

Compare the synthetic delay values on the sample clock.
Measure actual queueing and dispatch with a clock relation
when evaluating live components.
