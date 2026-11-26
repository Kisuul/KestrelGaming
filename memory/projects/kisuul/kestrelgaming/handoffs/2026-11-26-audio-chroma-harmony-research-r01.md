---
schema: 1
id: 2026-11-26-audio-chroma-harmony-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-26
updated: 2026-11-26
sources: "Audio branch 327ca13df3cef9193599762685f1350ae4df6900; Muller FMP log-frequency and template chord chapters, Ellis and Poliner (2007), mir_eval chord documentation; executed cyclic fold and triad ambiguity fixtures below."
---

# Skill 41 research for chroma and harmony

## Summary

**Task outcome:** COMPLETE

Treat chroma as measured support for pitch classes on a declared
tuning grid. A first reference can fold calibrated weights into
twelve bins and compare the result against major and minor triads.
Return the raw chroma and competing template scores. Unknown tuning,
unresolved bass and competing chords can require different remedies.
The checks cover cyclic interpolation, octave pooling, and chord
ties from two notes or four.
[Tuning research](2026-11-26-audio-tuning-analysis-research-r01.md)

## Evidence

### Calibrate spectral evidence before folding

Declare the input tap, exact frame support, tuning reference and
frequency range. Choose an ordinate appropriate for the task. For
the baseline, use nonnegative, per-bin or per-peak power masses in
declared units. When starting from Kestrel's one-sided PSD, multiply
each retained full-bin density by its bin spacing in Hz to obtain
power mass. Use the PSD's one-sided weighting as given. A magnitude
or log-compressed profile defines a different weight, so state
whether values are comparable across profiles. Skip DC for pitch
mapping and report excluded frequency and level support.
[Kestrel PSD normalization](../../../../../skills/audio-power-spectral-density/references/PSD_CALIBRATION.md#normalization) ·
[Log-frequency features](https://www.audiolabs-erlangen.de/resources/MIR/FMP/C3/C3S1_SpecLogFreq-Chromagram.html)

Map each positive frequency to $p=69+12\log_2(f/F_A)$. In the
simple linear-pitch interpolation profile, set $m=\lfloor p\rfloor$
and $\eta=p-m$. For weight $a$, add $a(1-\eta)$ to pitch class
$m\bmod 12$ and $a\eta$ to $(m+1)\bmod 12$. C is 0 and B is 11.
Use a nonnegative modulo result. This distributes every admitted
weight once, including across B and C. It approximates each spectral
observation as a point at its nominated frequency. State a
separate integration rule if you model finite bandwidth.

Check actual pitch resolution in the selected band. At 48 kHz a
2,048-sample unpadded transform has 23.4375 Hz bin spacing. E2 to
F2 in the 440 Hz grid spans about 4.90017 Hz. Interpolation and
padding may improve isolated peak locations, but resolving two
nearby components depends on window support and leakage. Test two
simultaneous low notes at different levels. Consider longer
windows or a log-frequency filterbank, with the corresponding
frequency-dependent support and availability.
[Window functions](../../../../../skills/audio-window-functions/SKILL.md) ·
[Harmonic-analysis resolution checks](../../../../../skills/audio-harmonic-analysis/SKILL.md)

Keep the unnormalized sum, occupied bins and quality gates.
Normalize only after passing the support and level rules. An
all-zero chroma has undefined vector direction. A very small
supported chord and a loud chord may have the same normalized
shape, so keep the absolute support with any chord decision.

### Compare hypotheses on the same support

For a major triad at root $r$, place unit entries in
$r+\{0,4,7\}\bmod 12$. Use $r+\{0,3,7\}\bmod 12$ for minor.
For nonzero chroma $c$ and template $v$, a simple baseline
computes their normalized dot product,
$c^\top v/(\lVert c\rVert_2\lVert v\rVert_2)$. Record the score,
margin, and tied or near-tied labels. Use a stated insufficient
evidence policy for weak support or if no allowed label explains
the distribution. Evaluate a musical no-chord label separately
from an unavailable measurement. A frame with one or two pitch
classes may allow several triads. Octave folding also removes the
bass register, so inference about bass and inversion needs the
unfolded evidence. A local triad supplies only part of the
evidence for a key.
[FMP template chord recognition](https://www.audiolabs-erlangen.de/resources/MIR/FMP/C5/C5S2_ChordRec_Templates.html) ·
[mir_eval chord vocabularies](https://mir-eval.readthedocs.io/stable/api/chord.html)

If combining frames over a beat, declare the aggregation domain.
For a time-weighted mean, use disjoint representative frame cells
clipped at the beat edges and retain the underlying window
supports. A missing beat or gap changes the eligible span. An
offline beat-synchronous feature may use a future beat anchor.
Keep the actual availability time for online work. If smoothing
chord labels, report which evidence the decision used and check
short chords near a transition.
[Ellis and Poliner (2007), §§2–4](https://www.ee.columbia.edu/~graham/papers/EllisP07-coversongs.pdf) ·
[Rhythm coordinate research](2026-11-26-audio-rhythm-analysis-research-r01.md)

### Executed checks and portable fixtures

The fold and the template rankings below used exact arithmetic.
For nonnegative vectors, the squared cosine preserves ranking
and avoids a square root in these fixtures.

| Probe | Verified result |
| --- | --- |
| Admit A3, A4 and A5 with weights 2, 1 and 4. | Pitch class A (9) has weight 7. The total admitted mass is 7. |
| Admit a unit point at MIDI pitch 71.75, then transpose it up one semitone. | First B gets 1/4 and C gets 3/4. The transposed vector rotates by one class and retains mass 1. |
| Unit chroma entries at C, E and G. Use the 24 major/minor triad templates above. | C major has the unique top score of 1. |
| Keep C and G only. Then test C, E, G and A with equal weights. | C major and C minor tie at squared score 2/3 in the first case. C major and A minor tie at 3/4 in the second. |

The fixture starts from supplied pitch coordinates or chroma and
checks the folding and template stages. Spectral front-end
resolution, harmonic interference, and chord accuracy on labeled
recordings require different inputs and acceptance checks.

## Next action

Implement the calibrated folding step and the bounded triad
comparison with visible support, tuning, and ambiguity. Test empty
or level-gated frames, inversion with measured bass, strong
partials, and wraparound under a tuning change. For labeled
evaluation, compare common time intervals with a declared
vocabulary and report duration-weighted agreement and coverage.

## Revisit when

The tuning grid, ordinate, filterbank, temporal support, chord
vocabulary, or treatment of bass and ambiguity changes.
