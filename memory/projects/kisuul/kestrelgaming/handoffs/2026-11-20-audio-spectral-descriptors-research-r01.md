---
schema: 1
id: 2026-11-20-audio-spectral-descriptors-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-20
updated: 2026-11-20
sources: "Peeters et al. (2011), Kestrel PSD and fractional-octave RTA contracts, and discrete/continuous bin-power and binary64 checks. Audio curriculum PR #2 at 4dc854e450bac96ec985c7ab226941cc8efe13c9. VeNerVRA audio engineering research brief, revised 2026-11-20."
---

# Spectral descriptors research

## Summary

Skill #25 · `audio-spectral-descriptors`

**Task outcome:** COMPLETE

Measure where frame power lies and how the distribution changes across comparable
observations. Start with discrete bin weighting on one original, calibrated, one-sided PSD
frame. Specify units and frequency support before computing any statistic.

## Evidence

**Choose what the frequency weights mean.** If an analyzer must describe where signal power
lies, trace the output to one original, calibrated, one-sided power spectral density (PSD)
frame. Confirm the signal tap, channel, time support, window, sample rate and grid.
Magnitude, squared magnitude, PSD and decibel values produce different results as weights. A
stitched multiresolution display can take values from several observation windows. Select
one original profile to measure a frame descriptor.
[Kestrel PSD](../../../../../skills/audio-power-spectral-density/SKILL.md) ·
[Multiresolution skill](../../../../../skills/audio-multiresolution-spectrum/SKILL.md)

