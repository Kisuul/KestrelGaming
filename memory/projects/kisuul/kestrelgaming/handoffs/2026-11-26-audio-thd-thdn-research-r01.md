---
schema: 1
id: 2026-11-26-audio-thd-thdn-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-26
updated: 2026-11-26
sources: "Audio branch 3d65d0ddb88fead8d8a067e6abb8877ae5609d7b; Audio Precision THD and THD+N method notes, AES17-2020 catalogue, Kestrel FFT and PSD contracts; executed coherent and off-bin fixtures below."
---

# Skill 45 research for THD and THD+N

## Summary

**Task outcome:** COMPLETE

Measure harmonic products and total residual power as distinct
quantities. State the fundamental estimator, measurement band,
accepted harmonics, and ratio denominator. A clean off-bin tone
can look distorted if the estimator removes only its nearest
FFT bin. Use the coherent fixture for calibration and an off-bin
fixture to test the rejection method.
[Audio Precision measurement conventions](https://www.audioprecision.com/news/more-about-thdn-and-thd)

## Evidence

### Declare the measured ratios

Let $P_1$ be the fitted fundamental mean square, $P_D$ the sum
of admitted harmonic powers above the fundamental, $P_R$ the
remaining in-band mean square after removing the fundamental,
and $P_B$ the total mean square in the declared band. Return the
linear powers with the ratios.

| Quantity | Definition for this handoff |
| --- | --- |
| Fundamental-relative THD | Amplitude ratio $\sqrt{P_D/P_1}$. In dB use $10\log_{10}(P_D/P_1)$. |
| Fundamental-relative THD+N | Amplitude ratio $\sqrt{P_R/P_1}$. The residual includes admitted distortion, noise and nonharmonic spurs. |
| Total-relative THD+N | Amplitude ratio $\sqrt{P_R/P_B}$. State that the reference power is the total in-band signal. |

Audio Precision describes total-relative THD+N and
fundamental-relative THD. If an instrument reports a reciprocal
or uses a different denominator, align the definitions before
comparing values. In an orthogonal decomposition with identical
band weights, $P_B=P_1+P_R$. A real notch, off-bin projection, or
different prefilter may require measuring numerator and denominator
separately. Preserve a valid zero residual and an unavailable
ratio when the reference is absent.
[Audio Precision THD/THD+N](https://www.audioprecision.com/news/more-about-thdn-and-thd) ·
[AES17-2020 catalogue](https://aes.org/publications/standards-store/?id=21)

### Separate extraction from calibration

- Freeze the tap, rate, amplitude, time span, settled stimulus
  frequency, weighting, and band. Report how DC, hum, sidebands
  and a component at Nyquist enter the calculation. Use matching
  units and support when comparing tests at different gain.
- Use a coherent rectangular frame for the first reference,
  with known fundamental bin $k_1$ and harmonics at $h k_1$.
  Use one-sided **power** weights and sum harmonic powers.
  For a PSD sum, include the bin width. If tapering, specify
  the integration region, window normalization and the limits
  of separating neighboring lines.
  [Spectrum calibration](../../../../../skills/audio-fft-spectrum/SKILL.md) ·
  [PSD normalization](../../../../../skills/audio-power-spectral-density/references/PSD_CALIBRATION.md#normalization)
- Consider a known-frequency sine/cosine fit on the actual
  samples for a noncoherent capture. Apply the same fit interval
  to both phases and any permitted DC term. If the frequency is
  estimated, measure sensitivity to frequency error and drift.
  A notch needs enough rejection and a measured response, since
  its skirts also affect nearby residual components.
- Report which harmonic orders fell in band, overlapped another
  product, or exceeded Nyquist. Flag a suspected aliased product
  as ambiguous. Compare a higher-rate capture or a controlled
  band limit for that diagnosis.
  [Harmonic assignment](../../../../../skills/audio-harmonic-analysis/SKILL.md)

### Executed checks and portable fixtures

Use 48 kHz and 4,800 samples. For $0\le n<4800$ the coherent
input is

$$
x[n]=0.05+0.5\sin(2\pi1000n/48000)+0.005\sin(2\pi3000n/48000)
+0.002\cos(2\pi1370n/48000).
$$

Exclude DC and include the positive-frequency band up to
Nyquist. Use harmonics 2–24 and count the unpaired Nyquist
bin only once.

| Probe | Verified result |
| --- | --- |
| Account for the three AC components in the coherent signal. | $P_1=0.125$, $P_D=0.0000125$ and $P_R=0.0000145$ in squared PCM units. The 1,370 Hz spur is in the residual. |
| Report ratios with their references. | THD is −40 dB. Fundamental-relative THD+N is −39.35542 dB. Total-relative THD+N is −39.35592 dB. |
| Analyze a pure 1,002.5 Hz sine at phase 0.37 rad and peak amplitude 0.5, with the same frame. | Removing only bin 100 leaves 43.47493% of the original RMS. A sine/cosine least-squares fit at the known frequency leaves a residual RMS ratio below `2.5e-15`. |
| Check spectral mass and reference behavior. | The coherent one-sided bin powers, including DC for this identity, integrate to the mean square of the time samples. If in-band $P_R=P_1$, the two THD+N conventions give 0 dB and −3.01030 dB respectively. |

The bin accounting and off-bin fit were executed on synthetic
PCM. The large-residual ratio comparison follows directly from
the definitions. Instrument bandwidth, hardware noise floor,
notch response and conformance need their own checks.

## Next action

Implement a bounded coherent reference with tracked harmonic
orders and named denominators. Use a known-frequency fit as a
separate comparator for leakage or clock drift. Freeze expected
results independently and add silence, a nonharmonic spur, a
harmonic beyond Nyquist, and an out-of-band component.

## Revisit when

The stimulus, measurement band, weighting, rejection method,
reference denominator, or accepted harmonic orders change.
