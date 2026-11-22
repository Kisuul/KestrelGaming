# Audio cross-correlation fixtures

Use reference-first order at 48 kHz. Report the full curve and paired
intervals along with any selected delay. Use a common capture start
except for cases that specify different origins.

| Input | Expected result |
| --- | --- |
| Lengths seven and eleven. Reference index 2 holds 2 and measurement index 6 holds 3. Other samples are zero. | Lag $+4$, raw sum 6, and seven pairs. Inversion yields score $-6$ at the same absolute peak. Channel swap yields lag $-4$. If $+4$ is the evaluated bound, flag the edge. |
| $x=[0,0,1,0]$, $y=[1,0,0,0]$, with $s_x=2^{60}+1$ and $s_y=2^{60}+6$. Search clock delays 0 through 4. | Evaluated delays 2 through 4. Local lag $-2$ pairs reference indices $[2,4)$ with measurement indices $[0,2)$. Clock delay $+3$ is 62.5 microseconds. |
| $x=[0,0,0,1]$, $y=[1,0,0,0]$. | The linear curve peaks at $-3$. A four-point circular calculation puts its maximum at index 1. |
| $x=[3,-1,4,-2,1,5,-4,2]$, $y=[2,-3,3,-1,4,-1,1,5]$. | One-pair cosine is one at $\pm7$. With at least six pairs the absolute peak is $+2$, about 0.991201182589. |
| Repeat $[1,0,-1,0]$ over 32 samples. Delay the measurement by one sample using periodic extension. Crop the reference to $[8,24)$ and search clock delays $-6$ through $+6$. | All overlaps have 16 pairs. Positive ties are $-3,+1,+5$. Absolute ties include $-5,-1,+3$ with negative sign. |
| Unit impulse at reference index 4. Measurement impulses at indices 7 and 13 have amplitudes $1/4$ and 1. Use length 32. | The strongest peak is $+9$. The earlier arrival is $+3$ and appears as the next score group. |
| Use PCM $x=2^{40}+[-2,-1,1,2]$ and reverse for $y$. Use a constant reference in a separate trial. | At zero lag centered power is $5/2$ per channel and Pearson is $-1$ for the reversed record. The constant reference gives unavailable Pearson. |
| $x=[1,0]$, $y=[1,2^{-30},1,0]$. Compare two-pair lags 0 through 2. | Lag $+2$ beats lag 0 exactly. Both show 1 in binary64. |
| $x=[1,0]$, $y=[2^{-600},1]$ at zero lag. | The positive binary64 cosine is $2^{-600}$. Rounding the squared ratio first would give a zero coefficient. |

Check finite PCM up to the maximum binary64 magnitude and down to
subnormals. Check raw zero for silence, missing normalized scores,
and a measured zero cross term with positive powers. Replay valid
captures through different callback partitions. Check channel order,
both level floors, mismatched capture clocks, and search bounds.

## FFT, fractional delay, and weighting

Compare a direct curve with two padded FFT lengths per record pair
and with SciPy 1.17.0 direct and FFT modes. Use
`correlate(y, x, mode="full")` and `correlation_lags(N_y,N_x,mode="full")`.
Seed 340020 gives 418 lags and 836 padded FFT comparisons. The
independent expected value for each lag is the sum of all original
pairs with that index difference.
[Research reproduction parameters](https://github.com/Kisuul/KestrelGaming/blob/f80718da04cb224ed45c8aeba496fb89089f282a/memory/projects/kisuul/kestrelgaming/handoffs/2026-11-21-audio-cross-correlation-research-r01.md#executed-checks-and-portable-fixtures)

For a true delay of 2.35 samples, the three stated sinc bandwidths
give integer peak $+2$. The three-point fit yields 2.231788, 2.326345,
and 2.344364 samples. For the two-band frequency-grid comparison,
unweighted, all-bin PHAT, and strong-band-only PHAT give $+3$, $+11$,
and $+3$. Use the research parameters to reproduce them.

## Review tasks

1. Give the agent the shifted capture starts and impulse positions.
   Ask for the local lag, clock delay, and paired intervals.
2. Give it the periodic capture and the permitted delay range. Ask
   which tied peaks qualify and which probe would resolve them.
3. Give it an impulse response with two arrivals. Ask which peak
   measures the strongest path and how to verify the first arrival.

Record the agent's decisions and evidence separately from execution
of the numerical tests.
