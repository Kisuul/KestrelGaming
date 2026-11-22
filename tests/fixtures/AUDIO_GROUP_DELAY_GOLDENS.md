# Audio group delay fixtures

Use 48 kHz unless specified. Keep the sign, sample support, offsets,
and aperture with every result.

| Fixture | Expected result |
| --- | --- |
| $h[n]=-2\delta[n-12]$ and $h[n]=-2\delta[n]$. | +12 samples or 0.25 ms for the delayed model. Valid zero for the constant inverted model. |
| FIR $[1/2,1/2]$ and $[1,0,1]$. | Delay $1/2$ and 1 sample where valid. The first has a Nyquist zero. The second has a 12 kHz zero. |
| $[1,0,1]$ sampled at bins 31 and 33 of a 128-point transform, or bins 31 and 32 of a 126-point transform. | The naive crossing slopes are −31 and −62 samples. Both 126-point endpoint magnitudes are positive. The intervening zero makes the crossing unavailable. The valid sides have +1 sample. |
| All-pass $H=(z^{-1}-3/4)/(1-(3/4)z^{-1})$ with an optional 12-sample delay. | Delay changes from 7 samples at DC to $1/7$ at Nyquist. The cascade adds 12. |
| $h[n]=\delta[n]+(3/4)\delta[n-24]$. | Group delay $72/7$ samples at DC and −72 at 1 kHz. First and largest impulse at index 0. |
| A 40-sample delay on 64- and 128-point grids. | The 64-point principal slope aliases to −24. A known 38-sample advance gives residual +2 and restored +40. The 128-point grid with a qualified bound gives +40. |
| A 40-sample delay with 128-point grid bins 0 through 4. | The endpoint angle alone gives +8 samples. Four qualified increments give +40 over the 1,500 Hz aperture. |
| A 40-sample delay with 5 samples already advanced. Fit another 32 on a 64-point grid. | Residual +3 and restored +40. Keep both offsets in the result. |
| Sample an inverted 12-sample delay at $[100,145,300,310,425,659]$ Hz. | Secants on actual Hz coordinates and the research weighted fit both recover +12. |
| $t+jt$ and $t-jt$ at 0 and 12 kHz, for maximum finite or smallest positive binary64 $t$. | Phase increment $-\pi/2$ and +1 sample with a qualified edge. |
| Use unknown branch bounds, a bound of exactly half a turn, a rejected bin, and an interior gap on an otherwise smooth transfer. | Every aperture crossing an invalid edge is unavailable with its first failure reason. |

For the model differential, use 513 frequencies from DC to Nyquist
for the inverted delay, two FIRs, all-pass, delayed all-pass, and
echo. The two exact nulls leave 3,076 comparisons against closed
forms and SciPy 1.17.0.

For the paired transfer, use six length-128 rectangular segments.
In segment $j$ place an impulse of amplitude $1+j/8$ at reference
index $21+7j$. Put its negatively scaled copy at index $33+7j$.
Use gain −2 and retain DC. Compare all 64 adjacent slopes in
each channel order. Repeating the period $[1,0,-1,0]$ instead gives
unity coherence at 12 kHz with no neighboring supported slope.

Use the $c=0.98$ all-pass at 200 Hz. The point derivative is
36.952603 samples. Apertures of 20 Hz and 360 Hz give noiseless
secants of 36.981683 and 44.826944 samples. Use enough qualified
phase steps for each aperture. With independent 1-degree endpoint
noise and seed 350050, the observed standard deviations were
9.523162 and 0.521227 samples in that order.
[Research reproduction parameters](https://github.com/Kisuul/KestrelGaming/blob/f6fa12046b811ecc611e34c53629a48168a71f1d/memory/projects/kisuul/kestrelgaming/handoffs/2026-11-21-audio-group-delay-research-r01.md#executed-checks-and-portable-fixtures)

## Review tasks

1. Give the agent the coarse and fine delay grids. Ask what evidence
   qualifies the branch and how to verify the original tap delay.
2. Give it the notch at a bin and between bins. Ask which apertures
   remain available when comparing the two grids.
3. Give it the signed echo fixture. Ask which measurement answers
   the first-arrival question and what the negative slope describes.

Record the agent's decisions and supporting evidence.
