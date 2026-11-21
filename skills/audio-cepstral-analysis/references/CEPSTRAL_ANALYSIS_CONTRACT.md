# Real cepstral analysis measurement contract

## Input frame

Take one original frame of a real signal from one channel. Record source,
clock, epoch, channel, amplitude unit, window, detrending, rate $f_s$,
observed length $M$, FFT length $N$, and hop. Use the half-open sample
interval $[s,s+M)$ and doubled center $2s+M-1$. Keep those coordinates as
integers. [FFT calibration](../../audio-fft-spectrum/references/FFT_CALIBRATION.md) ·
[Timebase](../../audio-timebase-sync/SKILL.md)

Supply the unnormalized DFT magnitudes for bins zero through
$\lfloor N/2\rfloor$. Preserve the original $N$ with the packed array.
If the producer supplies Kestrel peak amplitudes $A[k]$, recover
$|X[k]|=A[k]\sum_n w[n]/d_k$, where $d_k$ is 1 at DC and even Nyquist and
2 at paired bins. Use the sum of the observed window coefficients.
Taking logs of the doubled bins adds a frequency-dependent offset and
can create a false cepstral component.

## Real cepstrum

Choose a positive magnitude reference $A_\mathrm{ref}$ in the frame's
units. Start from $L[k]=\ln(|X[k]|/A_\mathrm{ref})$ where the magnitude is
positive or has been floored. Form the length-$N$, real, even log spectrum.
For every paired bin $k$, set $L[N-k]=L[k]$. DC is a singleton. At even length,
Nyquist is also a singleton. At odd length, the final stored bin is paired.
[Real cepstrum convention](https://www.fceia.unr.edu.ar/prodivoz/Oppenheim_Schafer_2004.pdf) ·
[Packed inverse parity](https://numpy.org/doc/2.3/reference/generated/numpy.fft.irfft.html)

For each reported index $q$ from zero through $\lfloor N/2\rfloor$, use:

$$
c[q]=\frac{1}{N}\left(L[0]+
2\sum_{k=1}^{\lfloor (N-1)/2\rfloor} L[k]\cos(2\pi kq/N)+
\mathbf{1}_{N\ \mathrm{even}}L[N/2](-1)^q\right).
$$

The coefficients are signed log ratios. Return quefrency as the integer
index and the time $q/f_s$. The index describes a circular lag. For a
periodicity task, select a positive range supported by the actual
observation length and the signal model. The FFT length alone gives the
circular grid. An echo and a periodic source may support the same
quefrency. Use another observation or signal evidence to distinguish them.

## Nulls and flooring

With strict evaluation, return `spectral_null` if a non-silent frame
contains any exact zero magnitude. With relative flooring, choose
$0<\epsilon<1$ and replace every stored magnitude strictly below
$\epsilon\max_k|X[k]|$. Match floor equality against the exact represented
product. Count replacements once per packed bin. Return the factor,
indices, count, and normalized log floor. Return `silent` for an all-zero
frame under either policy. Both unavailable states leave the coefficients
absent.

Evaluate wide ratios as differences of logarithms. Use relative
differences with `log1p` for close positive values. In the reference,
compute the varying log spectrum relative to the frame peak. Add the
common log offset to $c[0]$ after the inverse. This keeps small spectral
shape coefficients visible with large reference offsets. A common gain
that leaves the represented shape and floor pattern the same shifts only
the zero coefficient by the log of that gain.

## Spectral envelope

Choose an integer cutoff $Q$ from zero through $\lfloor N/2\rfloor$.
Retain coefficients with $\min(q,N-q)\le Q$ in the circular array.
Keep the even midpoint once if included. The forward transform of the
retained, even real sequence gives the normalized log magnitude envelope.
For an FFT implementation, check that the imaginary residual is within
roundoff. The cosine reference applies the paired terms directly.
[Cepstral windowing](https://www.dsprelated.com/freebooks/sasp/Cepstral_Windowing.html) ·
[Envelope synthesis](https://www.dsprelated.com/freebooks/sasp/Spectral_Envelope_Cepstral_Windowing.html)

$Q=0$ gives a constant envelope. The full cutoff recovers the floor-processed
input. The reference uses that identity to preserve the original linear
ordinates at the representable endpoints. For other cutoffs, exponentiate
the absolute log magnitude. Derive it from the frame peak and the
reconstructed log ratio. Return packed log magnitudes relative to
$A_\mathrm{ref}$ and the available linear magnitudes in the original
convention. A positive reconstruction that rounds to zero or overflows
gets an unavailable linear bin with its reason. The log envelope remains
available. A silent frame or an unavailable cepstrum carries its status
forward without envelope arrays.

## Reference and verification

[The offline reference](../scripts/reference_cepstral_analysis.py) supplies
`real_cepstrum(frame, magnitude_reference=..., relative_floor=...)` and
`spectral_envelope(result, cutoff=...)`. Omit the relative factor to use
strict mode. In a successful cepstrum result, `coefficients[q]` aligns
with `quefrency_seconds[q]`. Envelope results with any unavailable
linear bin have status `partial`. Their `underflow_bins` and
`overflow_bins` name the packed frequencies involved.

The reference uses the Python standard library and a bounded direct
cosine sum. Its input uses integer sample rates from 2 through 384,000 Hz
and $2\le M\le N\le1024$. The hop is an integer from 1 through 1024 samples.
Start and end-exclusive indices fit in $[0,2^{256}-1]$. The packed magnitudes
form a tuple of finite nonnegative built-in floats or integers that fit in
binary64. Invalid frame data, policy values, and cutoffs raise
`ValueError`. Use an FFT backend for larger transforms and compare it
against the same parity, scaling, and floor fixtures.

Use the [frozen cases](../../../tests/fixtures/AUDIO_CEPSTRAL_ANALYSIS_GOLDENS.md)
to verify a backend. Compare signed coefficients and the log envelope.
Check the floor count separately. Interpret outputs within the stated
signal, window, padding, and numerical conditions.
