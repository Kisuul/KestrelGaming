---
schema: 1
id: 2026-11-21-audio-phase-coherence-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-21
updated: 2026-11-21
sources: "Kestrel audio branch 9c30102949678a114120e2e84f253cbd7de2737b with Skills 31 and 32, Welch (1967), Carter et al. (1973), SciPy 1.17.0 coherence and CSD, Smaart LE v9.1 user guide, Lachaux et al. (1999), and executed analytical, direct DFT, and simulation checks."
---

# Skill 33 research for phase and coherence

## Summary

**Task outcome:** COMPLETE

For `audio-phase-coherence`, report magnitude-squared coherence and the
phase of the averaged cross-spectrum at each frequency. Average the complex
cross-products and both auto powers over the same complete segments before
normalizing. Use signed phase to describe the relative shift and coherence to
describe the consistency of a complex gain across segments.

The [curriculum ledger](2026-11-17-audio-curriculum-status-r01.md) orders this
skill after [zero-lag stereo correlation](../../../../../skills/audio-stereo-correlation/SKILL.md)
and [Mid/Side analysis](../../../../../skills/audio-mid-side-analysis/SKILL.md).
A coherent polarity inversion cancels in an equal-weight mono fold. A delay
can move a shared transient outside its paired segment and reduce the
measured coherence. The fixtures below make both cases observable.

## Evidence

### Choose the estimator and phase sign

