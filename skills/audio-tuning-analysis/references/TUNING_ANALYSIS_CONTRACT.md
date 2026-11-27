# Tuning analysis contract

[Pitch](#pitch-quantities) · [Weights](#evidence-and-weights) ·
[Estimate](#circular-estimate) · [Clock](#clock-and-coverage) ·
[Verification](#use-and-verify) · [Reference](#bounded-reference)

## Pitch quantities

Choose twelve-tone equal temperament (12-TET) and an A4 frequency
$F_A$. The standard musical A specified by ISO 16 is 440 Hz. Use
the reference specified by the session or calibration. For a
positive measured fundamental $f$ and a known MIDI note $k$,

$$
f_k=F_A\,2^{(k-69)/12},\qquad
c=1200\log_2(f/F_A),\qquad
e_k=c-100(k-69).
$$

Report $e_k$ as a signed, unwrapped error. For an unlabeled 12-TET
grid, use the residue $r$ of $c$ modulo 100 cents. This measurement
identifies a grid up to an integer number of semitones. An octave
or semitone error in pitch tracking can leave the same residue.
When note identity matters, keep the labels and the unwrapped errors.
[ISO 16 catalogue](https://www.iso.org/standard/3601.html) ·
[Müller, log-frequency pitch representation](https://www.audiolabs-erlangen.de/resources/MIR/FMP/C3/C3S1_SpecLogFreq-Chromagram.html)

## Evidence and weights

Use qualified stable fundamentals with a declared tap and source.
A usable observation from Skill #39 has a selected pitch on a
voiced frame. Keep silence, constant nonzero signal, low AC level,
unvoiced input, incomplete input, and exclusions in the record.
Exclude them and zero weights from the estimate. Preserve a
measured frequency on an excluded attack or bend if it helps
explain the selection. Periodicity depth describes the pitch
evidence. Calibrate any probabilistic weight separately.
[Pitch tracking](../../audio-pitch-tracking/references/PITCH_TRACKING_CONTRACT.md#level-and-voicing)

Choose the independent unit that the estimate should describe.
For typical note tuning, prefer one stable observation per note
event. A note event ID can group multiple frames. Two separate
occurrences of one MIDI pitch use different event IDs. For
nonnegative caller weights $w_i$, let $G(i)$ contain all eligible
observations in the event. Equal note budgets use effective
weights

$$
u_i=\frac{w_i}{\sum_{j\in G(i)} w_j}.
$$

This gives each eligible note a total weight of one. An event
with dispersed residues contributes a shorter vector. Making
each note's mean direction a unit vector would discard that
dispersion. Use $u_i=w_i$ for per-observation weighting. With
equal frame weights, a long note gets more influence. Report
the counts of eligible observations and distinct identified
events, the weights, and the chosen policy.

Use a stable portion of each note. Check vibrato, attacks,
bends, and changes between groups or spans. When using spectral
peaks, qualify level, resolution, and harmonic assignment. In
a harmonic model, divide each partial by its harmonic number
when estimating the fundamental. Verify the result against
qualified fundamentals. The third and fifth partials sit off
the 12-TET grid of a tuned fundamental. Count their source note
once and check inharmonicity or unresolved sources before pooling.
[Harmonic assignment](../../audio-harmonic-analysis/references/HARMONIC_ANALYSIS_CONTRACT.md#harmonic-assignment)

## Circular estimate

Fold cents to the half-open interval $[-50,50)$ by taking
$((c+50)\bmod 100)-50$ with mathematical modulo. In binary64, the
addition can move the value immediately below 50 onto the
seam. Use a symmetric remainder and map exact $+50$ to $-50$.
The reference scales the exact frequency ratio by a power of
two and uses a logarithm of one plus its deviation from one.
The whole octaves drop out of the residue and stay in the
known-note error.

Let $U=\sum_i u_i$ over positive eligible weights. When $U>0$,
compute the normalized weighted vector $Z$, its length $R$,
and the estimate $\delta$.

$$
Z=\sum_i \frac{u_i}{U}e^{j2\pi r_i/100},\qquad
R=|Z|,\qquad
\delta=\operatorname{wrap}_{[-50,50)}\!\left(\frac{100\,\arg Z}{2\pi}\right).
$$

Normalize before summing the real and imaginary components.
The reference keeps weight sums and ratios exact and uses
binary64 for the trigonometry and stable component sums.
Report unavailable when there is no eligible weight or when
the number of identified notes falls below a required count.
For a direction, require $R>10^{-12}$ in this reference and
$R\ge R_{\min}$ for a declared concentration floor. A failed
direction check is ambiguous. Retain the normalized vector
components and $R$ when they exist. Use a floor suited to the
application and validation data. Phase becomes sensitive to
small component errors at low $R$.

A single observation has concentration one. Two groups at
$-10$ and $+10$ cents can give $R\approx0.809$ and a mean where
neither group sits. Inspect the residues or compare group
estimates. For a histogram, wrap its neighborhood across
the seam and retain competing modes. Report any uncertainty
interval with an observation model or a suitable resampling
unit such as independent note events.
[Dressler and Streich, §§2–3](https://ismir2007.ismir.net/proceedings/ISMIR2007_p357_dressler.pdf) ·
[SciPy circular mean](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.stats.circmean.html)

## Clock and coverage

A period converted using $f_{s,\mathrm{used}}$ on capture at
$f_{s,\mathrm{actual}}$ gives an indicated pitch scaled by
$f_{s,\mathrm{used}}/f_{s,\mathrm{actual}}$. The signed apparent
shift is $1200\log_2(f_{s,\mathrm{used}}/f_{s,\mathrm{actual}})$
cents. Use a measured rate or an independent known-frequency
tone through the same input path to distinguish clock bias
from source tuning. Correct a supplied indicated frequency by
$f_{s,\mathrm{actual}}/f_{s,\mathrm{used}}$. The correction keeps
the original sample coordinates and the declared upstream rate.
Check the upstream pitch band and reanalyze if its decisions
depend on the new rate.

Keep the original epoch, tap, support, and actual input end per
observation. The exact nominal center is $2c_s=s+e-1$ for start
$s$ and exclusive end $e$. Keep data readiness and observed
delivery as separate boundaries. When stable-note qualification
uses later evidence, include it in the ready boundary and record
the later delivery when known. The result includes the span of
supplied observations and the latest readiness of contributing
observations. Its contributing delivery is available when every
contributing observation has a reported boundary. A bounding
span can contain gaps. Use the per-row support to inspect them.

Measure each timed estimate within one epoch and tap. Compare
separate groups if clocks, taps, or sources differ. An untimed
estimate can use already qualified frequency observations with
a declared reference. Apply sample-rate calibration only with
identified clock provenance.
[Timebase and clock domains](../../audio-timebase-sync/references/TIMEBASE_CONTRACT.md#mapping-rate-domains)

## Use and verify

Check the circular error by the shortest signed distance
between offsets. Use unwrapped errors for known notes and time
alignment for drift comparisons. The librosa 0.11.0 histogram
comparator reports the lower edge of a winning bin in fractions
of a pitch step. Convert using $1200/B$ cents for $B$ bins per
octave. Its empty input returns zero with a warning. Check units,
binning, and the support before comparing methods.
[librosa pitch tuning source](https://librosa.org/doc/0.11.0/_modules/librosa/core/pitch.html#pitch_tuning)

Give a chroma consumer the declared reference, offset, validity,
and time scope. Apply the correction once. Shift grid centers by
$2^{\delta/1200}$ or subtract $\delta$ from measured cents before
folding. Use labeled notes or a stated prior to choose a semitone
representative for absolute pitch classes. Use a stated reference
or report unknown tuning if the estimate is unavailable or ambiguous.
[Chroma and harmony research](../../../memory/projects/kisuul/kestrelgaming/handoffs/2026-11-26-audio-chroma-harmony-research-r01.md)

## Bounded reference

[Reference](../scripts/reference_tuning_analysis.py) ·
[Fixture definitions](../../../tests/fixtures/AUDIO_TUNING_ANALYSIS_GOLDENS.md) ·
[Executable checks](../../../tests/test_audio_tuning_analysis_reference.py)

| Entry point | Contract |
| --- | --- |
| `TuningProfile` | Declare A4, note or observation weighting, the concentration floor and any minimum event count. Defaults are A440, equal note budgets, and no additional data floors. |
| `TuningObservation` | Supply an optional known MIDI note, note event ID, state, and nonnegative weight. A qualified row has a positive frequency. Timed measured frequencies have complete, ready support. |
| `observation_from_pitch` | Make an observation from a Skill #39 frame. Preserve voicing, nominal and available support, and the delivery metadata. Apply stable-note qualification in the caller. |
| `estimate_tuning` | Receive up to 4,096 observations from one epoch or an untimed set. Optionally correct from the epoch rate to a declared actual rate. Return evidence, coverage, result state, and optional estimate. |

The output keeps each raw weight and its effective weight, the
exact ratio used for a clock correction, and the weighted vector.
A representative A4 is available for an estimated offset. Its
exponential is evaluated in binary64. This offline estimator
uses supplied note events and qualification. Measure timing and
stability separately when adding a causal tracker or adaptive
tuning.
