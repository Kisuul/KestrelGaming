# Audio tuning analysis fixtures

[Contract](../../skills/audio-tuning-analysis/references/TUNING_ANALYSIS_CONTRACT.md) ·
[Reference](../../skills/audio-tuning-analysis/scripts/reference_tuning_analysis.py) ·
[Executable checks](../test_audio_tuning_analysis_reference.py)

Use twelve-tone equal temperament with A4 at 440 Hz unless
stated. For an intended shift of $c$ cents from A4, use
$440\cdot 2^{c/1200}$ Hz. Compare wrapped results by shortest
circular distance. For ideal values rounded to binary64,
use tolerances for the logarithm and angle. Check direct
cents wrapper boundaries exactly.

## Pitch and wrap

| Probe | Expected evidence |
| --- | --- |
| Four notes 60, 64, 69, 72 at $442\cdot2^{(k-69)/12}$ Hz. | With A440, each known-note error and the offset are $+7.8514150401$ cents. The resultant length is one to floating-point accuracy. With A442, the offset is near zero. |
| Label a $+55$ cent shift from 440 Hz as A4. Repeat with 880 Hz and 220 Hz. | Wrapped values are $-45$, 0, 0. Labeled errors are $+55$, $+1200$, $-1200$. |
| Wrap exact $+50$, $-50$, $+150$, $-150$ cents. Try both adjacent binary64 values at $+50$ and $-50$. | The exact endpoints map to $-50$. Adjacent values stay on their correct side of the seam. |
| Use notes at $+49$ and $-49$ cents. | The mean lies at the seam by circular distance and $R\approx0.9980267284$. The arithmetic mean of the two residues is zero. |
| Use notes at $+25$ and $-25$ cents. | The ideal resultant is zero. The test reports ambiguous and no selected direction. |
| Use notes at $-10$ and $+10$ cents. | The mean is near zero and $R\approx0.8090169944$. Each group contributes a residue about 10 cents from the mean. |
| Multiply a rational frequency and its A4 reference by the same positive rational. Move a separate observation by an exact octave. | Both transformations preserve the wrapped result. Known-note error changes by 1,200 cents per octave at fixed labels. |

Check one binary64 step on each side of 880 Hz for MIDI note
81. The unwrapped error retains its sign and agrees with
$1200\log_2(1+(f-880)/880)$. Evaluate the ratio of the largest
finite binary64 magnitude to the least positive subnormal
and its inverse. The reference keeps the wrapped result
finite with the original positive frequencies.

## Weight and qualification

| Probe | Expected evidence |
| --- | --- |
| Two note events at 0 cents and one at $+20$. Supply one frame for the first two and 100 equal frames for the last. | Three event IDs and 102 observations. Note weighting reports $+6.2183826553$ cents, $R\approx0.8324040137$, and total effective weight 3. Observation weighting reports $+19.6991646282$ cents, $R\approx0.9866275631$, and total 102. |
| One event with equal observations at $+25$ and $-25$, plus another event at 0. | The spread event has two half-weight rows. Overall mean near zero and $R=0.5$ within numerical tolerance. |
| Two observations at 0 and $+20$ cents each with weight $10^{308}$, and one negligible subnormal weight. | Observation mode gives $+10$ cents. The eligible raw total exceeds the last finite binary64 value and remains exact. Scaling all weights by a positive common factor preserves the mean vector. |
| A zero-weight row, an excluded measured row, and rows for silence or unavailable input. | Retain the rows. There is no eligible weight, direction, or concentration. |
| Twenty-four positive observations of one event with a requirement of two note events. | Concentration still exists. The result remains unavailable for insufficient notes. |
| Set the minimum concentration equal to the computed $R$ and then set it one binary64 step higher. | Equality admits the estimate. The higher floor retains the vector and reports ambiguous. |

For the partial probe, supply the second, third, and fifth
harmonics of 440 Hz with equal weights in one event. The
residues are 0, $+1.9550008654$ and $-13.6862861352$ cents.
Pooling them gives $\delta\approx-3.7515674710$ cents with
$R\approx0.9067243981$. Divide by the known harmonic numbers
and the result becomes zero. The relatively large $R$ in the
first run reflects the concentration of biased evidence.

## Clock and timing

A nominal 48,000 Hz analysis rate and a measured 48,004.8 Hz
capture rate give an exact correction factor of $10001/10000$.
Apply that factor to indicated frequencies for
$+0.1731147493$ cents. Reversing the two rates makes the
correction negative. The correction keeps the observation's
nominal clock and original sample addresses in the evidence.

Use the Skill #39 reference on a cosine of amplitude 0.4 for
each note in the A442 fixture. Generate PCM at 48,004.8 Hz
with phase $0.25(k_i+1)$ radians for the zero-based note
index $k_i$. Use a width of 1,440 and a 150–1,000 Hz pitch
profile. Start the four frames at $O+2000k_i$ for
$O=2^{60}+37$. The nominal analysis needs 1,761 samples per
frame and the calibrated analysis needs 1,762. In this
fixture both select the same periods.

| Tuning input | Offset relative to A440 | Latest contributing readiness |
| --- | ---: | --- |
| Nominal pitch results | $+7.6778657528$ cents | $O+7761$ |
| Nominal results with calibrated frequency correction | $+7.8509805021$ cents | $O+7761$ |
| Pitch replay with the calibrated epoch | $+7.8509805021$ cents | $O+7762$ |

For the partial-input check, supply three complete frames from
one 22-sample block. Their ready boundaries run from $O+12$
to $O+20$. Add a two-sample partial frame starting at $O+16$
and measured silence starting at $O+40$. The full nominal
span ends at $O+52$. The contributing data are ready at
$O+20$ and observed at $O+22$. The partial remains unavailable.

## Comparator and review

For a pitch at $+13.25$ cents and histogram resolution 0.01,
the pinned librosa histogram policy gives lower edges
0.13 bins at 12 bins per octave and 0.26 bins at 24. Both
represent $+13$ cents. Check the conversion and bin edge when
using a histogram as a comparator.
[librosa 0.11.0 source](https://librosa.org/doc/0.11.0/_modules/librosa/core/pitch.html#pitch_tuning)
