# Intermodulation fixture values

## Coherent levels

Use 480 samples at 48 kHz. Place local offset zero at
sample $2^{60}+37$. Use a rectangular window and no
padding. Generate cosine-phase carriers at 7 and 8 kHz
with peaks $A=0.2$ and $B=0.1$. Apply
$y=x+0.05x^2+0.1x^3$.

| Line | Bin | Peak | Mean-square power |
| --- | ---: | ---: | ---: |
| Low carrier | 70 | 0.2009 | 0.020180405 |
| High carrier | 80 | 0.100675 | 0.0050677278125 |
| $f_2-f_1$ | 10 | 0.001 | $5\times10^{-7}$ |
| $f_1+f_2$ | 150 | 0.001 | $5\times10^{-7}$ |
| $2f_1-f_2$ | 60 | 0.0003 | $4.5\times10^{-8}$ |
| $2f_2-f_1$ | 90 | 0.00015 | $1.125\times10^{-8}$ |

For this isolated polynomial model, the quadratic sum
and difference each have peak $|a_2AB|$. The near-carrier
cubic products have peaks $3|a_3A^2B|/4$ and
$3|a_3AB^2|/4$. The cubic carrier terms add
$a_3(3A^3/4+3AB^2/2)$ to the low peak coefficient and
$a_3(3B^3/4+3A^2B/2)$ to the high peak coefficient.

Double both input peaks. The quadratic line peaks grow
by four and the cubic peaks by eight. Use a linear
control and separate square and cubic runs to check
product assignment. Interpret small computed line values
on the linear control in light of the DFT roundoff.

Use only the two near-carrier cubic products for the
IM3 group. Their total power is $5.625\times10^{-8}$.
The lower IM3 line gives −56.517174 dBc referenced to
the low carrier and −50.516008 dBc referenced to the
high carrier. The IM3 group ratio to both measured
carriers is 0.1492610974% or −56.521067 dB.
The two quadratic products give 0.6293400452% with
the both-carrier power reference. The arithmetic
amplitude ratio for those same lines is 0.6631849457%.

## Geometry and qualification

| Probe | Expected result |
| --- | --- |
| Use 19 and 20 kHz with the original peaks and $y=x^2$. Model products through order two. | With 960 frames at 96 kHz the sum is in bin 390 at 39 kHz. With 480 frames at 48 kHz it folds to bin 90 at 9 kHz. Both peaks are 0.02. This pure-square case supplies line-level evidence. |
| Allow order three for that pair with digital folding. | The lower third harmonic at 57 kHz shares the observed sum bin at both rates. The product status is \`collision\` even if the known square trace has zero cubic coefficient. |
| Use verified band limiting at 48 kHz for the 19 and 20 kHz pair. | The 39 kHz product has no assigned observed line. Its possible fold bin is 90. |
| Use 3 and 7 kHz with $y=x+0.1x^3$. | $2f_1-f_2$ has signed frequency −1 kHz. Its observed bin is 10, with peak 0.0003 and no above-Nyquist fold. |
| Use 4 and 8 kHz with the baseline polynomial. | The difference shares the low carrier. The second harmonic of the low carrier shares the high carrier. $2f_1-f_2$ shares DC. The sum, $2f_2-f_1$, and $3f_1$ share the 12 kHz bin. |
| Use 9 and 15 kHz with $y=x+0.1x^3$. Shift the high tone by a quarter turn in the second capture. | The 27 kHz third harmonic folds onto the 21 kHz near-carrier product. The two phases give shared bin peaks 0.00035 and 0.00005. Individual ratios are unavailable. |
| Set carrier bins to 5 and 11 with $y=x+x^2$ and a second-order family. | The sum has peak 0.02 at bin 16 in both captures. Its power is 0.0004 at $N=32$ and 0.0002 at $N=33$. Disabling Nyquist excludes the even bin only. |
| Limit the baseline band to [1,000, 9,000] Hz. | Both edges enter. The sum at 15,000 Hz retains its power and has status \`out_of_band\`. The four-member ratio is unavailable. A declared two-member IM3 subset remains valid. |
| Use a positive floor equal to the smaller baseline carrier power, then raise it. | At equality both carriers qualify. Above that power, the reference is unavailable and the raw line powers remain. |
| Test silence and an exact zero-power product with qualified carriers. | Silence has unavailable ratios. Under a qualified reference, an exact zero-power product contributes zero and gives $-\infty$ dB. |

[Executable fixture checks](../test_audio_intermodulation_reference.py) ·
[Research fixture and longer spans](../../memory/projects/kisuul/kestrelgaming/handoffs/2026-11-26-audio-intermodulation-research-r01.md#executed-checks-and-portable-fixtures)
