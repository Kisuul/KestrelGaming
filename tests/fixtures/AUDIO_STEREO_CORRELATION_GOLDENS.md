# Stereo correlation fixtures

Use aligned original PCM and one rectangular window. Compare the signed
zero-lag coefficient, channel mean squares, exact availability, and
retention $G$ against average input channel power. Interpret all finite
decimal constants as represented inputs.

## Measurement and mono fold-down

| Input | Expected result |
| --- | --- |
| $L=[1,-1,1,-1]$, $R=L/2$. Then use $R=-L/2$. | Coefficients +1 and −1. Mono retentions $9/10$ and $1/10$. Mono RMS values $3/4$ and $1/4$. |
| One silent channel and one unit alternating channel. Then both silent. | The coefficient is unavailable in both cases. $G$ is $1/2$ in the first case and unavailable in the second. |
| $L=[1,-1,1,-1]$, $R=[1,1,-1,-1]$. | Both RMS values are one. The available coefficient is exactly zero and $G=1/2$. |
| Repeat $(1/4,-3/4)$ and $(3/4,-1/4)$. | The raw coefficient is $-3/5$. Removing each channel's mean yields a coefficient of +1 on the resulting input. |
| $L=[1,-1,1/8,-1/8]$, $R=[1,-1,-1/8,1/8]$. | The two halves give +1 and −1. Their combined product totals give $63/65$ and $G=64/65$. |

Take 480 samples at 48 kHz. Let $a$ be a 1 kHz cosine with peak $3/4$
and $b$ a 2 kHz cosine with peak $1/4$, both at zero phase. With
$L=a+b$ and $R=a-b$, the coefficient is 0.8 and $G=0.9$. The equal-weight
mono waveform is $a$. Use a coherent sine and cosine projection at
2 kHz. The two input peaks at that frequency are 1/4. The mono residual
should be below $10^{-15}$ in peak units for the test data.

On the same support, make $R$ a periodic copy of $L$ advanced or
delayed by 12 samples. At 500, 1,000, and 2,000 Hz, the coefficients
are $\sqrt{1/2}$, 0, and −1 for either shift sign. Use $2\times10^{-15}$
absolute tolerance for these tone coefficients and the two-tone ratios.

## Rounding and support

| Input | Expected result |
| --- | --- |
| $L=[1,1+d]$, $R=[1,-(1-d)]$, $d=2^{-52}$. | Exact mean cross-product $2^{-105}$. The coefficient rounds to $2^{-105}$. Scaling the planes in binary64 can erase the cross-product. |
| $L=[1,-1]$, $R=-(1-2^{-40})L$. | Mono RMS $2^{-41}$ and exact mean square $2^{-82}$. The residual survives the direct fold-down. |
| $L=[2^{-600},-2^{-600}]$, $R=[2^{600},-2^{600}]$. | Exact endpoint +1. Both RMS values are finite although the left power underflows and the right power overflows if converted to binary64. |
| $L=R=[\eta,0,0,0]$, $\eta=2^{-1074}$. | Each channel has exact RMS $\eta/2$. Both rounded RMS values are zero. The coefficient is +1 and both energies are positive. |
| $L=[B,0]$, $R=[\pm\eta,B]$, $B$ the largest finite binary64. | Coefficient rounds to signed zero from a nonzero cross-product. Keep the exact sign. |
| $L=[1,1]$, $R=[1,1+2^{-52}]$. | The value rounds to +1. The exact squared ratio is below one. |
| Length 4, hop 2, origin $2^{53}+1$. Use $L=[1,-1,1,-1,1/8,-1/8,1/8,-1/8]$ and invert its last four samples for $R$. | Coefficients +1, $63/65$, −1. Doubled centers 18014398509481989, 18014398509481993, and 18014398509481997. All callback partitions and explicit reversed plane order preserve the result. |

For root ties, use the exact square of the midpoint between adjacent
binary64 values. Compare the roots just below, at, and just above the
midpoint. At equality the even low bit selects the result. Exercise
midpoints in the subnormal range and on both sides of a power of two.

## Review tasks

1. Give an agent a broadband meter near +0.8 with one tone missing in
   mono. Ask for the source tap, the actual mix weights, and a direct
   measurement that identifies the missing band.
2. Give it two meters that report +1 and +0.8 for the same proportional
   stereo pair. Ask it to locate the difference in their estimators.
3. Give it a signed-zero reading from underflow and a separate silent
   channel. Ask which exact checks determine coefficient availability.

Record the agent's observed decisions with evidence from the task.
