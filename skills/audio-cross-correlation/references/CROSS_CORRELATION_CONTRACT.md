# Audio cross-correlation measurement contract

[Clock and lag](#clock-and-lag) · [Score and gates](#score-and-gates) ·
[Interpretation](#interpret-the-peak) · [FFT and refinements](#verify-fft-and-refinements) ·
[Offline reference](#offline-reference)

## Clock and lag

Select reference $x$ and measurement $y$ in that order. Record
their taps, units, half-open capture bounds, epoch, clock domain, and
exact rate $f_s$. The samples may be in one or two captures on that
clock. A gap or reset starts a new observation. For different devices,
establish a clock mapping before interpreting a lag as elapsed time.
[Capture contract](../../audio-oscilloscope/references/OSCILLOSCOPE_CONTRACT.md) ·
[Sample clocks](../../audio-timebase-sync/SKILL.md)

At integer lag $\ell$, pair $x[n]$ with $y[n+\ell]$. For lengths
$N_x,N_y$ the feasible lags are $1-N_x$ through $N_y-1$. Use

$$
I_\ell=[\max(0,-\ell),\,\min(N_x,N_y-\ell)),\qquad
R_\ell=\sum_{n\in I_\ell} x[n] y[n+\ell].
$$

The paired measurement interval is $I_\ell+\ell$. With capture starts
$s_x,s_y$, the clock delay is $d=s_y-s_x+\ell$ and the time is $d/f_s$.
Positive $d$ means the measurement is later. Translate the inclusive
clock search range into local lags before intersecting it with the
feasible range. Report the requested and evaluated bounds. Swapping
roles reflects the real-valued curve and negates the delay.

## Score and gates

Use $m=\lvert I_\ell\rvert$, $A_x=\sum x$, $A_y=\sum y$, $P_x=\sum x^2$,
and $P_y=\sum y^2$ on the same pairs at that lag.

| Mode | Score |
| --- | --- |
| Raw | $R_\ell$, in product units. Gain, DC, and overlap affect it. |
| Mean product | $R_\ell/m$, in product units. The divisor accounts for the pair count. |
| Overlap cosine | $R_\ell/\sqrt{P_xP_y}$. Dimensionless. DC remains in the score. |
| Overlap Pearson | $(mR_\ell-A_xA_y)/\sqrt{(mP_x-A_x^2)(mP_y-A_y^2)}$. Dimensionless. Centers each overlap. |

Set a minimum pair count and optional per-channel power floors. Use
$P_x/m$ and $P_y/m$ for uncentered scores. For Pearson use
$(mP_x-A_x^2)/m^2$ and the equivalent for $y$. Each power must be
positive and meet its floor for peak selection. A zero denominator
makes a normalized score unavailable. With positive powers a zero
cross term is a measured zero. Retain the support and any defined
score for ineligible rows.

One pair can give unit-magnitude cosine. Two varying pairs can give
unit-magnitude Pearson. Set the gate based on the stimulus. For fixed
support, crop the reference to an interval included at every tested
lag. Keep the original sample start and add measurement guard time.
[Zero-lag stereo correlation](../../audio-stereo-correlation/SKILL.md) ·
[Numerical stability](../../audio-numerical-stability/SKILL.md)

## Interpret the peak

Use the largest positive eligible score for a known same-polarity
path. For unknown polarity rank absolute scores and retain the
original sign. Report all top ties and the next distinct score's
lags. Flag a top peak at an evaluated search edge. Use signal-specific
uncertainty to judge whether competing peaks can be resolved.

Repeated signals can give several supported delays. A strong
reflection can outrank the direct path. Compare a distinctive,
finite probe before and after adding a known delay. Check repeated
captures and document the taps that determine a loopback or
round-trip measurement. Track the offset across observations when
drift is plausible.
[Measurement provenance](../../audio-analysis-provenance/SKILL.md) ·
[Research and diagnostic fixtures](https://github.com/Kisuul/KestrelGaming/blob/f80718da04cb224ed45c8aeba496fb89089f282a/memory/projects/kisuul/kestrelgaming/handoffs/2026-11-21-audio-cross-correlation-research-r01.md)

## Verify FFT and refinements

For an FFT comparison of the raw linear sum, pad both arrays to
$L\ge N_x+N_y-1$. Invert $\overline{X[k]}Y[k]$ and read each feasible
lag at $\ell\bmod L$. Use the inverse normalization of the chosen DFT.
Keep complex products intact with the real inverse's conjugate
reconstruction. For per-lag normalized scores, use the same original
overlap for their norms or centered moments. Compare the complete
raw curve against the direct reference.
[Correlation theorem](https://www.dsprelated.com/freebooks/mdft/Correlation_Theorem.html) ·
[SciPy correlation argument order](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.signal.correlate.html) ·
[Cross-spectrum convention](../../audio-phase-coherence/references/PHASE_COHERENCE_CONTRACT.md#welch-profile)

For an isolated maximum with two eligible neighbors, use three
scores $q_-,q_0,q_+$. Negate all three for an inverted winner. A
concave parabolic fit gives $\delta=(q_--q_+)/[2(q_--2q_0+q_+)]$.
Check that the vertex remains inside the fitted and searched support.
Verify bias against known offsets and bandwidths.

GCC-PHAT uses $C[k]/\lvert C[k]\rvert$ on retained nonzero bins.
Record the mask, enforce conjugate symmetry for real signals, and
compare with the unweighted curve. Excluded bins contribute zero.
An empty mask gives insufficient evidence. The weighting can favor
a different band and change the winning delay.
[Fractional and weighting fixtures](../../../tests/fixtures/AUDIO_CROSS_CORRELATION_GOLDENS.md)

## Offline reference

Put the `scripts` directories of `audio-oscilloscope`,
`audio-stereo-correlation`, and `audio-cross-correlation` on the
module search path. Pass two `CaptureWindow` values, a
`LagProfile(delay_bounds, minimum_pairs, ...)`, and explicit channel
IDs to `correlate_captures`. Both captures must share clock domain,
epoch ID, origin, and rate. Each has at most 1,024 samples per channel.

Use `raw`, `mean_product`, `cosine`, or `pearson` with the
`positive` or `absolute` peak rule. The curve carries exact powers,
raw sums, and time coordinates. A normalized score's `rank_value`
is the signed squared ratio, so ranking uses exact order. Its
`value` rounds the coefficient to binary64 with ties to even and
its `status` records exact or rounded zero and endpoints. Raw and
mean-product values remain rational.

Each row checks pair count, zero power, and the two floors in that
order. Result status distinguishes `empty_search`, `no_eligible_peak`,
`ambiguous`, and `selected`. `peaks` and `next_best` hold the
top and second distinct rank groups in ascending delay order.
`on_search_edge` checks top peaks against the evaluated bounds.
