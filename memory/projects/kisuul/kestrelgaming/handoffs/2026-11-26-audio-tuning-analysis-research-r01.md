---
schema: 1
id: 2026-11-26-audio-tuning-analysis-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-26
updated: 2026-11-26
sources: "Audio branch 327ca13df3cef9193599762685f1350ae4df6900; ISO 16:1975 catalogue preview, Muller FMP pitch representation, librosa 0.11.0 pitch_tuning documentation; executed circular-offset and harmonic bias fixtures below."
---

# Skill 40 research for tuning analysis

## Summary

**Task outcome:** COMPLETE

Estimate a common offset from a declared pitch grid. Start with
qualified fundamental or known-note observations. Report the offset,
eligible observations, weights, and how they concentrate on the
tuning circle. The checks show wraparound bias, the effect of counting
consecutive frames as separate evidence, and why untreated harmonics
can shift the estimate.
[Pitch-tracking research](2026-11-26-audio-pitch-tracking-research-r01.md)

## Evidence

### Declare the target and the timebase

For twelve-tone equal temperament with A4 frequency $F_A$, map a
positive frequency $f$ to continuous MIDI pitch
$p=69+12\log_2(f/F_A)$. ISO 16:1975 specifies a 440 Hz standard
musical A. Use the reference requested by the measurement, which
may be different. To measure a particular known note with reference
frequency $f_k$, keep the unwrapped error $1200\log_2(f/f_k)$.
A global tuning estimate for unlabeled notes uses a different
observable and resolves a shift only modulo a semitone.
[ISO 16:1975 preview](https://www.iso.org/standard/3601.html) ·
[Log-frequency pitch representation](https://www.audiolabs-erlangen.de/resources/MIR/FMP/C3/C3S1_SpecLogFreq-Chromagram.html)

Record the tap, rate, timestamp span and applicable clock
verification. If the rate used to convert periods to Hz differs
from the actual capture rate, the indicated frequency is scaled
by their ratio. The cents shift from that ratio is indistinguishable
from a uniform change of tuning in an isolated recording.
Use a known calibration source or timebase evidence when this
distinction affects the result.
[Clock and rate domains](../../../../../skills/audio-timebase-sync/references/TIMEBASE_CONTRACT.md#mapping-rate-domains)

### Estimate an offset on the tuning circle

For each qualified pitch take the cents residue on $[-50,50)$.

$$
r_i=((100 p_i+50)\bmod 100)-50,\qquad
Z=\frac{\sum_i w_i e^{j2\pi r_i/100}}{\sum_i w_i},\qquad
R=\lvert Z\rvert .
$$

Use mathematical modulo and finite nonnegative weights. If the
weight sum or the resultant magnitude is too small, give an
unavailable or ambiguous result, with the reason. Otherwise the
circular mean is the wrapped value of $100\arg Z/(2\pi)$.
Apply the same endpoint convention after angle conversion. If a
restricted prior range is required, check whether a representative
of this offset lies in the declared range. Return $R$ as a
concentration measure. An uncertainty interval requires an
observation model or resampling over suitable independent units.

A circular histogram or kernel mode can show multiple candidate
offsets. Count both sides of the seam as neighbors, state the bin
width, and retain near ties. Keep this distribution alongside a
circular mean when a single offset may be insufficient. librosa
0.11.0 exposes a histogram-based comparator whose output is in
fractions of a bin. For $B$ equally spaced bins per octave, each
bin represents $1200/B$ cents.
[librosa 0.11.0 pitch tuning](https://librosa.org/doc/0.11.0/generated/librosa.pitch_tuning.html) ·
[Comparator source](https://librosa.org/doc/0.11.0/_modules/librosa/core/pitch.html#pitch_tuning)

### Choose evidence and weights

- Prefer one stable estimate per note or capped per-note
  contributions if the measurement should weight notes equally.
  Weighting all frames by duration is a separate question. Report
  the number of notes or sources as well as the number of frames.
- Examine the effect of vibrato, bends and unstable note attacks.
  Keep the pitch range, observation span and exclusion rules.
  Compare short and long windows when the source may drift.
- If using spectral peaks, qualify their level, prominence and
  resolution. Group likely partials by source. Equal temperament
  does not place every harmonic on an exact semitone. The third
  and fifth partials can bias a histogram pooled over raw peaks.
  Check the offset obtained from fundamentals against the one
  from the selected partial evidence.
  [Harmonic assignment](../../../../../skills/audio-harmonic-analysis/references/HARMONIC_ANALYSIS_CONTRACT.md#harmonic-assignment)
- Separate groups or report a mixed result when sources have
  different tuning. A single wrapped offset can also hide an
  octave or semitone error in the upstream tracker. Check labeled
  notes when absolute pitch accuracy matters.

### Executed checks and portable fixtures

| Probe | Verified result |
| --- | --- |
| Generate MIDI pitches 60, 64, 69 and 72 with $f=442\cdot 2^{(p-69)/12}$. Estimate with a 440 Hz reference and equal weights. | All residues give a common offset of about +7.851415 cents. The resultant has magnitude 1 to floating-point accuracy. |
| Use equal residues +49 and −49 cents, then +25 and −25 cents. | The first pair has a circular mean of −50 cents in the chosen interval, with $R\approx0.998027$. The second has a zero ideal resultant and no supported mean. |
| Give two notes one frame each at 0 cents. Give a third note 100 frames at +20 cents. | Equal frame weights give +19.69916 cents. Equal note weights give +6.21838 cents. The count of different notes is three in both cases. |
| Use harmonics 2, 3 and 5 of an exactly tuned note and compare each peak to the nearest equal-tempered grid point. | The relative residues are approximately 0, +1.9550 and −13.6863 cents even though the fundamental is on the grid. |

These checks use direct log-frequency mapping and complex sums.
The wrap and partial results also follow analytically from the
formula. Pitch tracking quality, a multi-source recording and
the choice of concentration floor need separate evaluation.

## Next action

Implement a bounded circular-offset estimator over labeled pitch
observations. Return the input reference, the wrapped estimate,
eligible weight and note count, dispersion or competing modes, and
explicit unsupported states. Test seam behavior and scale/reference
changes before accepting a tuning correction into chroma.

## Revisit when

The pitch grid, clock calibration, source grouping, weight policy,
or interpretation of concentration changes.
