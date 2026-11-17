# Fractional-octave RTA fixture ledger

Reproduce the analytic fixtures with the [standard-library suite](../test_audio_fractional_octave_rta_reference.py).
The reference's scope and commands are in the [measurement contract](../../skills/audio-fractional-octave-rta/references/FRACTIONAL_OCTAVE_RTA_CONTRACT.md).
The fixture signals are synthetic.

## IEC base-10 geometry

The 65-digit Decimal oracle uses IEC 61260-1's $G=10^{0.3}$, computes the
center as a multiple of 1 kHz, and multiplies or divides by the half-band
ratio for the edges. The table shows rounded examples from those equations.
Tests compare against the higher precision values with relative tolerance
$3\times10^{-15}$ for the sampled indices. This covers rounding the
binary64 base-10 exponent and logarithmic frequency conversion over the
tested range. The 1 kHz center or edge and adjacent binary64 edge identity
are exact checks. The common edges and one-ULP interval checks use exact
binary64 equality.

| Family | Index | Center (Hz) | Lower edge (Hz) | Upper edge (Hz) |
| --- | ---: | ---: | ---: | ---: |
| 1/1 | 0 | 1000 | 707.945784384 | 1412.537544623 |
| 1/3 | 0 | 1000 | 891.250938134 | 1122.018454302 |
| 1/3 | 1 | 1258.925411794 | 1122.018454302 | 1412.537544623 |
| 1/6 | −1 | 944.060876286 | 891.250938134 | 1000 |
| 1/6 | 0 | 1059.253725177 | 1000 | 1122.018454302 |
| 1/12 | 0 | 1029.200527194 | 1000 | 1059.253725177 |
| 1/24 | 0 | 1014.495208069 | 1000 | 1029.200527194 |

## Analytic and adversarial vectors

Unless specified, the power tests take one 64-sample unpadded rectangular
segment at 8 kHz, with no detrending. Origin is 23, epoch is `fixture` and
channel is `L`. Tone amplitudes below are peak values in units of normalized
sample amplitude. Coherent tones and their sums have closed-form mean-square
values from discrete orthogonality. Use relative power or RMS tolerance
$4\times10^{-14}$ for these short transforms and absolute level tolerance
$2\times10^{-13}$ dB for the 1 kHz calibration. These tolerances cover
rounding in tone generation, FFT operations and frequency edges. Power-of-two
and exact-zero checkpoints use exact equality.

