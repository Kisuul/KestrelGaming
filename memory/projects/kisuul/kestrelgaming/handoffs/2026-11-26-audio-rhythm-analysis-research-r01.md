---
schema: 1
id: 2026-11-26-audio-rhythm-analysis-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-26
updated: 2026-11-26
sources: "Audio branch 327ca13df3cef9193599762685f1350ae4df6900; Skill 37 research PR 50 at eeb502a5bdfc2412cf4533b2e734b539cbd34193; Friberg and Sundstrom (2002); Grosche, Muller and Kurth (2010); executed exact-coordinate and periodicity fixtures below."
---

# Skill 38 research for rhythm analysis

## Summary

**Task outcome:** COMPLETE

Use timed events and a declared beat grid to measure when events occur
within each beat. The first reference should return inter-onset
intervals, beat-relative event positions, and residuals to named
subdivision grids. It should expose the evidence for competing grids.
Given a pulse estimate, metre and downbeat still require their own
evidence. The checks below cover tempo changes, a gap, swing, and a
Fourier tempo harmonic.
[Beat-tracking research](2026-11-21-audio-beat-tracking-research-r01.md)

## Evidence

### Map events to a declared beat

Record the sample rate, epoch, tap, event definition, and whether the
beats were supplied, observed, or inferred. Keep event weights in
named units, or count all accepted events equally. A simultaneous
accent can arise in several channels. Declare whether to count those
as separate voices, pair them, or use one source. For inter-onset
intervals, difference successive events within the intended voice
and continuous run. Preserve zero intervals for simultaneous events
if they are distinct observations.
[STFT frame geometry](../../../../../skills/audio-spectrogram-waterfall/references/STFT_WATERFALL_CONTRACT.md#frame-geometry) ·
[Timebase](../../../../../skills/audio-timebase-sync/SKILL.md)

With increasing beat anchors $b_j$, give beat $j$ the half-open support
$[b_j,b_{j+1})$. For an event $t$ in that support use

$$
\Delta_j=b_{j+1}-b_j,\qquad u=(t-b_j)/\Delta_j.
$$

Keep $u$ exact as a ratio of sample differences when the inputs
permit it. Return $j$, $u$, $\Delta_j$ and the two anchors. The last
anchor can be an observed beat while its following phase is
unavailable. Across a gap or changed epoch, leave the interval
unavailable. A live estimate made with a predicted next anchor must
retain that prediction and its status. A result with two confirmed
anchors becomes ready only after those anchors and the event are
available. A stable BPM alone gives no anchor for this mapping.

### Measure subdivisions

For $q$ equal subdivisions, test grid locations $b_j+k\Delta_j/q$
for $0\le k\le q$. The right endpoint is the next beat's zero slot.
Keep signed residual $t-(b_j+k\Delta_j/q)$ in samples and optionally
divide it by $\Delta_j$ for beat units. Retain a tie or apply a
declared tie rule and expose it. When the nearest slot is the next
beat, the residual is negative for an event just before it. Assign a
phase once and keep both the event and the grid location.

Compare each grid over the same eligible spans. Report matched event
count, residual distribution and which slots actually have support.
A grid can contain another grid's points, so residual alone can
favor unnecessarily dense grids. If a selection is required, declare
the allowed grids and preference for subdivision density. Use
independent evidence such as repeated accents or voice patterns for
a bar-level claim.

With one intended offbeat and two credible anchors, the long-to-short
ratio is $u/(1-u)$. Collect ratios by voice and tempo. Keep missed
notes, added syncopations and near-anchor events separate. A position
at $2/3$ is consistent with a 2:1 split. Friberg and Sundstrom found
large tempo dependence in the performances they measured.
[Swing study](https://doi.org/10.1525/mp.2002.19.3.333)

### Use periodicity as supporting evidence

A local autocorrelation of onset strength measures support for
lags. A windowed Fourier tempogram measures modulation frequencies.
An onset pulse train has harmonics, so a Fourier maximum may be at a
multiple of the beat rate. Autocorrelation can support multiples of
a period, including longer patterns. At either stage, retain the time
span, window, candidate rate and normalization. A longer window
contains more cycles and can hide a transition. Tempo-octave folding
is useful for comparison if the application permits half/double
rates. Keep the unfolded candidates for metrical decisions.
[Grosche, Muller and Kurth (2010), §§2–3](https://www.audiolabs-erlangen.de/content/resources/MIR/tempogramtoolbox/2010_GroscheMuellerKurth_TempogramCyclic_ICASSP.pdf) ·
[Autocorrelation tempogram](https://www.audiolabs-erlangen.de/resources/MIR/FMP/C6/C6S2_TempogramAutocorrelation.html)

### Executed checks and portable fixtures

| Probe | Verified result |
| --- | --- |
| At 48 kHz use anchors `[0, 24000, 45600, 69600]`. Use events `[12000, 34800, 57600]`, then `[16000, 38400, 61600]`. | Exact phases are `1/2` for all three first events and `2/3` for all three second events despite different beat lengths. The second set has long-to-short ratio 2. |
| Use the same anchors. Test event `24000` and then the last anchor. Change the epoch between the second and third anchors and test `34800`. | `24000` belongs to the second interval at phase zero. The last anchor has no bracket beyond it. After the epoch change, the `34800` phase is unavailable. |
| Add $2^{60}+37$ to the anchor and event coordinates. Test the offset `38400`. | Exact subtraction and division retain phase `2/3`. |
| Test an event at phase `1/4` against the two-subdivision grid. Compare a set of midpoint hits against the two- and four-subdivision grids. | The quarter point ties between zero and `1/2`. Midpoint hits have zero residual on both grids. |
| At a 100 Hz feature rate put unit pulses at $7+50j$ for $j=0,\ldots,15$ in 800 frames. Use the rectangle and zero elsewhere. | Raw linear autocorrelation at lags 25, 50 and 100 is `[0, 15, 14]`. The unnormalized Fourier magnitudes at 120 and 240 BPM are both 16 within `1e-12`. |

The phase checks used exact rational arithmetic. The periodicity
check used direct pair sums and direct complex sums. Musical metre
and groove accuracy require separate annotations and held-out
recordings.

## Next action

Implement the bounded beat-coordinate and subdivision reference.
Report unsupported spans, ties, signed residuals, and the time when
each result becomes available. Use the tempo-changing grid to
compare a local ratio with a single global BPM assumption. Review a
straight, a swung and a syncopated performance with independently
marked voices and anchors before selecting default tolerances.

## Revisit when

The beat commitment policy, event definition, subdivision vocabulary,
confidence interpretation, or annotation target changes.
