# Chroma and harmony contract

[Power](#power-and-support) · [Tuning](#tuned-pitch-classes) ·
[Chords](#chord-scores-and-decisions) · [Bass](#bass-and-voicing) ·
[Time](#time-and-evaluation) · [Reference](#bounded-reference)

## Power and support

Chroma measures the support assigned to each pitch class.
Record the tap, epoch, sample rate, channel or mix, analysis
window, frequency band, and power units. A bin center, a
resolved peak, and a grouped fundamental have different
support. For this reference, each point contributes a
nonnegative power mass at its stated frequency.

For a complete real one-sided PSD with grid spacing
$\Delta f=f_s/N_{\mathrm{fft}}$, use $a_k=P_1[k]\Delta f$.
The density already pairs interior positive frequencies
with their negative frequencies. DC and even-length Nyquist
have one contribution each. The final bin of an odd transform
is paired. Integrate whole bins using this spacing. The
reference folds the mass at the bin center. A finite-width
band integration needs its own allocation rule.
[PSD normalization](../../audio-power-spectral-density/references/PSD_CALIBRATION.md#normalization)

Exclude DC before mapping frequencies to pitch. Select centers
on the closed frequency band after any clock correction.
Apply the minimum individual power with equality admitted.
Keep the DC and out-of-band masses, in-band mass below the
point floor, and admitted mass. Their sum is the full input
power. Keep a magnitude or log-compressed profile and its
weights separate from linear power.

Test two adjacent low notes with the actual time aperture,
window, and level ratio. A denser FFT grid samples the same
windowed spectrum more finely. Use more observed samples or
a qualified filterbank when resolving the components requires
longer support. Track the associated data boundary. Also
check leakage before calling a peak the lowest supported note.
[Log-frequency representation](https://www.audiolabs-erlangen.de/resources/MIR/FMP/C3/C3S1_SpecLogFreq-Chromagram.html) ·
[Harmonic analysis](../../audio-harmonic-analysis/SKILL.md)

## Tuned pitch classes

Use twelve-tone equal temperament with A4 at $F_A$.
For positive frequency $f$ and a correction $\delta$ in cents,
use

$$
p=69+12\log_2(f/F_A)-\delta/100,\qquad
m=\lfloor p\rfloor,\qquad
\eta=p-m .
$$

Use $0$ for C and $11$ for B. Add $a(1-\eta)$ to $m\bmod 12$
and $a\eta$ to $(m+1)\bmod12$. Both class indices are
nonnegative. The rule covers negative pitch coordinates and
the seam between B and C. The two shares sum to $a$. Moving
one octave preserves the vector. Transposing every point one
semitone rotates it by one class.

Use the original $F_A$ with a cents correction, or declare
the equivalent shifted reference $F_A 2^{\delta/1200}$.
Apply the correction once. Skill #40 estimates a residue
in $[-50,50)$ cents. Select a representative $\delta+100k$
using a known note or a declared prior when absolute pitch
class matters. An estimated residue without $k$ can still
produce a relative ranking. An unavailable tuning estimate
has its own state. A caller can explicitly choose a
declared grid as a fallback and record that choice.

Preserve the tuning source and its scope. For a timed
Skill #40 estimate, use the same epoch and a frame inside its
available measurement span. Check the evidence spans for
gaps or changes of tuning. The bounding span can include
gaps. If the estimate corrected the sample rate, apply the
same factor to spectrum and bass frequencies in that epoch.
The calibrated bin mass stays the same because a change of
frequency-axis spacing has the reciprocal effect on density.
Untimed tuning is supplied as precomputed evidence.
[Tuning analysis](../../audio-tuning-analysis/references/TUNING_ANALYSIS_CONTRACT.md#use-and-verify) ·
[Clock domains](../../audio-timebase-sync/references/TIMEBASE_CONTRACT.md#mapping-rate-domains)

## Chord scores and decisions

Keep the raw vector, per-point assignments, and absolute
power. Count classes with positive mass at or above a stated
share of the total. An interpolated point can occupy two
classes. Use separate source evidence when interpreting
the number of notes.

For root $r$, compare the three classes $r+\{0,4,7\}$ for
major and $r+\{0,3,7\}$ for minor, with indices modulo 12.
Use the same nonzero vector $c$ for all 24 templates. For
the template's class set $T$, the reference uses

$$
S_T=\frac{\big(\sum_{k\in T}c_k\big)^2}{3\sum_{k=0}^{11}c_k^2}.
$$

This squared cosine preserves the cosine ordering for
nonnegative vectors. Set the score floor and ambiguity
margin in squared score units. The exact power, squared
scores, and score differences use the represented input
weights. Hz conversion has logarithmic roundoff. Use a margin
appropriate to that precision and to the measurement task.
[Müller, template-based chord recognition](https://www.audiolabs-erlangen.de/resources/MIR/FMP/C5/C5S2_ChordRec_Templates.html)

Use these decisions in order.

| Status | Condition and retained evidence |
| --- | --- |
| Input unavailable | A frame is incomplete or has no ready boundary. Preserve its nominal and available support. |
| Tuning unavailable or out of scope | Preserve the input and the tuning record. The reference supplies no tuned chroma. |
| Insufficient power | The admitted mass is zero or below its absolute floor. Keep raw power and chroma and leave ranking empty. |
| Poor fit | The leading squared score is below its floor. Retain all candidate scores. |
| Ambiguous | The difference between the first two scores is at or below the declared margin. Keep all candidates within that margin of the top. |
| Unanchored | A unique qualified candidate has a relative grid coordinate and the semitone lift is unspecified. |
| Matched | The absolute grid, enough power, adequate score, and a lead above the margin support one label. |

Power and score floors admit equality with positive
admitted mass. A tie at the ambiguity margin stays ambiguous.
Candidate order is descending score, then root and quality
for display. Declare a separate decision policy for the
musical label `N` (no chord). A chord score measures template
fit. Calibrate any fit threshold or probability on labeled
material from the intended task.
[Harte et al., chord symbols and no-chord](https://ismir2005.ismir.net/proceedings/1080.pdf)

## Bass and voicing

Compare untreated peaks and qualified fundamentals when
strong partials can contribute several chord tones. The
harmonics 1, 3, and 5 of one C4 can produce a near-unit
C-major score. State what the frequency observations support.

Use an independently qualified bass observation with a
frequency, epoch, and support. The reference checks that
the bass support contains the chroma frame center in the
same epoch and tap. Map its frequency with the same rate correction
and tuning. Qualify the nearest semitone within a declared
tolerance below 50 cents (25 cents by default). A matched
triad with bass on its root, third, or fifth has inversion
index 0, 1, or 2 respectively. Leave the inversion unset
if the bass is absent, out of scope, off grid, or outside
the chord. Retain the bass observation and its available
diagnostics. Identical chroma can describe multiple voicings.
[Harte et al., chord root and bass](https://ismir2005.ismir.net/proceedings/1080.pdf)

## Time and evaluation

For original support $[s,e)$, keep the exact doubled
center $s+e-1$. The reference uses the latest ready boundary
among the power frame, its timed tuning, and any in-scope
bass used for diagnostics. Its observed evidence delivery
is the latest reported boundary if every dependency reports
one. Measure dispatch separately. If a later decision
qualifies a frame, carry that dependency in the input timing.

With a beat-synchronous extension, clip disjoint frame
cells to the beat interval and weight each raw vector by
its admitted duration. Report the covered fraction on the
beat. Keep the original overlapping analysis windows and
the timing of both beat anchors. Later tuning, later anchors,
and smoothing affect readiness. Test a short chord next to
a boundary as well as a sustained passage.
[Beat readiness](../../audio-beat-tracking/references/BEAT_TRACKING_CONTRACT.md#input-clock-and-readiness) ·
[Ellis and Poliner, beat-synchronous chroma](https://www.ee.columbia.edu/~graham/papers/EllisP07-coversongs.pdf)

Evaluate on common reference and estimate intervals. State
the label vocabulary, gap handling, and duration denominator.
Report coverage and duration-weighted agreement. Compare root
and quality, then add inversion agreement where reliable bass
labels exist. For key or extended-chord tasks, provide the
appropriate longer context and vocabulary and evaluate them
separately.
[mir_eval chord metrics](https://mir-eval.readthedocs.io/stable/api/chord.html)

## Bounded reference

[Reference](../scripts/reference_chroma_harmony.py) ·
[Fixtures](../../../tests/fixtures/AUDIO_CHROMA_HARMONY_GOLDENS.md) ·
[Executable checks](../../../tests/test_audio_chroma_harmony_reference.py)

| Entry point | Contract |
| --- | --- |
| `PowerFrame` | Supply a bounded tuple of nonnegative point masses from DC to the epoch's Nyquist, declared power units, and original support. A frame without ready support contains no points. |
| `power_frame_from_psd` | Convert the complete one-sided grid to masses. Derive exact centers and spacing from the epoch and FFT length. Preserve the transform size and the actual window support. |
| `ChromaGrid` | Declare A4 directly or use `from_tuning` with the source result and optional integer semitone lift. A lift of zero is an explicit choice of representative. |
| `ChromaProfile` | Set the frequency band, power and reporting floors, score and margin limits, and bass tolerance. Default floors and the margin are zero. The default band admits all positive frequencies. |
| `split_pitch` and `score_triads` | Verify an exact pitch split and the all-template ranking on supplied coordinates and weights. |
| `analyze_chroma` | Use the available input from one frame. Return raw masses, assignments, candidate evidence, optional absolute label and inversion, and sample boundaries. |

The adapter accepts up to 8,192 FFT samples and 4,097
one-sided bins. The point path accepts up to 4,097 supplied
points. The reference uses stable octave-reduced logarithmic
conversion from the tuning reference and exact rational
arithmetic for accumulation and score decisions. Use it to
check alternate spectral front ends and performance paths.