| Vector | Expected evidence |
| --- | --- |
| 1 kHz tone at peak 0.5, third-octave index 0 | $Q=1/8$, RMS $1/\sqrt{8}$, −9.030899869919436 dBFS. Span [23, 87) |
| Same signal with fraction 1/6 | The two 1 kHz edge neighbors each get $1/16$. The 1 kHz bin is centered on the shared edge and the neighbors cover the bin |
| 875, 1125 and 2000 Hz at peaks 0.5, 0.25 and 0.75, octave bands | 1 kHz octave has 0.15625 power, next octave has 0.28125. Whole spectrum has 0.4375 |
| Anti-phase stereo plus a half-amplitude third channel | First two spectra match. The third has one quarter of their band power. Permuting the planes and labels permutes the channel results |
| Silence, or rectangular DC at 0.25 | Full bands report 0 power and −∞ dBFS. Whole power is 0 or 0.0625, respectively |
| 0.5 DC, 8-sample periodic Hann | Whole power 0.25. Bin 1 carries one third of it before allocation. A 7-sample constant 0.1 with mean removal gives exact zero |
| Unit impulse at sample 0, 2 kHz, 128-point FFT | Every two-sided DFT magnitude is 1. Whole power is $1/64$. For the 1/6 band ending at 1 kHz, power is $2(1000-891.2509381337456)/(2000\times64)$ |
| Alternating +1 and −1 at 2 kHz, 1/6 family | Whole power and power for the band ending exactly at 1 kHz are both 1. Bands starting at or above 1 kHz are unavailable |
| Same alternating sequence at 1999 and 2001 Hz | The band ending at 1 kHz is truncated at 1999 Hz. It is full at 2001 Hz and receives $1-0.5/(2001/128)$ of the Nyquist power |
| 48 kHz, 64-point FFT | The positive cell domain begins at 375 Hz. The third-octave bands near 316 and 398 Hz return `unresolved_dc` |
| Synthetic 1 Hz cells for $S(f)=1/f$ | Ideal third-octave power is $\ln(10)/10$. The midpoint hold has an absolute error bound $(f_u-f_l)\,0.5/[f_l(f_l-0.5)]$ within the selected range |
| Synthetic cell bounds at 1.5 Hz and adjacent floats | Cells of width 1 Hz receive exactly $2^{-52}$ on each side that overlaps. Touching a boundary alone contributes zero |
| Direct DFT and Parseval, 60 samples padded to 128, seed 1809 | Per-bin comparator is the [PSD skill's direct DFT](../../skills/audio-power-spectral-density/scripts/reference_psd.py). Check relative bin-power error within $5\times10^{-12}$ on this vector and independently computed prepared time-domain power within $4\times10^{-14}$ |
| 4 kHz, 1 kHz quarter-cycle PCM sequence at peaks $2^{-128}$ and $2^{128}$ | Expected band powers are $2^{-257}$ and $2^{255}$. No numerical floor or clipping |
| Three 4 kHz quarter-cycle segments at peaks $2^{80},2^{-80},2^{-80}$, two-segment mean | Consecutive band powers are $2^{158}$ and $2^{-161}$ under binary64 rounding. The quiet result checks history after the loud frame leaves |
| Smallest positive binary64 as synthetic bin or segment power | Underflow to zero during projection or averaging raises an arithmetic error |
| 203 samples, 60-sample segments, 17-sample hop, three segments per mean, origin $2^{53}+17$ | Identical results for whole and partitioned input. First span length 94, exact integer starts at offsets 0, 17, 34, 51, 68, 85 and 102 |
| A late invalid plane, gap, overlap, arithmetic rejection or reused epoch | A retry matches the corresponding uninterrupted stream. A valid fresh epoch clears overlap and history |

## Independent SciPy differential and seeded noise trials

Local environment was Python 3.12.14, NumPy 2.3.5 and SciPy 1.17.0. The
reference and regression suite require only the standard library. These
extra checks use SciPy as a separate PSD implementation and Decimal
geometry with a separate vectorized cell-intersection calculation.

Generate independent Gaussian planes with `numpy.random.default_rng(seed)`.
For the differential signal use `0.2 + rng.normal(0, 0.25, length)` for each
channel in order. Use the inclusive default center limits of 20 to 20,000 Hz.
For each contributing span, call `scipy.signal.welch` with the same
`fs`, `nperseg=M`, `noverlap=M-H`, `nfft=N` and per-segment detrending
mode. Pass a periodic Hann or boxcar from `get_window(..., fftbins=True)`.
Use one-sided density and mean averaging. For the band oracle multiply
density by $f_s/N$, skip bin zero and apply each cell's intersection fraction
using the independent Decimal edges. Check full bands and the whole PSD
integral. The local comparison threshold was $5\times10^{-12}$ relative
to the expected power.

| Input | Configuration | Band comparisons | Max relative error, including total power |
| --- | --- | ---: | ---: |
| 48 kHz stereo, seed 243, 3,045 samples per channel | $M=1000,H=409,K=4,N=2048$, Hann, mean removal, three frames per channel across all five fractions | 2,760 | $1.344\times10^{-13}$ |
| 96 kHz mono, seed 325, 24,000 samples | $M=12000,H=6000,K=3,N=16384$, rectangular, no detrending, one 1/24-octave frame | 240 | $6.728\times10^{-14}$ |

The noise trials used seeds 173, 359, 887 and 1601. Each 48 kHz record has
262,144 samples. Generate white Gaussian data with $\sigma=0.1$. Derive
the pink plane by taking its whole-record real FFT, setting DC to zero,
dividing positive-frequency coefficients by $\sqrt{f}$ and taking the inverse.
Use 32 nonoverlapping 8192-sample periodic Hann segments, no detrending,
octaves with centers from 200 to 5000 Hz, and one result per channel. The
white expectation is $2\sigma^2(f_u-f_l)/f_s$. The pink expectation is
$2\sigma^2\ln(f_u/f_l)/f_s$. Adjacent octaves ideally differ by 3 dB for
this white density and 0 dB for this pink density.

The largest absolute departures from those expectations across seeds and
bands were 0.246267 dB for white and 0.199384 dB for pink. A 0.75 dB
sanity bound has margin for finite records in this setup. The lowest included
octave spans roughly 30 FFT cells before overlap effects from the window,
and each average uses 32 disjoint segments. This comparison is statistical.
It supplies no universal confidence interval or guarantee for a single
short input.