Welch averages modified periodograms across time segments. Carter, Knapp and
Nuttall describe applying overlapped FFT processing to magnitude-squared
coherence. SciPy 1.17.0 gives a concrete comparison for the ratio and uses
$\overline X Y$ for its cross density. Match the window samples, segment starts,
FFT size, detrending, scaling and input order for a differential check.
[Welch (1967)](https://ocean.phys.msu.ru/courses/geoseries/1967%20Welch%2C%20The%20Use%20of%20Fast%20Fourier%20Transform%20for%20the%20Estimation%20of%20Power%20Spectra_%20A%20Method%20Based%20on%20Time%20Averaging%20Over%20Short%2C%20Modified%20Periodograms.pdf)
· [Carter et al. (1973)](https://doi.org/10.1109/TAU.1973.1162496)
· [SciPy 1.17.0 coherence](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.signal.coherence.html)
· [SciPy 1.17.0 CSD](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.signal.csd.html)

1. **Declare paired sample support.** Record reference $x$ and measurement $y$,
   channel identities, taps, units, sample rate, epoch, and exact integer segment
   starts. Use complete real PCM segments of length $M\ge2$ with the same hop
   $0<H\le M$. Use DFT length $N\ge M$. With $K$ segments and origin $s$ the
   observation covers $[s,s+M+(K-1)H)$. Zero padding changes the frequency grid.
   The measured support and segment count come from the original samples.
   Specify any alignment as an explicit change of input indices.
   [Sample clocks](../../../../../skills/audio-timebase-sync/SKILL.md)
2. **Form both transforms the same way.** Use the unnormalized negative-exponent
   DFT, one window $w$, and one detrending rule for both channels. The proposed
   first reference retains DC and uses an arithmetic mean over complete segments.
   For bin $k$ set $d_k=2$ at paired positive frequencies and $d_k=1$ at DC and
   even-length Nyquist. The highest positive bin of an odd DFT is paired.
   Use $q_k=d_k/(f_s\sum_n w[n]^2)$ for both auto and cross density.
   [Kestrel PSD scaling](../../../../../skills/audio-power-spectral-density/references/PSD_CALIBRATION.md#normalization)
3. **Average products before taking the magnitude or phase.** With $j$ the
   segment index at a fixed bin, use

   $$
   D_{xx}=q_k\,\operatorname{mean}_j(\lvert X_j\rvert^2),\quad
   D_{yy}=q_k\,\operatorname{mean}_j(\lvert Y_j\rvert^2),\quad
   D_{xy}=q_k\,\operatorname{mean}_j(\overline{X_j}Y_j).
   $$

   Multiply the complex positive-frequency product by its one-sided factor.
   Adding the actual negative-frequency conjugate would discard the imaginary
   part. Auto density units are squared sample units/Hz. Cross density units
   are the product of the two channels' sample units per Hz.
4. **Calculate the two results.** Where both auto powers are positive, use

   $$
   \gamma^2=\frac{\lvert D_{xy}\rvert^2}{D_{xx}D_{yy}},\qquad
   \phi_{y\mid x}=\arg(D_{xy})\quad(D_{xy}\ne0).
   $$

   Use radians and declare a principal branch, such as $(-\pi,\pi]$.
   For a delayed copy $y[n]=x[n-d]$ with $d>0$, ideal matching
   bins have phase $-2\pi k d/N$ modulo a full turn. This follows by
   substituting $Y=X\exp(-2\pi i k d/N)$ in the cross density. An observed
   phase slope depends on correct pairing and the analysis support.
   Record the applied offset so a phase trace of the aligned residual can
   be related back to the original taps. At DC and even Nyquist the cross
   density is real, so its phase is 0 or $\pi$ when it is nonzero.
   Swapping channels conjugates the cross density. Reversing the measurement
   polarity adds $\pi$ modulo a full turn. Both operations preserve $\gamma^2$.
   Compare angles by their wrapped difference.

### Check evidence before interpreting the display

Cauchy–Schwarz on the two segment vectors bounds $\gamma^2$ in $[0,1]$. It is
one when $Y_j=A X_j$ for one complex constant $A$ across the included segments
at that bin, with positive auto powers. A fixed delay or inverted polarity can
therefore have perfect coherence in a controlled test. Inspect transfer phase,
mono output or the actual signal path to answer those questions. A common source
can drive both channels. A causal claim needs additional evidence.

| State | Measurement behavior |
| --- | --- |
| Fewer than two complete segments | Mark the proposed estimator as warming up. One nonzero pair of DFT bins yields $\gamma^2=1$ by algebra, regardless of whether it predicts another observation. |
| An auto power is zero | Coherence and relative phase are unavailable. Give the channel energy and validity state. |
| Both auto powers positive and $D_{xy}=0$ | Coherence is zero and phase is undefined. |
| Both auto powers positive and $D_{xy}\ne0$ | Compute coherence and phase. Keep any low-level gate or display blanking separate from the calculated values. |

Several complete segments can still contain only one energized pair at a
particular bin. A value of one then has support from that single event. Examine
the reference and measurement levels and segment contributions when deciding
whether the reading generalizes. Overlap reuses samples. It can improve the
estimate but the number of overlapped segments alone gives no independent
sample count. Choose segment length for bandwidth and time resolution, hop
for overlap, and buffer duration for the degree of averaging the application
can tolerate. A dropped segment or clock change needs an explicit validity or
epoch decision. [PSD verification guidance](../../../../../skills/audio-power-spectral-density/SKILL.md)

An estimator that pools segments must use the same nonnegative weights on all
three products. Independently masking auto and cross terms can violate the
bound. Average complex products before extracting phase. For example, equally
weighted cross phases of $+179^\circ$ and $-179^\circ$ combine near $180^\circ$.
Averaging their degree values gives $0^\circ$. A phase-only concentration can
instead average unit cross-phase vectors over valid pairs and take the magnitude
of that mean. It describes agreement of angles while the coherence formula also
responds to gain variation. For $X=[1,1]$ and $Y=[1,3]$ the phase-only result is
one and magnitude-squared coherence is $4/5$.
[Lachaux et al. (1999), phase-locking measure](https://pubmed.ncbi.nlm.nih.gov/10619414/)

Smaart LE documents separate phase/magnitude trace blanking and cites
misalignment, noise and reflections as diagnostic leads. Select a
display threshold for the operating context and label masked data.
A display that shows the square root needs to label the quantity as
coherence magnitude and use a threshold in those units.
A low reading by itself does not identify a cause. Check both tap levels,
the known delay and the repeatability of the stimulus. Prefer a controlled
single change, such as adding a known shift, before attributing an effect to
the physical signal path. [Smaart LE v9.1 user guide, Coherence, pp. 68–69](https://rationalacoustics.de/download/smaart_le_v9.1_user_guide.pdf)

For a transfer measurement with $Y=AX+E$, assume $E$ is uncorrelated
with $X$ at the bin. The population cross density is $A D_{xx}$ and the
response density is $\lvert A\rvert^2D_{xx}+D_{ee}$. The resulting
magnitude-squared coherence is the fraction of response power explained
by that linear model. For example, equal modeled response power and additive
noise power give 0.5. These assumptions matter when interpreting a reading
as a noise fraction. The same coherence can arise from segment-to-segment
gain variation.

### Respect numerical limits and estimator uncertainty

A product of two finite auto densities can overflow or underflow. For the
ratio and phase, scale each channel's complex segment vector by a fixed positive
maximum component magnitude at that bin before accumulating the products. A
positive scale for each vector cancels in the ratio and preserves phase.
The normalization scale for reporting physical densities must remain explicit.
Apply the same segment selection and weights to all terms. Accumulate real and
imaginary cross-products accurately when they nearly cancel. Use an endpoint
rounding tolerance tied to the numerical error budget. Investigate values
outside that tolerance as an estimator or arithmetic defect.
[Numerical stability](../../../../../skills/audio-numerical-stability/SKILL.md)

For an optional null-model check, consider $K>1$ independent, equally weighted,
circular complex Gaussian coefficients per channel at one interior bin. Under
independence between channels, a unitary rotation can align the reference
channel's vector of $K$ coefficients with a coordinate axis. The statistic
then has the distribution of one exponential random variable divided by the
sum of that variable and $K-1$ independent exponentials of the same mean.
It has mean $1/K$ and tail probability $(1-c)^{K-1}$ at threshold $c$.
The 5% single-bin threshold for $K=8$ is about 0.3482.

Apply that result only to the stated model. Overlapped segments, real-only
endpoints, multiple comparisons, averaging weights, and colored or time-varying
signals require their own uncertainty analysis. Keep display blanking and
statistical inference distinguishable.

### Executed checks and portable fixtures

| Fixture | Result |
| --- | --- |
| At one bin, $X=[1,1]$, $Y=[1,-1]$ | Each single segment gives coherence 1. The pooled auto powers are 1 and 1 with unit scale. The pooled cross-product is 0, so coherence is 0 and phase is unavailable. |
| At one bin, $X=[1,1]$, $Y=[1,3]$. Then use $Y=[-1,-1]$. | Gain variation gives coherence $4/5$ at phase 0. The inverted copy gives coherence 1 at phase $\pi$. Its equal-weight sum with the reference vanishes. |
| At one bin, $X=[1,1]$, $Y=[e^{i179^\circ},e^{-i179^\circ}]$ | Coherence is about 0.99969541351 at phase $180^\circ$ under the stated branch. An angle average gives the wrong direction. |
| Four rectangular segments of 64 samples at 48 kHz. Use a 3 kHz cosine with zero initial phase and periodic extension for both signed delays $d=\pm4$ samples. | The probes measured coherence 1 in bin 4 with phases $-90^\circ$ and $+90^\circ$, respectively. Zero-lag correlation over the complete cycles was near zero in both cases. Reversing input order conjugated the cross density. |
| In nine samples put a unit impulse at index 3 of $x$ and 4 of $y$. Analyze rectangular length-4 segments with hop 4. Repeat with $x[0:8]$ paired with $y[1:9]$. | Before alignment, both channels have energy but the cross-products are zero. Coherence is zero at all three bins. Known alignment gives coherence one in all three bins, supported by the single energized pair of segments. |
| Repeat two matching bin coefficients of magnitude $2^{500}$, then $2^{-530}$. | Individual auto powers were finite and positive. Their products overflowed and underflowed in binary64, respectively. Per-channel vector scaling gave coherence one in both probes. |

A direct DFT matched SciPy 1.17.0 on 72 bins across four Welch configurations.
The greatest absolute auto or cross density difference was $1.968\times10^{-19}$
in normalized PCM squared/Hz. The greatest coherence difference was
$3.497\times10^{-15}$. To reproduce, use 48 kHz and six complete segments plus
a two-sample tail. Set $(M,N,H)$ to $(24,32,12)$ and $(24,33,12)$ with a periodic
Hann and no detrending, $(25,25,25)$ with a rectangular window and no detrending,
and $(31,48,17)$ with a periodic Hann and per-segment mean subtraction. For each
case generate $x$ and then an independent noise tape $v$ from standard Gaussian
draws with NumPy PCG64 seed $3300+N$. Set $y=0.6\,\mathrm{roll}(x,1)+0.5v$, with a
circular shift for the generated tape only. Pass the same explicit window and
settings to both methods. Also check each auto-density integral against its
window-energy-normalized mean square.

The null probe used 40,000 independent complex Gaussian pairs of segment
vectors for each $K$, with independent standard real and imaginary components
and NumPy PCG64 seed $330700+K$. Observed mean coherence was 0.49994, 0.12586 and
0.03107 at $K=2,8,32$. The respective 5% threshold exceedance fractions were
0.04983, 0.05128 and 0.05038. These simulations exercise the stated null
model and the comparison runs exercise the specified finite fixtures.

## Next action

Implement an offline estimator on aligned PCM with explicit segment support,
power, phase, coherence and availability. Run the analytic cases first. Then
check odd/even one-sided density and complex sign with the matched oracle.
Exercise zero channels, zero cross density, first-frame warm-up, a single
energized segment, channel swap, polarity, extreme magnitudes, and invalid or
discontinuous input. Preserve exact sample bounds across callback partitions
if the implementation offers streaming.

Give the reviewer the delayed impulse and the inverted copy. Ask them to
identify the supported time intervals, correct the known offset at the
measurement tap, and show why the coherence and phase lead to different
diagnoses. Use the actual mono path to check audible cancellation.

## Revisit when

The capture alignment, spectral convention, averaging weights, taper, phase
mask, numerical representation or downstream application changes.
