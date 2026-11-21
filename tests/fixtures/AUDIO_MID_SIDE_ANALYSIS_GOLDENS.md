# Mid/Side analysis fixtures

Use the amplitude-normalized convention $M=(L+R)/2$ and $S=(L-R)/2$.
Compare exact samples, powers, and fractions before binary64 rounding.

## Matrix, energy, and range

| Input | Expected result |
| --- | --- |
| $(L,R)$ equal to $(1,1)$, $(1,-1)$, $(1,0)$, $(0,1)$, or $(0,0)$. | $(M,S)$ equal to $(1,0)$, $(0,1)$, $(1/2,1/2)$, $(1/2,-1/2)$, or $(0,0)$. The Side fractions are 0, 1, $1/2$, $1/2$, and unavailable. |
| All 121 pairs with each value chosen from $i/4$ for integers $-5\le i\le5$. | The exact inverse recovers both samples. Verify $M^2+S^2=(L^2+R^2)/2$ and $MS=(L^2-R^2)/4$. Swapping channels reverses only Side. |
| $L=[1,-1]$ and $R=(1-2^{-40})L$. Add common or differential DC in separate cases. | The original Side power is $2^{-82}$. A common offset shifts only Mid. Opposite offsets shift only Side. |
| $B$ the largest finite binary64 value and $\eta=2^{-1074}$. Use $(B,B)$, $(B,-B)$, $(\eta,\eta)$ and $(\eta,-\eta)$. | The active component keeps amplitude $B$ or $\eta$ and the other component is zero. Each active RMS is finite. |
| $(\eta,0)$. | Both exact components are $\eta/2$ and have power $(\eta/2)^2$. Their binary64 RMS values are zero with rounded-to-zero status. The exact Side fraction is $1/2$. |
| $(B,B)$ and $(\eta,-\eta)$ in the same window. | $F_S=\eta^2/(B^2+\eta^2)$ stays positive as an exact ratio. Its binary64 conversion is zero. |
| $(1,2^{-60})$. | The exact inverse recovers the right sample. Binary64 conversion gives 0.5 for both components. Their rounded inverse gives zero on the right. |

Use squared midpoints between adjacent binary64 RMS values for exact
rounding tests. Include the zero midpoint $\eta/2$, both parities
of the finite endpoints, and a boundary where the spacing doubles.

## Gain and the mono path

| Input | Expected result |
| --- | --- |
| For every input pair on the exact grid, choose each gain from $-2,-1,-1/2,0,1/2,1,2$. | Across all 5,929 cases, the Mid/Side decode equals the L/R matrix. Mono is $g_MM$. Each gain combination attains its sharp sample bound on the grid. |
| $(L,R)=(1,0)$, $g_M=1$, $g_S=2$. Clamp each reconstructed channel to $[-1,1]$. | The linear pair is $(1.5,-0.5)$ with mean 0.5. The clamped pair is $(1,-0.5)$ with mean 0.25. |
| $S=[1,0,0]$ and $M=[0,0,0]$. Delay Side before decoding. In a separate path, delay only the decoded right channel. | The first aligned fold-down is $[0,0,0]$. The second is $[1/2,-1/2,0]$. |
| FLAC input integers $(1,0)$ and $(-32768,32767)$. | Integer outputs are $(0,1)$ and $(-1,-65535)$. The Side parity completes the inverse. The analysis matrix gives $(1/2,1/2)$ for $(1,0)$. |

## Band and sample support

Take 480 samples at 48 kHz. Let $a$ be a 1 kHz cosine at peak amplitude
0.75 and $b$ a 2 kHz cosine at peak amplitude 0.25. Start both at zero
phase. Set $L=a+b$. Compare $R=a+b$ with $R=a-b$. Both cases have L/R
peaks of 0.75 and 0.25 at bins 10 and 20. The whole-window Side fraction
is 0 then 0.1. At bin 20 the fraction is 0 then 1. Check the direct
component projections and the complex cross-term identity with
$2\times10^{-15}$ absolute tolerance for this fixture.

Replay the same sample pairs through the shared capture with arbitrary
callback partitions and explicit reversed plane order. Check original
indices above $2^{53}$. Exercise rejected blocks, gaps, and an epoch
reset while keeping exact sample support in each measurement.

## Review tasks

1. Supply the two L/R magnitude spectra and their different mono
   outputs. Ask where the 2 kHz component lies in each case and which
   measurement can verify it.
2. Supply the gain and clamp fixture. Ask which stage first changes the
   mono waveform.
3. Supply the two delay paths. Ask the agent to identify the side-channel
   processing and sample pairing that leads to each result.

Record the agent's observed decisions and measurement evidence.
