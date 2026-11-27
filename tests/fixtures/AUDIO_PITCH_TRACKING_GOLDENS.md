# Audio pitch tracking fixtures

[Reference](../../skills/audio-pitch-tracking/scripts/reference_pitch_tracking.py) ·
[Contract](../../skills/audio-pitch-tracking/references/PITCH_TRACKING_CONTRACT.md) ·
[Executable checks](../test_audio_pitch_tracking_reference.py)

Use $f_s=48000$ Hz and one rectangular PCM channel unless a row
specifies a different clock. Set the threshold to $1/10$ and AC
RMS floor to zero unless stated. Treat each period band as closed.
Use raw-difference refinement by default. Repeat the same
finite cycle array for exact periodic fixtures.

## Exact difference and voicing

| Input and profile | Expected evidence |
| --- | --- |
| $W=3$, integer band $[2,3]$, PCM $[1,3,0,2,4,1,-2]$. | Evaluate through lag four using three pairs per lag. Raw curve $(0,17,18,3,17)$. CMND $(1,1,36/35,9/38,68/55)$. |
| $W=1$, integer band $[2,3]$, PCM $[1,1,2,1,2]$. | CMND has no value at lag one. Lags two through four give $(2,0,2)$. Select lag three. |
| $W=7$, band $[2,4]$. Supply a complete frame of zero, $0.125$, or $-7$. | Report silence for zero and DC only for the other two. Retain the signed mean. All positive-lag CMND values are unavailable. |
| Same grid with an AC RMS floor of $1/4$. Repeat $(3/4,1/4)$ or $(5/8,3/8)$ over the frame. | Both means are $1/2$. AC powers are $1/16$ and $1/64$. Both have the same CMND. The first is voiced at equality. The second is below floor and has no selected pitch. |
| $W=960$, band $[48,320]$. Draw one complete frame with Python's Random seed 390091, uniform on $[-0.2,0.2]$. | Complete unvoiced frame with local troughs and no eligible candidate. |

Use a repeated dyadic fixture and an exactly represented common
gain and DC offset to check CMND invariance. For alternating
$+a,-a$ with $W=7$, check $d(1)=28a^2$ and an eligible lag two
at Nyquist. Run one case for the least positive binary64
subnormal and one for the largest finite binary64. Keep the
reference output exact before converting it for display.

## Octave and source decisions

Use $W=960$ and band $[48,240]$. Repeat a 120-sample cycle with
$x[n]=0.30\cos(2\pi n/60)+b\cos(2\pi n/40)$.

| Input | Expected evidence |
| --- | --- |
| $b=0.20$. | $d(40)/W=0.135$ and $d(60)/W=0.08$ within $3\times10^{-16}$. $d(120)=0$ exactly. Select lag 120, 400 Hz, with only 800 and 1,200 Hz components. |
| $b=0$ and repeat a 60-sample cycle. | Select lag 60, 800 Hz. Source assumptions would be needed to choose 400 Hz. |
| $b=0.03$, integer profile. | CMND at 60 is about 0.019798713 and at 120 is zero. Both are eligible. Select 60. Set the threshold to the exact represented depth of lag 60. Its status becomes threshold rejected at equality. |
| $b=0.09$, integer profile. | CMND at 60 is about 0.164910673. Retain that rejected candidate. Select 120. |

Use $W=960$, band $[48,320]$, and repeat 240 samples of
$0.30\cos(2\pi n/120)+0.25\cos(2\pi n/80)$. The input has 400
and 600 Hz components. The aggregate gives eligible lag 240,
200 Hz. A per-source result needs more evidence.

## Fractional and edge cases

Use $W=960$ and a cosine at amplitude $0.4$. For the 437.5 Hz
tone with true period $768/7$ and band $[48,240]$, both profiles
select seed 110. The raw fit gives about 437.50135765 Hz
($+0.00537235$ cents) and the CMND fit gives about 437.51494149 Hz
($+0.0591240$ cents). Compare the signed error with a declared
tolerance. One fixture measures one profile's local bias at one
phase and frequency.

| True period | Physical band | Expected guarded result |
| --- | --- | --- |
| 96.25 | $[96.125,98.125]$ | Raw fit seed 96, last evaluated lag 100, period about 96.24991686. |
| 119.75 | $[118.25,119.875]$ | Raw fit seed 120, last evaluated lag 121, period about 119.75004015. |
| $768/7$ | $[109.7141,109.715]$ | Keep the raw fit from seed 110 as out of band. Report unvoiced with this evidence. |

The integer search misses both valid edge seeds. Use the
reference frequency range after fitting. For the plateau fixture
$W=1$, band $[2,4]$, PCM $[0,1,0,0,1,1]$, use seed two once
and fit to 2.5 samples with raw refinement. With
$[0,100,100,10,9.99,1]$ on the same grid, the CMND trough is
at three while raw difference is falling to its right.
Retain the integer fallback at three.

## Small comparison support

At 48 kHz, use $x[n]=0.4\cos(2\pi(n-315)/960)$, period
band $[48,960]$, and CMND refinement. The guard lag is 961
in both cases. An earlier trough can pass the threshold when
the comparison covers little of each cycle.

| $W$ | Required $M$ | First selected seed | Estimated frequency |
| ---: | ---: | ---: | ---: |
| 63 | 1024 | 568 | 84.47736 Hz |
| 1920 | 2881 | 960 | 50.00003 Hz |

Inspect CMND at lag 568 in the short frame. Its depth is about
0.063747759 and passes the default threshold. Measure support
and center-to-readiness cost together when choosing $W$.

## FFT and cancellation checks

For a direct-to-FFT differential use NumPy 2.3.5 and SciPy
1.17.0. Draw uniform $[-1,1)$ samples in order from
PCG64 seed 390039. Use $(W,P)$ of $(96,120)$, $(129,91)$,
$(192,128)$, and $(257,199)$ with $W+P$ samples each. Compare
direct paired differences with the two energies and valid
linear correlation of the frame and its first $W$ samples.
Include 538 positive lag checks and four zero-lag controls.

For the cancellation probe use $W=960$, $P=241$, and
$x[n]=0.5+2^{-30}\cos(2\pi n/(768/7))$. The largest reference
difference is about $1.67\times10^{-15}$ squared PCM. In the
stated FFT run, all 241 positive lags gave negative differences
and the largest absolute error was about $5.13\times10^{-13}$.
Subtract one common $x[0]$ first and recompute. The largest
absolute error in that run was about $5.33\times10^{-30}$.
FFT roundoff varies with the transform and hardware. Check error
relative to the available evidence.

## Clock and delivery

Use an origin $O=2^{60}+37$, $W=7$, band $[2,4]$, and
$H=4$. A complete frame starting at $O+12$ has $M=12$,
center twice $2O+35$, and ready boundary $O+24$. Allow an
observed boundary of $O+27$. Repeat on a rate of $48000/1001$
Hz with alternating PCM. The lag-two estimate is $24000/1001$
Hz. For a two-sample partial frame at $O+8$, retain available
end $O+10$, nominal end $O+20$, and center twice $2O+27$.
The ready boundary, level, and curve are unavailable.

Replay the test tape with $W=24$, integer period band $[8,16]$,
and hop 16. Compare a single block, one sample per block, and
seeded irregular blocks. Keep the selected lag, evidence, support,
and exact center equal. Each observed delivery boundary is
the first block end at or after readiness. Drop pending history
when opening an epoch after a seek. A gap or an overlap in one
epoch raises an error before accepting the block.
