# Beat tracking fixtures

Use exact frame positions and declare the pulse level for every
target. The novelty fixtures below use 100 frames per second unless
specified. Frames outside the listed pulses have valid zero scores.
[Contract](../../skills/audio-beat-tracking/references/BEAT_TRACKING_CONTRACT.md) ·
[Regression checks](../test_audio_beat_tracking_reference.py) ·
[Research construction](../../memory/projects/kisuul/kestrelgaming/handoffs/2026-11-21-audio-beat-tracking-research-r01.md#executed-checks-and-portable-fixtures)

## Period and phase

| Fixture | Expected result |
| --- | --- |
| Length 800 with unit pulses at $7+50j$ or $31+50j$. | Raw linear autocorrelation agrees at lags 1–129. Both select lag 50 and 120 BPM. Equal-support phase sums select offsets 7 and 31 respectively. |
| Length 800 with unit pulses at $7+25j$. | At lags $25,50,75,100$, raw sums are $31,30,29,28$. Mean products are all $0.04$. In the 60–240 BPM band, the mean-product estimate retains all four as tied. A prior of width 0.5 octaves centered at 240, 120, or 60 BPM chooses its center. |
| Length 1,600 with alternating strengths 1 and 0.25 at $20+50j$. | Mean products at lags 50 and 100 are 0.005 and 0.010625. The slower period wins in the default band. |
| Novelty 2 throughout a complete window. | Every positive-lag mean product is 4. A mean-removed comparison gives zero. Report unavailable tempo. |
| Length 64 with impulses at frames 0 and 63. | Linear lag 1 is zero. Circular lag 1 is one. Lag 63 has mean product one on just one pair and fails a two-pair minimum. |
| Two tracks share the first 200 of 300 frames with pulses at $10+25j$. The first then has pulses at 210 and 260. The second has pulses at 235 and 285. | At period 50, whole-track phase sums select 10 and 35. Before frame 200 the available evidence is the same. |

## Alignment and support

Use $\lambda=8$ in the basic path comparison.

| Fixture | Expected result |
| --- | --- |
| Length 400, unit pulses at $20+50j$ with frame 170 missing. Add strength 0.8 at 145 and 0.7 at 245. | At period 50 the path retains eight intended positions, including 170, and scores 7. Multiply novelty by ten to move the selected beat from 170 to 145. Multiply the penalty by ten as well to restore the path and score 70. |
| Length 400, pulses only at 20, 70, 120, 320 and 370. | The unrestricted path includes 170, 220, and 270. With a 100-frame observation limit, track the spans 20–120 and 320–370 separately. |
| One missed pulse between frames 120 and 220 with a 100-frame observation limit. | An observed zero at 170 permits interpolation at equality. A missing feature at 170 divides the run. A limit one sample below the observation distance also divides it. |
| Strength 4 at 20 and 120 with period 50. | The allowed direct edge has score $8-8\log^2 2=4.156376$. Its endpoints are both supported. A 90-frame elapsed-support limit splits the observations. |
| Length 1,200 with pulses at $20+60j$ before frame 600, and at $600+40j$ from 600 onwards. | Local raw autocorrelation selects periods 60 and 40 in the supplied windows. The path with those supplied periods matches all 25 beats. A fixed target of 60 gives 15 matches, 5 extras, and 10 misses at 70 ms. |

## Exact clock and evaluation

At 137 BPM, the period on a 100 Hz grid is $6000/137$ frames. Start
at frame 7. Adding 44 repeatedly produces 202.3358 ms of positive
error by beat index 99. Rounding each of the 100 ideal positions
to the nearest frame has maximum absolute error 4.9635 ms.

For the merged onset-input fixture, use $f_s=48000$, a periodic
Hann window with $M=N=960$, hop 480, and 350 complete frames.
Set the epoch origin to $2^{60}+37$. Place an impulse at
$(7+50j)480+480$ relative to origin for $j=0,\ldots,6$,
with $j=3$ omitted. For a containing frame, the impulse amplitude
spectrum is its window coefficient divided by the coherent sum,
with the paired positive bins doubled. Its weighted RMS is the
coefficient divided by the window's Euclidean norm. Use lag one,
two right frames, four preceding scores, and margin 0.01 in Skill #36.

Skill #36 confirms six onsets. Frame 0 has unavailable novelty.
Frame 157 has known zero. Use a 48,000-sample support cap for beat
tracking. The tempo estimate selects 120 BPM and the path contains
$[7,57,107,157,207,257,307]$. Exactly frame 157 is inferred. The
first beat center is 3839.5 samples relative to origin. Its
novelty frame ends at 4320 and its onset is ready at 5280. The beat
path uses the entire run through boundary 168480.

For beat matching, use reference frames $25+50j$ for $j=0,\ldots,15$.
Use 70 ms inclusive tolerance over the full declared interval. Exact,
half-rate, double-rate, and 25-frame offbeat estimates yield $F_1$ of
1, $2/3$, $2/3$, and 0. Half and double profiles have correct matches
at some positions. The offbeat profile retains the correct rate.
