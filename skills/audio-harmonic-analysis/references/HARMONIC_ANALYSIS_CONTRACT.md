# Harmonic analysis measurement contract

## Input frame

Take a complete, original real-input FFT frame from one channel. Supply the
linear one-sided peak-amplitude bins in their declared unit and reference.
Record the tap, clock, epoch, window identity, detrending, sample rate $f_s$,
window length $M$, FFT length $N$, and hop. Use the half-open sample interval
$[s,s+M)$ and the doubled center $2s+M-1$. Preserve those coordinates as
integers. [FFT calibration](../../audio-fft-spectrum/references/FFT_CALIBRATION.md) ·
[Timebase](../../audio-timebase-sync/SKILL.md)

The one-sided grid has bins $0$ through $\lfloor N/2\rfloor$. Bin $k$ is at
$k f_s/N$. The FFT producer owns coherent gain. Its amplitude scale is
$1/\sum_n w[n]$ at DC and even-length Nyquist, and $2/\sum_n w[n]$ at
paired bins. The divisor uses the observed window coefficients. The measured
bin amplitude for an off-bin tone depends on the window and its grid position.

## Peak search

Provide a half-open search band $[f_\mathrm{lo},f_\mathrm{hi})$ within the
frame's one-sided range. Provide a nonnegative amplitude floor in the same
unit as the frame. A positive local maximum at the floor is eligible.
Compare a candidate with its neighbors in the original frame. Keep a
flat-topped run with lower outside neighbors as an unresolved plateau if it
contains a positive bin center in the band. Preserve its inclusive bin
interval. DC never supplies an individual candidate. The half-open band
excludes the even-length Nyquist endpoint. The last odd-length bin may supply
a coarse candidate.

For a strict maximum at index $k$, use a three-point fit when both flanks are
positive and the three bins are paired. With center amplitude $A_k$, define

$$
u=\ln(A_{k-1}/A_k),\qquad
v=\ln(A_{k+1}/A_k),\qquad
\delta=\frac{u-v}{2(u+v)},\qquad
\hat f=(k+\delta)f_s/N.
$$

Require negative curvature, finite values, and $|\delta|\le 1/2$.
Use relative differences with `log1p` near equal amplitudes. Use the
difference of logarithms for a wide ratio. This avoids the loss of curvature
from separately rounded logs near equality and avoids a rounded zero for a
very small positive ratio. Log-parabolic fitting models the local lobe. Check
its error for the actual window, frequency range, and source.
[Quadratic interpolation](https://www.dsprelated.com/freebooks/sasp/Quadratic_Interpolation_Spectral_Peaks.html) ·
[Interpolation bias](https://www.dsprelated.com/freebooks/sasp/Bias_Parabolic_Peak_Interpolation.html)

The reference retains the bin index, bin center, and measured bin amplitude.
It supplies an interpolated frequency with `refined` status. A candidate
with a missing flank, unpaired flank, zero flank, or invalid fit keeps its
bin center and a reason. Apply band membership to the selected frequency.
Positive neighboring bins with the correct factors make the arithmetic
eligible. Establish physical peak isolation with a controlled signal.

## Harmonic assignment

Supply a positive fundamental $f_0$, positive integer orders, and a rational
tolerance $0<\alpha<1/2$. For each order $h$, compute the target $h f_0$
and use the closed frequency gate

$$
[h f_0-\alpha f_0,\ h f_0+\alpha f_0].
$$

The gates are disjoint. A peak can match at most one order. Use a candidate
whose selected frequency is inside both the search band and the gate.
Treat input binary64 frequencies as their exact represented values for this
comparison. Compare the exact gate distance before rounding the displayed
target or residual. Express a decimal tolerance such as 0.05 as $1/20$.
[Fundamental-relative tolerance](https://essentia.upf.edu/reference/std_HarmonicPeaks.html)

Select the smallest absolute residual. Break ties by larger measured bin
amplitude, then lower frequency, then lower bin index. Report the selected
peak and its refinement status. Give the signed residual
$f_\mathrm{peak}-h f_0$ in hertz. Return unused candidates by bin index.

| Status | Condition |
| --- | --- |
| `matched` | An eligible candidate occupied the order's gate. |
| `missing` | The whole gate lies in the search band and no candidate matched. |
| `partial_band` | Part of the gate lies outside the band and no candidate matched. |
| `out_of_band` | The target itself lies outside the band. |

The `full_gate` flag describes coverage by the declared band, including
for matched orders. A gate with its upper edge equal to the exclusive
band end has partial coverage. Count all in-band targets as eligible.
Report the number with full gates and the number matched. Those counts
describe the assignment. Verify resolvability independently. Report the
supplied fundamental even when its first order is missing.

## Reference and verification

[The offline reference](../scripts/reference_harmonic_analysis.py) supplies
`find_peaks(frame, band, min_amplitude=...)` and
`assign_harmonics(peaks, band, fundamental_hz=..., orders=..., tolerance=...)`.
Pass the measured result's peaks and band into assignment. Retain the peak
search result as the frame provenance for the assignment. The assignment
function can also take measured candidates from one upstream frame. Use one
amplitude convention and a unique bin index for each candidate. Supply the
original band and preserve the same source metadata with those inputs.

Use integer rates from 2 through 384,000 Hz, $2\le M\le N\le32768$, and integer
hops from 1 through 32,768 samples. Start and end-exclusive indices must fit
in $[0,2^{256}-1]$. The full spectrum has $\lfloor N/2\rfloor+1$ entries, each a built-in
finite nonnegative float or integer that fits in binary64. The reference
checks all entries, even outside the search band. Orders are distinct
integers from 1 through 32,768. The supplied fundamental is at most
192,000 Hz. The tolerance is a `Fraction`. Invalid input raises
`ValueError`.

Use known source frequencies for the acceptance check. An isolated tone can
benefit from more FFT points at fixed $M$. To test resolution, use two tones
with known separation, relative amplitudes, and phase. Test the actual
observation length and window when the application needs to resolve both
partials. Check phase and floor effects before using any fixture to support a
general resolution limit.
[Abe and Smith, AES 6256](https://aes.org/publications/elibrary/elibrary-page/?id=12913) ·
[Frozen cases](../../../tests/fixtures/AUDIO_HARMONIC_ANALYSIS_GOLDENS.md)

The reference is deterministic, offline, and uses the Python standard
library. Scope the evidence to the window, input domain, and tests that ran.
Fundamental estimation, tracking, tone amplitude inference, noise power,
and THD+N require their own methods and acceptance checks.
