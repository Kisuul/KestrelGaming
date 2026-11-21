---
schema: 1
id: 2026-11-20-audio-cepstral-analysis-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-20
updated: 2026-11-20
sources: "Oppenheim and Schafer (2004), Smith's Spectral Audio Signal Processing, and a signed two-impulse echo check at odd and even FFT lengths. Audio curriculum PR #2 at 4dc854e450bac96ec985c7ab226941cc8efe13c9. VeNerVRA audio engineering research brief, revised 2026-11-20."
---

# Cepstral analysis research

## Summary

Planned skill #27 · `audio-cepstral-analysis`

**Task outcome:** COMPLETE

Use a real cepstrum for periodic structure or for a smoothed magnitude envelope. Declare the
transform, floor policy and valid quefrency range. Preserve the original FFT length through
packing and inversion.

## Evidence

**Choose the inference before the transform.** The real cepstrum can reveal periodic
structure in a log-magnitude spectrum or produce a smoothed spectral envelope. Define the
expected lag or period range, the observation length that supports it, and whether an echo
or competing periodic source could produce the same peak. State the transform convention
explicitly, since the literature uses several forms of cepstrum.
[Oppenheim and Schafer, IEEE SPM 2004](https://www.fceia.unr.edu.ar/prodivoz/Oppenheim_Schafer_2004.pdf)
· [Noll, JASA 1967](https://pubmed.ncbi.nlm.nih.gov/6040805/) ·
[Smith, cepstral windowing](https://www.dsprelated.com/freebooks/sasp/Cepstral_Windowing.html)

**First reference.** Prepare $M$ real samples with a declared window and detrending policy.
Let $X[k]$ be their unnormalized length-$N$ DFT, $N\ge M$. With fixed positive magnitude
reference $A_\mathrm{ref}$, form the real, even log spectrum
$L[k]=\ln(|X[k]|/A_\mathrm{ref})$. Take the length-$N$ inverse DFT with factor $1/N$. An
explicit real-valued form is

$$
c[q]=\frac{1}{N}\sum_{k=0}^{N-1}L[k]\cos(2\pi kq/N),\qquad 0\le q<N.
$$

With a packed half-spectrum, mirror the paired log-magnitude bins. Keep DC and the
even-length Nyquist bin once each. Preserve $N$ and its parity through the inverse. The
one-sided factors used for calibrated amplitude and PSD would change selected log bins.
Record quefrency as integer samples $q$ and seconds $q/f_s$ on a separate axis from the
frame timestamp. Search positive quefrencies within the intersection of the task's supported
period range and $1\le q\le\lfloor N/2\rfloor$. Consider how much of the original frame
supports the longest candidate when padding is used.
[Kestrel FFT](../../../../../skills/audio-fft-spectrum/SKILL.md)

- **Handle nulls deliberately.** Strict evaluation has a defined unavailable state when any
  magnitude is zero. If using a relative floor $\epsilon\max_k|X[k]|$, state its scale and
  count the affected bins. Compute logs in a way that avoids overflow or underflow in
  intermediate ratios. Give all-zero input its own status. Under a common gain and the same
  floor pattern, only $c[0]$ changes. This is a useful test of calibration and endpoint
  handling.
- **Control envelope smoothing.** Keep the chosen low signed quefrencies symmetrically at
  both ends of the circular array. To recover an amplitude envelope, take the real part of
  the forward DFT of the liftered coefficients, exponentiate, and multiply by
  $A_\mathrm{ref}$. Keeping only $c[0]$ produces a constant. Use a known envelope and known
  ripple period to check how the cutoff trades envelope detail against residual ripple.
  [Smith, spectral envelope by cepstral windowing](https://www.dsprelated.com/freebooks/sasp/Spectral_Envelope_Cepstral_Windowing.html)
- **Report candidates with limits.** For a peak at $q>0$, $f_s/q$ expresses a candidate
  repetition frequency. The same $q$ can describe an echo delay. Use the signal model and
  corroborating evidence to interpret it. Phase reconstruction, complex cepstrum, MFCCs and
  pitch tracking have different output contracts.

**Diagnose a disagreement across implementations.** Verify length and parity, inverse
normalization, folded bins, and floor policy before comparing peak positions. Use an impulse
for a flat log spectrum, gain and circular-shift checks on the prepared frame, and a
two-impulse echo for signed nonzero coefficients. For $x[n]=\delta[n]+a\delta[n-D]$,
$0<a<1$, the real cepstrum has terms $(-1)^{m+1}a^m/(2m)$ at $\pm mD$ before the DFT
periodizes them. Compare a small direct inverse DFT or that series to the optimized
implementation. Check an odd and even length, a spectrum with analytic nulls, and a
symmetric lifter. An FFT can return tiny residual magnitudes at analytic nulls. Use an exact
synthetic null to check the strict failure path, then check the floor policy with the FFT
output.

### Reproducible checks

| Check | Reproduction method | Recorded result |
| --- | --- | --- |
| Echo cepstrum | Prepare impulses 1 at index 0 and 0.4 at index 7. Use $A_\mathrm{ref}=1$, no further window or detrend, and lengths 255 and 256. Compare the packed-input inverse to the full-spectrum inverse. Multiply the prepared frame by 3, then separately rotate it circularly by 11 samples. Keep only $c[0]$ in a separate lifter check. | At quefrencies 7, 14, 21 both lengths gave 0.200000000000, −0.040000000000 and 0.010666666667 within $2\times10^{-14}$ of the leading series terms. Inverses agreed to $2\times10^{-15}$. Gain changed only $c[0]$ by $\ln 3$, rotation preserved the cepstrum, and the one-coefficient envelope was flat at 1 within $2\times10^{-15}$. |
| Spectral nulls and FFT parity | Use two unit impulses at 0 and 8 with length 256. Their spectral sum is zero at multiples $16(2m+1)$ below 256. Compare an explicitly length-255 real inverse with a backend that infers an even length from the packed bin count. | Four nonnegative-frequency zeros at 16, 48, 80 and 112, and eight zeros on the full grid. The tested default inverse inferred length 254 from the odd transform's stored bins. Specify parity at the adapter boundary. [Example inverse transform convention](https://numpy.org/doc/1.24/reference/generated/numpy.fft.irfft.html) |

The recorded spectral probes used binary64 with NumPy 2.3.5 and SciPy 1.17.0. Use the
specified signals and equations to reproduce the measurements in the target stack. The
results cover the tested windows, lengths, and signals.

The reference contract and acceptance cases are proposed. The recorded checks concern the
listed numerical fixtures.

## Next action

Freeze the real-cepstrum convention and analytic echo, gain, parity and null fixtures. Ask
the agent to explain a discrepancy on an odd-length frame across two backends. Check
original length, packed-bin symmetry, scaling and flooring before comparing peak locations.

## Revisit when

A new transform backend, floor policy, period range or lifter changes a supported
measurement, or the task requires phase recovery or a pitch tracker.
