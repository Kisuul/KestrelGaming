# Phase and coherence fixtures

Use ordered reference and measurement captures at 48 kHz. Use a
rectangular window and retain DC unless the fixture specifies another
profile. Keep complete segment starts and the used sample interval.

## Segment products and phase

| Input | Expected result |
| --- | --- |
| One-bin segment vectors $X=[1,1]$, $Y=[1,-1]$. Use two length-two segments with PCM $x=[1,0,1,0]$, $y=[1,0,-1,0]$ for the same products. | Both auto powers are positive. The cross-product sum is zero. Coherence is zero and phase is unavailable. Each segment separately gives unity coherence. |
| $X=[1,1]$ and $Y=[1,3]$, then $Y=[-1,-1]$. | Gain variation gives coherence $4/5$ and phase zero. Inversion gives unity coherence and phase $\pi$. The equally weighted mono signal cancels for the inverted case. |
| $X=[1,1]$, $Y=[-1+i\tan(1^\circ),-1-i\tan(1^\circ)]$. | The pooled phase is $\pi$ and coherence is about 0.99969541351. |
| Four length-64 segments of a 3 kHz cosine, with a periodic extension. Delay the measurement four samples. In a second trial advance it four samples. | At bin 4 both coherence values are one. The phases are $-\pi/2$ and $+\pi/2$. Channel swap conjugates the cross-density. |
| Nine samples with a reference impulse at index 3 and a measurement impulse at index 4. Use length and hop four. Repeat with $x[0:8]$ paired with $y[1:9]$. | The original pairing has coherence zero and phase unavailable in all three bins. The revised pairing has coherence one and phase zero with one energized pair. |

## Density and range

Let $B$ be the largest finite binary64 PCM value and
$\eta=2^{-1074}$ its smallest positive value.

| Input | Expected result |
| --- | --- |
| $x=[1,0,1,0]$, $y=[0,1,0,1]$, length and hop two, DFT length four. | DC cross-density is $1/(2f_s)$, bin 1 is $-i/f_s$, and Nyquist is $-1/(2f_s)$. Both endpoints are real. The phases are $0,-\pi/2,\pi$. |
| Repeat the preceding fixture with DFT length five. | Reference auto density at the last bin is $1/f_s$. Highest-bin cross phase is $-4\pi/5$. |
| Both channels contain four copies of $B$, length and hop two. | DC density is $2B^2/f_s$, and coherence is one. An unscaled binary64 DFT sum overflows for each segment. |
| Four copies of $\eta$ in the reference and $-\eta$ in the measurement, length and hop two. | DC density is positive even if a binary64 display rounds it to zero. Coherence is one and phase is $\pi$. |
| $x=[B,B,\eta,\eta]$, $y=[0,0,B,B]$, length and hop two. | The DC cross-product sum is $4B\eta$. The exact coherence $\eta^2/(B^2+\eta^2)$ is positive although its binary64 conversion is zero. Phase is zero. |

Repeat with overlap, both detrending rules, odd and even transforms,
and a large sample origin above $2^{53}$. Supply a partial tail with
large finite values. Check that complete segment support and measured
products agree across callback partitions. Also check silence, warm-up,
invalid profile values, channel label order, and an explicit epoch reset.

For a differential check, match window samples, segment starts, input
order, and normalization with SciPy 1.17.0. Compare complex density on
all 72 bins of the four seeded profiles. Check each auto-density integral
against mean tapered energy divided by window energy. Use absolute
error for small densities and wrapped error for phase.
[Seeded profiles](https://github.com/Kisuul/KestrelGaming/blob/beda56539e68bc7fcf8e3a62b3f81d1c107db1d1/memory/projects/kisuul/kestrelgaming/handoffs/2026-11-21-audio-phase-coherence-research-r01.md#executed-checks-and-portable-fixtures)

## Review tasks

1. Give the agent the original taps, segment starts, and impulse
   positions. Ask it to predict the paired support and choose the
   alignment measurement that tests its diagnosis.
2. Give the agent unity coherence and phase $\pi$ from the inverted
   fixture. Ask it to predict the result for the declared equal-weight
   fold and identify the output tap that verifies delivery.
3. Give the agent the two extreme-range densities and the binary64
   coherence display. Ask it to find evidence of a positive cross term.

Record the agent's decisions and the sample or signal evidence it uses.
