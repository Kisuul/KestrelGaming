# Pitch tracking contract

[Support](#frame-geometry) · [Difference](#fixed-support-lag-difference) ·
[Selection](#candidate-selection-and-refinement) · [Voicing](#level-and-voicing) ·
[Timing](#timing-tracking-and-evaluation) · [Reference](#bounded-reference)

## Signal model

For a periodic signal model, the fundamental frequency $F_0$ is
$f_s/p$ for the shortest repeating period $p$ in sample units.
A finite record supplies evidence for one or more candidate periods.
A harmonic above $F_0$ can have the largest spectral peak. The
fundamental can be absent while other harmonics support its period.
When only even harmonics of a proposed $F_0$ are present, the observed
signal also repeats at half the proposed period. State which evidence
or source prior supports an octave choice. Two independent sources
can have a shared repetition period. A monophonic estimator can
return that period and tell you little about the isolated sources.
[YIN, §§II–III](https://www.ee.columbia.edu/~dpwe/e6820/papers/deChevK02-yin.pdf) ·
[Harmonic peak assignment](../../audio-harmonic-analysis/SKILL.md)

## Frame geometry

Declare a channel or mix, the tap, PCM units, clock domain, rate,
epoch, frame grid, and preprocessing. Check mix cancellation and
level changes before interpreting an unvoiced result. Keep the pitch
band $0<f_{\min}\leq f_{\max}\leq f_s/2$ and the exact period band
$[L,U]=[f_s/f_{\max},f_s/f_{\min}]$.

| Profile | Integer seed range | Last evaluated lag $P$ |
| --- | --- | --- |
| Integer only | $\lceil L\rceil$ through $\lfloor U\rfloor$ | $\lfloor U\rfloor+1$ |
| Refined period | $\lfloor L\rfloor$ through $\lceil U\rceil$ | $\lceil U\rceil+1$ |

The extra evaluated lag supplies the right neighbor of the last
seed. Compute positive lags from one and include the left neighbor
of the first seed. With no integer in the physical band, the
integer profile has no candidate seeds.

For comparison width $W$ and hop $H$, a frame beginning at $s$
reads $M=W+P$ samples on $[s,s+M)$. Use $x[0]$ through $x[M-1]$
with indices relative to $s$. Use $1\le H\le M$ for contiguous
frame coverage. Keep $W$ fixed across all lags, including guard
lags. Choose $W$ with enough periodic evidence at the low end and
time resolution for changes of pitch. Check phase sweeps and short
notes. With 48 kHz input and a 50 Hz lower limit, the period is
960 samples and the guard is 961. A frame of 1,024 samples then
has 63 sample pairs at every lag. On the fixture, those pairs
supply a misleading trough for a clean 50 Hz tone. Increasing the
comparison width to 1,920 samples admits the 50 Hz candidate and
raises required support to 2,881 samples.
[Low-pitch fixture](../../../tests/fixtures/AUDIO_PITCH_TRACKING_GOLDENS.md#small-comparison-support) ·
[Timebase and epochs](../../audio-timebase-sync/SKILL.md)

## Fixed-support lag difference

Use a rectangular comparison. Let $d(0)=0$ and for $1\le p\le P$
compute the squared difference over $W$ pairs.

$$
d(p)=\sum_{i=0}^{W-1}\big(x[i]-x[i+p]\big)^2,\qquad
C(p)=\sum_{j=1}^{p}d(j),\qquad
y(p)=\frac{p\,d(p)}{C(p)} .
$$

Here $y$ is the cumulative mean normalized difference (CMND).
Use $y(0)=1$ by convention. When $C(p)=0$, mark $y(p)$ unavailable.
The sum starts at one even when the search band starts much higher.
Raw $d$ has squared PCM units and sums $W$ terms. CMND is
dimensionless. If a common gain and offset leave all sample
differences proportional, CMND is invariant. Check the level gate
and actual PCM quantization separately.

For an FFT version, let $E_p=\sum_{i=0}^{W-1}x[i+p]^2$ and
$R(p)=\sum_{i=0}^{W-1}x[i]x[i+p]$. Then

$$
d(p)=E_0+E_p-2R(p).
$$

Use both window energies on the same support. Use linear correlation
of the $M$-sample span with its first $W$ samples and a transform
length of at least $M+W-1$. Verify the lag sign and extracted offsets
against direct products. Subtraction of comparable energies can
erase small $d$ even in binary64. Subtract one common offset from
all samples before computing the identity when DC dominates. Check
the remaining cancellation at near-repeats. Compare to direct
differences, measure the error at the scale of the trough, and use
a direct calculation when the error can change the decision. A
negative value from the identity warrants a numerical check.
[Linear correlation](../../audio-cross-correlation/references/CROSS_CORRELATION_CONTRACT.md#verify-fft-and-refinements) ·
[Numerical stability](../../audio-numerical-stability/SKILL.md)

## Candidate selection and refinement

Inspect seeds in ascending lag order. Require defined CMND at $p$
and its neighbors and use $y(p)<y(p-1)$ and $y(p)\le y(p+1)$.
This rule selects the leading index of a trough plateau. Record
every trough with its seed, depth, fit method, period, frequency,
and eligibility. Apply the depth threshold $y(p)<h$ at the integer
seed, where $0<h\leq1$. Equality fails. Later troughs, including
exact repetition at a longer period, can remain eligible.

For refinement, use the three values $z_-,z_0,z_+$ from the named
curve. Require finite available values, a local minimum, and
positive curvature $a=z_- -2z_0+z_+$. Compute

$$
\delta=\frac{z_--z_+}{2a},\qquad
\hat p=p+\delta,\qquad
\hat F_0=f_s/\hat p.
$$

Require $|\delta|\leq 1/2$. If the fit geometry fails, record the
integer fallback and its method. For every method, qualify the
final period on the closed interval $[L,U]$. Record any out-of-band
fit with its actual period. Moving an out-of-band fit to a boundary
would create a frequency without supporting evidence.

The reference tests the integer CMND depth and defaults to fitting
raw $d$ for the period. A CMND fit is available for comparison.
YIN step 5 uses a normalized interpolated ordinate for trough
comparison and the raw-difference abscissa for the period. The
reference selects the first eligible trough and leaves the frame
unvoiced if there is none. A global-minimum fallback is a separate
policy in the YIN paper. Test it as a separate voicing decision if
you use it. Depth measures repeatability on the selected support.
A calibrated probability requires a model and validation data.
[YIN, §§II.B–E](https://doi.org/10.1121/1.1458024)

## Level and voicing

Measure the signed mean $\mu$ over all $M$ samples. Measure AC
mean square $v=M^{-1}\sum_{i=0}^{M-1}(x[i]-\mu)^2$. Use an AC RMS
floor $A$ in the declared PCM units. Apply the frame rules in order.

| Frame state | Condition | Evidence to retain |
| --- | --- | --- |
| Unavailable | Fewer than $M$ samples. | Nominal interval and actual input boundary. |
| Silence | Complete, $v=0$ and $\mu=0$. | Mean, AC power, and unavailable positive-lag CMND. |
| DC only | Complete, $v=0$ and $\mu\ne0$. | Signed mean, AC power, and unavailable positive-lag CMND. |
| Below floor | $0<v<A^2$. | Level and trough diagnostics. |
| Unvoiced | $v>0$, $v\ge A^2$, and no eligible trough. | Lag curves and trough rejections. |
| Voiced | $v>0$, $v\ge A^2$, and an eligible trough. | First eligible trough and alternatives. |

The floor admits equality for nonconstant input. A periodic
signal below the floor can have an eligible trough with no selected
pitch in the frame result. Aperiodic noise at an adequate level
can be unvoiced. Evaluate false positives at the declared floor
and threshold with quiet periodic material, noise, and DC.

## Timing, tracking, and evaluation

Keep the exact center $2c=2s+M-1$ and the first complete input
boundary $s+M$ as separate quantities. A short frame has a nominal
center and a measured input end. Its ready boundary is unavailable.
An observed delivery boundary can be later than the first complete
input boundary. Convert elapsed time from differences on the
sample clock. Measure dispatch time separately on the target host.

To track over time, retain competing candidates and an unvoiced
state. Specify how duration, entry and exit, transition rate, and
octave swaps affect selection. Consider pYIN's threshold
distribution and Viterbi decoding when you need a sequence model.
For a live tracker, state the commitment and revision rules. Replay
equal prefixes with different continuations to measure lookahead.
Test a transient, a gradual glide, an abrupt note leap, and a gap.
Keep unvoiced or unavailable intervals visible in downstream data.
[pYIN, §§2.1–2.2](https://webspace.eecs.qmul.ac.uk/s.e.dixon/pub/2014/MauchDixon-PYIN-ICASSP2014.pdf) ·
[Buffering](../../audio-stream-buffering/SKILL.md)

Align estimates with labels on the declared time grid. Report
labeled coverage and missing data. Count estimated voiced frames
among reference voiced frames for voicing recall and among
reference unvoiced frames for voicing false alarm. Report their
denominators. For matched positive estimates and references, use
signed cents $1200\log_2(\hat F_0/F_{0,\text{ref}})$. Separate
octave-sensitive pitch agreement from pitch-class agreement.
The latter can accept an octave error. State the tolerance and
denominator for each result. The mir_eval melody defaults are
50 cents for raw pitch and raw chroma accuracy. Choose a tolerance
to match the application. Report low support, polyphony, and
octave alternatives along with aggregate scores.
[mir_eval melody metrics](https://mir-eval.readthedocs.io/stable/api/melody.html)

## Bounded reference

The [reference](../scripts/reference_pitch_tracking.py) accepts
list or tuple PCM with finite binary64 or signed 32-bit integer
samples from a one-channel scope epoch. The caller supplies the
mix if needed. Each frame uses the same represented PCM for
level and periodicity. Exact integer differences on a shared
dyadic scale and rational results preserve the evidence present
in those samples. Use this arithmetic as an offline baseline
when checking a production path.

| Entry point | Contract |
| --- | --- |
| `PitchProfile` | Set $W$, band, CMND threshold, AC RMS floor, and refinement. Raw refinement, threshold $1/10$, and a zero floor are defaults. |
| `PitchGrid` | Bind the profile, epoch, hop, and first start. Derive exact period limits, seeds, and support. |
| `measure_pitch` | Analyze one grid position using at most $M$ samples. Keep an incomplete request unavailable. |
| `PitchTracker.push` | Accept contiguous blocks beginning at the first start. Return complete rows in grid order. Use the supplying block end as the observed delivery boundary. |
| `PitchTracker.reset` | Start a different epoch and discard pending samples. Use reset after a gap, seek, or incompatible input change. |

The reference caps $W$ and $P$ at 4,096 each, blocks at 8,192
samples, and output at 128 frames per block. It checks a block
before changing assembler state. A caller can partition delivery
into smaller blocks. Each complete frame uses a separate candidate
decision. Contiguous replay verifies estimates and addresses.
Measure sequence inference and real-time execution in the target
system when those capabilities are required.
[Fixture definitions](../../../tests/fixtures/AUDIO_PITCH_TRACKING_GOLDENS.md) ·
[Executable checks](../../../tests/test_audio_pitch_tracking_reference.py)
