---
schema: 1
id: 2026-11-20-audio-harmonic-analysis-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-20
updated: 2026-11-20
sources: "Abe and Smith (AES 6256), Salamon and Gómez (2012), Essentia HarmonicPeaks, and isolated/two-tone and harmonic-order checks. Audio curriculum PR #2 at 4dc854e450bac96ec985c7ab226941cc8efe13c9. VeNerVRA audio engineering research brief, revised 2026-11-20."
---

# Harmonic analysis research

## Summary

Planned skill #26 · `audio-harmonic-analysis`

**Task outcome:** COMPLETE

Assess which peaks support a supplied harmonic series. Decide what separation, leakage, and
time support the application requires before selecting an analysis window and testing peak
interpolation. Treat an inferred fundamental as a separate estimation task.

## Evidence

**Separate three engineering tasks.** Locating a spectral peak, assigning it to a known
harmonic series, and inferring a fundamental use different evidence. Start with assignment
from a supplied $f_0$. Use observation length and window choice to meet separation,
leakage, and time-support requirements. Use FFT length to set the sampling grid for the
spectrum. Check the intended frequency error for isolated peaks and the minimum separable
spacing with different fixtures. Choose the hop from the required update interval.
[Abe and Smith, AES 6256](https://aes.org/publications/elibrary/elibrary-page/?id=12913) ·
[Smith, sinusoidal peak interpolation](https://www.dsprelated.com/freebooks/sasp/Sinusoidal_Peak_Interpolation.html)
· [Kestrel FFT](../../../../../skills/audio-fft-spectrum/SKILL.md)

1. **Measure peaks.** From three positive magnitudes around an isolated interior maximum,
   take their logs $l,c,r$. The quadratic offset is $\delta=(l-r)/(2(l-2c+r))$ bins and the
   estimated frequency is $(k+\delta)f_s/N$. Require negative curvature, finite inputs, and
   $|\delta|\le0.5$. Give ties, endpoints, and unresolvable peaks explicit handling. Report
   nearest-bin and interpolated estimates under distinct names. Any coherent-gain amplitude
   estimate for an off-bin peak is approximate. Carry window length $M$, FFT length $N$,
   hop, source support and amplitude convention with the result.
2. **Assign harmonics.** For $f_0>0$ and supported targets $hf_0$, use a declared gate such
   as $|f_\text{peak}-hf_0|\le\alpha f_0$, $0<\alpha<0.5$. These gates do not overlap.
   Within a gate prefer the smallest absolute residual, then larger amplitude, then lower
   frequency. Preserve order, estimated peak frequency, target, and signed residual in Hz.
   If useful, also report $1200\log_2(f_\text{peak}/hf_0)$ in cents. Label missing and
   out-of-band orders explicitly. Keep a supplied $f_0$ distinct from a measured first
   harmonic.
   [Essentia HarmonicPeaks](https://essentia.upf.edu/reference/std_HarmonicPeaks.html)
3. **Interpret fit quality.** Report matched coverage with any aggregate. One possible
   weighted deviation is $\sum A_h^2|f_h-hf_0|/(f_0\sum A_h^2)$ over matched peaks in one
   amplitude convention. A small deviation on one match gives little evidence about the rest
   of the series. An unassigned peak could be another source, leakage, or noise. A
   noise-power or THD+N claim requires its own measurement.
   [Essentia Inharmonicity](https://essentia.upf.edu/reference/streaming_Inharmonicity.html)

**Diagnose an apparent resolution failure.** Increase FFT length at the same window length
and compare the isolated-tone error and two-tone separation. In the recorded check, padding
improved the isolated estimate but the pair spaced 0.35 native bins apart still produced one
peak. If peaks merge, test a longer observation within the latency and stationarity limits.
Compare leakage with an unequal-amplitude pair before choosing a different window. Report
unresolved partials when the required separation cannot be demonstrated.

**Test fundamental ambiguity.** Peaks at 440, 660 and 880 Hz fit orders 2/3/4 at 220 Hz and
4/6/8 at 110 Hz. With only 440 and 880 Hz, 440 Hz also fits. The strongest peak can differ
from the most plausible fundamental. If estimation is added, declare the candidate range and
weighting, score unique matches, keep near ties, and return insufficient evidence when
needed. Any preference for coprime orders is a prior. A salience value is a score. A
calibrated probability needs a calibration experiment. Treat tracking, voicing and tests on
multiple sources as distinct tasks.
[Salamon and Gómez, §III-A](https://mtg.upf.edu/system/files/publications/SalamonGomezMelodyTASLP2012.pdf)
· [Klapuri, ISMIR 2006](https://archives.ismir.net/ismir2006/paper/000125.pdf) ·
[YIN paper](https://www.ee.columbia.edu/~dpwe/e6820/papers/deChevK02-yin.pdf)

For review, sweep isolated on- and off-grid tones over the operating band and phase. Include
close equal and unequal pairs, a missing first harmonic, unrelated peaks, silence, and a
target above the supported band. Set separate acceptance bounds for frequency error,
assignment accuracy and false matches. Use the analytic signal frequencies and the supplied
fundamental as independent references.

### Reproducible checks

| Check | Reproduction method | Recorded result |
| --- | --- | --- |
| Frequency estimate for one tone | At 48 kHz, generate $x[n]=\cos(2\pi fn/f_s+\phi)$, $0\le n<2048$. Set $f=(173+d)f_s/2048$ with $d=-0.49,-0.48,\ldots,0.49$ and $\phi=0,0.7,1.9$ rad. Apply the periodic Hann $w[n]=(1-\cos(2\pi n/2048))/2$. At each tested transform length, find the largest positive magnitude and fit the three-point log parabola. Take the maximum absolute error over 297 trials per length. | For FFT lengths of 1×, 2×, 4× and 8× the original frame, max errors were 0.375163722, 0.038053080, 0.004555196 and 0.000563807 Hz. |
| Two-tone separation and harmonic ambiguity | Keep the same rate and window. Sum zero-phase unit cosines at native bins 173 and $173+d$, with $d=0.35$ and 3 in separate runs. Count strict interior local maxima above half of the maximum at 1× and 8×. Separately assign 440, 660 and 880 Hz against 220 and 110 Hz. | One peak at both lengths for 0.35 bins, two at both lengths for 3 bins. Both fundamentals fit exactly with orders 2/3/4 and 4/6/8. |

The recorded spectral probes used binary64 with NumPy 2.3.5 and SciPy 1.17.0. Use the
specified signals and equations to reproduce the measurements in the target stack. The
results cover the tested windows, lengths, and signals.

The reference contract and acceptance cases are proposed. The recorded checks concern the
listed numerical fixtures.

## Next action

Build the first reference around measured-peak assignment from a supplied fundamental. Ask
the agent to investigate two reported partials in a densely sampled spectrum. Use known
separation and an amplitude sweep to assess resolvability. Use isolated-tone estimates to
bound interpolation error independently.

## Revisit when

The target needs a different resolving bandwidth or error budget, estimates its own
fundamental, or must assign peaks in a mixture of sources.
