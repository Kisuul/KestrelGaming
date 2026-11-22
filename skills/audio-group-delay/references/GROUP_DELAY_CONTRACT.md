# Audio group delay measurement contract

[Timing](#timing-and-units) · [Known model](#known-model) ·
[Sampled transfer](#sampled-transfer) · [Offline reference](#offline-reference)

## Timing and units

Use measurement over reference with the negative-exponent transform.
For $\omega=2\pi f/f_s$, group delay is $g=-d\phi/d\omega$ in
samples and $\tau=g/f_s$ in seconds. $f$ and $f_s$ are in Hz.
A pure delay $d$ gives $g=d$. A nonzero constant gain preserves the
slope. An inversion adds a half-turn to phase.

Record the tap order, clock domain, epoch, exact rate, and original
sample intervals. A positive advance shifts a measured response
earlier. Track both the advance already applied to the input and
any extra advance used to resolve the phase branch. Establish a
time mapping before making clock-based claims across devices.
Retain the same response support when applying a timing correction.
Use a broadband delay measurement to check the coarse offset.
[Sample time](../../audio-timebase-sync/SKILL.md) ·
[Cross-correlation](../../audio-cross-correlation/SKILL.md) ·
[Phase and group delay](https://www.dsprelated.com/freebooks/filters/Phase_Group_Delay.html)

Phase delay $-\phi/\omega$ depends on the phase branch. Group delay
describes the local phase slope. An envelope can approximately
follow that slope when magnitude and slope are nearly constant over
the signal band. Check the impulse response for the first arrival.
A causal echo can give negative group delay in part of the band.

## Known model

For a real coefficient sequence $u[n]$ starting at index zero,
form $U=\sum_n u[n]e^{-j\omega n}$ and
$M_U=\sum_n n u[n]e^{-j\omega n}$. The derivative is $U'=-jM_U$.
Use $\operatorname{Re}(M_U/U)$ for an FIR with response $U$, or
$\operatorname{Re}(M_B/B-M_A/A)$ for a rational section $B/A$.
Add the section derivatives when every section is valid and add
any explicit bulk delay. Use coefficients in ascending powers of
$z^{-1}$ with $a_0\ne 0$.
[Numerical derivative](https://www.dsprelated.com/freebooks/filters/Numerical_Computation_Group_Delay.html) ·
[Filter conventions](../../audio-filter-design/references/FILTER_DESIGN_CONTRACT.md#4-frequency-response-group-delay-and-sampled-acceptance)

Mark a numerator zero, denominator zero, or common zero as
unavailable. For a common zero, reduce the representation first
if the task requires its limiting response. Keep a valid zero
slope distinct from an unavailable value. An analytic point can
have a defined derivative at DC or Nyquist. When comparing with
SciPy, inspect singularity warnings and their output placeholders.
[SciPy 1.17.0 group delay](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.signal.group_delay.html)

Evaluate phase axes exactly. The other reference rotations are
represented by binary64 values. Accumulate the represented products
and ratios exactly to preserve range. An optional floor compares
each polynomial magnitude with the floor times its coefficient
one-norm. Label a nonzero value below this floor separately from
a detected zero. Use an error budget for non-axis points near a null.
[Numerical stability](../../audio-numerical-stability/SKILL.md)

## Sampled transfer

Use a strictly increasing grid in Hz. For a paired Welch capture
form $H_1=C_{xy}/S_{xx}$ at positive reference density. Interpret
this estimate with a reliable reference and uncorrelated output
noise. Keep segment support and the grounds for a level or
magnitude-squared coherence gate.
[Paired Welch convention](../../audio-phase-coherence/references/PHASE_COHERENCE_CONTRACT.md#welch-profile)

Qualify each adjacent interval. A true null can lie between two
valid bins. Use a finer supported grid or a known model to inspect
such an interval. Break an aperture at a missing or rejected bin,
a zero response, or an unqualified edge.

Let $a$ be the input advance already applied and $b$ the additional
fit advance. For each adjacent interval of width $\Delta f$, take
the principal phase increment of
$H_{k+1}\overline H_k\exp(j2\pi b\Delta f/f_s)$. Reduce the rotation
before trigonometry. Use exact real and imaginary products and
scale both components together for angle conversion.

Use a verified bound $G$ on the absolute residual delay throughout
the edge and a phase uncertainty margin $m$ in turns. Require
$G\Delta f/f_s+m<1/2$. Check that the observed residual increment
agrees with that limit. A missing bound or a half-turn leaves
the branch unresolved. On a uniform $N$-point grid, pure delays
separated by $N$ samples give the same bins.

Sum the qualified adjacent increments over the aperture. Divide
their negative sum in turns by $(f_+-f_-)/f_s$. Report the midpoint
and actual width $f_+-f_-$ in Hz. Add $a+b$ to the residual delay to
restore the original tap delay. Keep both offsets in the result.
For a local weighted phase fit, use actual Hz coordinates and report
the weighted center and full frequency support.
[Aperture and phase sampling](https://helpfiles.keysight.com/csg/m9485a/tutorials/group_delay6_5.htm)

Check two apertures in the same band. With independent endpoint
phase noise of standard deviation $\sigma_\phi$ radians, delay
standard deviation is $\sqrt 2\,\sigma_\phi/(2\pi\Delta f)$ seconds.
Account for covariance with correlated endpoints. A wider aperture
can reduce variance and blur changes in the point delay. For an
excess group-delay curve, identify the minimum-phase reference
and any applied time offset.
[Excess group delay](https://www.roomeqwizard.com/help/help_en-GB/html/graph_groupdelay.html)

## Offline reference

Put `audio-oscilloscope/scripts`, `audio-phase-coherence/scripts`, and
`audio-group-delay/scripts` on the module search path. Use
`model_group_delay` with `RationalSection` values, a frequency array,
and the exact rate. The limit is four sections, 129 coefficients
per polynomial, 1,024 frequencies, and 262,144 coefficient-frequency
terms. The result retains the sections, rate, floor, and bulk delay.

Use `sampled_group_delay` with `TransferSample` values, a
`SlopeProfile`, and one boolean `supported_edges` entry for each
adjacent interval. `aperture_steps` selects the number of consecutive
intervals to combine. Keep original tap and sample bounds with
`TransferProvenance`. With `welch_group_delay`, supply Skill #33's
analysis and any `WelchQuality` settings. The result retains the
analysis and the supplied provenance.

Each unavailable sampled aperture carries the first failed edge
index. Its status identifies an unqualified interval, rejected bin,
zero response, unresolved branch, phase mismatch, or angle underflow.
The comparison of observed angles allows $2^{-48}$ turn for
roundoff. The half-turn bound uses the declared exact coordinates.
Returned delay fractions preserve coordinates and offset arithmetic.
Sampled phase still has the accuracy of the binary64 angle and
the input transfer.
[Fixtures and review tasks](../../../tests/fixtures/AUDIO_GROUP_DELAY_GOLDENS.md)
