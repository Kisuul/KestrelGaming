# Real cepstral analysis fixtures

Use raw one-sided DFT magnitudes and unit reference unless a row specifies
another input. Compare coefficients on the packed quefrency side. All
status, bin, length, and floor-mask assertions are exact. These tolerance
values apply to the corresponding fixtures.

## Parity, scaling, and echo

| Input | Expected result |
| --- | --- |
| Packed magnitudes `[1,1,4]` | At $N=4$, $c[q]=(\ln 4)(-1)^q/4$. At $N=5$, $c[q]=(2\ln 4)\cos(4\pi q/5)/5$. Compare with $2\times10^{-15}$ absolute tolerance. |
| Unit impulse, $N=16$ and 17 | Raw magnitudes are 1 and all cepstral coefficients are 0. Doubling only paired magnitudes produces the false component $c[2]=-2\ln 2/16$ or $-\ln 2/17$, respectively. |
| $x[n]=\delta[n]+0.4\delta[n-7]$, $N=255$ and 256 | $c[7]=0.2$, $c[14]=-0.04$, and $c[21]=0.4^3/6$ within $2\times10^{-14}$. Check the full packed side with the periodized series below. |
| Same amplitude, $D=8$ and $N=16$ | $c[8]=\operatorname{atanh}(0.4)=0.423648930194$. The positive and negative echoes coincide modulo 16. |
| Gain of 3 and circular shift of 11 samples on a prepared echo frame | Gain adds $\ln 3$ to $c[0]$. The remaining coefficients stay within $2\times10^{-14}$ of their previous values. A circular shift preserves the cepstrum. |
| All bins $2^{800}$ with reference $2^{-800}$, and the reversed pair | The direct ratios overflow or round to zero. The log offsets are $\pm1600\ln 2$. The other coefficients are zero. |

For the echo oracle at $0<a<1$, add
$(-1)^{m+1}a^m/(2m)$ at both indices $\pm mD$ modulo $N$ for
$m=1,2,\ldots$. This follows from the log series of the echo transfer
function. For $a=0.4$, terms beyond order 229 are negligible for the stated
tolerance. This check preserves the negative sign of the second rahmonic
and includes aliases.

## Nulls and relative floors

| Input | Expected result |
| --- | --- |
| Equal impulses at indices 0 and 8, $N=256$ | Packed nulls occur at 16, 48, 80, and 112. In strict mode, supply exact zero there and expect `spectral_null`. For an actual FFT, assert those magnitudes are small and check a relative floor. |
| All stored magnitudes zero | `silent` for strict and floored policies. |
| Peak 1 and $2^{-10}$ floor factor | Compare the value exactly at the floor and its adjacent binary64 values. Replace only the value below the floor. |
| Peak 1.3 and factor 0.1 | The rounded linear product is below the product of the exact represented inputs. A bin equal to that rounded product must still be marked floored. |
| Peak $2^{-900}$ and floor factor $2^{-300}$ | The linear product rounds to zero. For `[peak, smallest_positive_binary64, 0]`, only the final packed bin is floored. The log floor is about $-831.776616672$. |

## Symmetric lifters

At $N=32$ and 33, generate
$L[k]=\ln 2+0.6\cos(2\pi k/N)+0.4\cos(14\pi k/N)$ and use
$\exp L[k]$ as the input. At $Q=1$, expect log values
$\ln 2+0.6\cos(2\pi k/N)$ within $2\times10^{-15}$.
At $Q=0$, expect magnitude 2 at every bin. Keeping one side of a retained
pair in a full-array FFT introduces an imaginary residual.

For $N=16$, use $L[k]=0.3(-1)^k$. Then $c[8]=0.3$. At $Q=7$ the log
envelope is zero within roundoff. At $Q=8$ the envelope recovers the input.
At $N=4$, use $L[k]=[700,700,-700]$ and the signs reversed. The $Q=1$
envelope at bin zero has absolute log magnitude 1050 or −1050. Keep that
log result and mark only the unrepresentable linear bin.

For the wide-range regression, set $N=1024$ and $Q=417$. Use constant
magnitude $2^{-900}$ except for $2^{900}$ at stored bin $j=123$.
The log envelope at bin $k$ is:

$$
-900\ln 2 + \frac{1800\ln 2}{N}\left[D_Q(k-j)+D_Q(k+j)\right].
$$

Use $D_Q(r)=\sin((2Q+1)\pi r/N)/\sin(\pi r/N)$, with value $2Q+1$ at a
multiple of $N$. Check each packed bin with $3\times10^{-12}$ absolute
tolerance. This case exercises cancellation over a long lifter and a
large common log offset.

## Review tasks

1. Give the agent the same packed magnitudes with $N=4$ and 5. Require
   an explanation of the different results and a check of the stored
   transform length at the backend boundary.
2. Give the agent the delayed impulse and ask how to distinguish it
   from a periodic source that produces the same quefrency.
3. Ask for phase reconstruction as a routing check. Ask the agent to
   demonstrate a symmetric cutoff for a magnitude-envelope request.

These tasks define behavioral trials. The automated tests exercise the
transforms, floor decisions, and numerical range.