**First reference.** On a uniform DFT grid, assign bin power $q_k=S_{xx}[k]\Delta f$ to the
bin center $f_k$, where $\Delta f=f_s/N$. The Kestrel PSD already incorporates the
paired-bin power factor. Preserve the full $S_{xx}[k]\Delta f$ mass at the endpoints. An
even-length transform has an unpaired Nyquist bin. An odd-length transform's highest
positive bin still has a negative-frequency partner. Use a full grid or a declared half-open
bin-center selection. Declare terminal Nyquist inclusion. Exclude DC by default with an
explicit opt-in. Use the RTA cell-overlap model when an application needs fractional-band
coverage and can state that model.
[Kestrel RTA integration](../../../../../skills/audio-fractional-octave-rta/references/FRACTIONAL_OCTAVE_RTA_CONTRACT.md#psd-integration-and-coverage)

| Output | Proposed definition | Edge behavior |
| --- | --- | --- |
| Total selected power | $Q=\sum_k q_k$, in squared input units | A valid silent selection gives zero. An empty selection has its own status. |
| Centroid and RMS spread | $\mu=\sum_k p_k f_k$, $\sigma=\sqrt{\sum_k p_k(f_k-\mu)^2}$, with $p_k=q_k/Q$ | Both in Hz. A single occupied bin gives spread zero. Accumulate around the computed mean. |
| Rolloff | First selected center $f_k$ with $\sum_{j\le k}q_j\ge rQ$, $0<r<1$ | Equality satisfies the crossing. Include examples at 0.85 and 0.95. |
| Flatness and crest | Geometric mean divided by arithmetic mean of linear PSD. Crest is maximum divided by the same arithmetic mean. | Any zero ordinate in a positive-power selection gives flatness zero. Both ratios are dimensionless. |
| Entropy | $-\sum_{p_k>0}p_k\ln p_k$, optionally divided by $\ln K$, where $K$ counts all selected bins | For $K=1$, raw entropy is zero and normalized entropy is unavailable. Grid and selection affect the value. |
| Power flux and shape flux | $\lVert q_t-q_{t-1}\rVert_2$ in power units and $\lVert p_t-p_{t-1}\rVert_2$ dimensionless | First frame unavailable. Power flux can compare valid silence and signal. Shape flux needs positive power in both frames. |

Return unavailable shape descriptors when $Q=0$. Reject negative and nonfinite PSD before
changing state. For scale-free statistics, scale ordinates by the maximum positive ordinate
before summing and evaluate the geometric mean in the log domain. Declare the supported
numerical range and report positive values that underflow separately from exact zeros. For
flux, match the epoch, channel, tap, calibration, sample rate, window, FFT, detrending, hop,
profile and bin selection. Require the next expected sample index. A rejected frame
preserves the last valid comparison frame. A reset clears it.

**Diagnose before tuning.** If a uniform gain changes centroid or normalized entropy for an
unchanged, representable spectrum, inspect weighting, flooring and normalization. If
integrated power is wrong only at DC or Nyquist, check one-sided folding and grid width
against time-domain power. If flux spikes after a seek or configuration change, compare
frame provenance and sample support first.

| Fixture | Expected result |
| --- | --- |
| Centers 100 and 200 Hz, powers 1 and 3 | Centroid 175 Hz and spread $25\sqrt{3}$ Hz. A 25% rolloff is 100 Hz. At 85% and 95% it is 200 Hz. |
| Positive flat PSD over three bins | Flatness 1, crest 1, normalized entropy 1. |
| Powers [1, 0, 0] on a common grid | Spread 0, flatness 0, crest 3, normalized entropy 0. |
| Successive powers [1, 3] and [2, 6] | Power flux $\sqrt{10}$ and shape flux 0. |
| DC and even-length Nyquist, then an odd DFT | Compare total bin power to the prepared time-domain mean square, with the same window normalization. Check the endpoint factors with a direct DFT. |
| Invalid final ordinate, discontinuity, or reset | Verify atomic rejection and the first frame of a new epoch. Use sample indices above $2^{53}$. |

**When the application needs continuous cells.** For a constant-density overlap $[a,b]$,
the conditional mean is $m=a+(b-a)/2$ and the variance is $(b-a)^2/12$. For normalized cell
masses $p_k$, the total variance is $\sum_k p_k[(m_k-\mu)^2+(b_k-a_k)^2/12]$. Use this
centered form to retain precision for narrow cells far from zero. Single-cell spread is
28.867513459 Hz for a uniform density over [100, 200] Hz, and its 85% quantile is 185 Hz.
The discrete point at 150 Hz gives zero spread and 150 Hz rolloff. For a Nyquist bin with 8
units of power distributed over its 100 Hz physical cell, a 50 Hz overlap receives 4. Using
the original 200 Hz grid width as the physical support would assign 2.

### Comparison sources

Published descriptors use a range of representations. Peeters et al. compare several in the
Timbre Toolbox. For a differential check, match the comparison implementation's weights,
centers, rolloff fraction, flatness floor, and flux norm before drawing conclusions from a
difference. The MPEG-7 catalog provides standards scope and edition.
[Peeters et al., §III](https://www.mcgill.ca/mpcl/files/mpcl/peeters_2011_jasa.pdf) ·
[librosa spectral conventions](https://librosa.org/doc/0.11.0/_modules/librosa/feature/spectral.html)
· [Essentia Flux](https://essentia.upf.edu/reference/streaming_Flux.html) ·
[ISO MPEG-7 Audio catalog](https://www.iso.org/standard/34231.html)

### Reproducible checks

| Check | Reproduction method | Recorded result |
| --- | --- | --- |
| Discrete and continuous weighting | Compare point mass at 150 Hz with uniform density on [100, 200] Hz. Evaluate centroid, spread and 85% rolloff from the definitions above. | Centroid 150 Hz for both. Spread 0 and 28.867513459 Hz. Rolloff 150 and 185 Hz. |
| Endpoint mass and cancellation | Allocate 8 units from a Nyquist half-cell [300, 400] Hz into a 50 Hz overlap. For a separate cell $[a,b]=[16000,16000+10^{-6}]$ Hz, compare $(a^2+ab+b^2)/3-((a+b)/2)^2$ with $(b-a)^2/12$ in binary64. | Overlap power 4. Raw-moment subtraction gave $2.98023223877\times10^{-8}$ Hz². The centered result was $8.3333389756\times10^{-14}$ Hz². |

The reference contract and acceptance cases are proposed. The recorded checks concern the
listed numerical fixtures.

## Next action

Freeze the discrete input and output contract and the analytic test vectors. Give an agent a
visualizer whose centroid changes after a uniform gain change. Require the agent to trace
the tap and weights, then use the gain test and a known two-bin spectrum to distinguish
weighting, flooring and grid changes. When reusing power or shape flux in an onset detector,
specify baseline, peak picking and event timing independently.

## Revisit when

The descriptor weighting or band-inclusion contract changes, a target requires
fractional-band support, or a compatibility or precision test fails.
