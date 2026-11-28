# Paired audio transfer response

[Path](#path-and-support) · [Estimators](#estimator-choice) ·
[Qualification](#bin-qualification) · [Timing](#timing)

## Path and support

Measure a declared reference-to-response path. Record
both taps, channels, units, gains, clock, epoch, original
sample intervals, and time offsets. Pair complete windows
on the same clock. Keep complete segment starts, the
used interval, and the full capture interval. Restart
the analysis when a gap or clock change breaks the path.

Check the excitation in the band of interest. For an
impulse, capture the required response tail. For a sweep,
retain the emitted reference, matching inverse, and
well-conditioned band. A single supported coherent
probe can give $Y/X$. Repeat the measurement to establish
repeatability. Use one driven input at a time when the
stimulus cannot resolve a transfer matrix. Compare the
complex response and residual at another drive level or
time to check the linear, time-invariant path model.
[Test signals](../../audio-test-signals/SKILL.md) ·
[Transfer measurement with sweeps](https://publications.rwth-aachen.de/record/192865)

Pass a \`PhaseCoherenceAnalysis\` from the accepted paired
Welch reference to \`analyze_transfer_response\`. The
adapter retains that object and the original bin records.
Keep its window, hop, detrending, and exact rate. Use the
shared bound of 1,024 transform points and at most
262,144 sample-bin terms per channel. Fewer than two
complete segments give warm-up with an empty bin tuple.
[Paired capture and Welch calibration](../../audio-phase-coherence/references/PHASE_COHERENCE_CONTRACT.md#welch-profile)

## Estimator choice

Use the negative-exponent DFT and pooled products
$P_x=\langle X^*X\rangle$, $P_y=\langle Y^*Y\rangle$,
and $C=\langle X^*Y\rangle$. Apply the same segment
selection, real window, normalization, and nonnegative
weights to all three products. Divide the pooled
products.

$$
H_1=C/P_x,\qquad
H_2=P_y/C^*=P_y C/|C|^2,\qquad
\gamma^2=|C|^2/(P_xP_y).
$$

| Measurement model | Interpretation |
| --- | --- |
| Reliable input and uncorrelated additive output noise | At population level $C=HP_x$. H1 recovers the transfer. Extra output power can raise H2 magnitude. |
| Independent input measurement error with clean output | Measured input power includes the error. H1 magnitude is attenuated. H2 recovers the transfer at a nonzero cross denominator. |
| Noise on both taps, feedback, or path variation | Check the taps and use a model that describes the measured noise and variation. |

Where both estimates are nonzero, $H_1/H_2=\gamma^2$
and their phase is the phase of $C$. Check this identity
for consistency across the estimates. Check absolute
phase sign with a known quadrature or delay response.
Swapping input and output conjugates $C$ and interchanges
the reciprocal estimates on their common support.
[SciPy cross-spectrum convention](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.signal.csd.html) ·
[Siemens estimator assumptions](https://community.sw.siemens.com/articles/en_US/Knowledge/what-is-a-frequency-response-function-frf)

## Bin qualification

Keep the exact grid, auto and cross densities, coherence,
and energized-pair count for each bin. Report gain as
output units per input unit. Use $20\log_{10}|H|$ for
level relative to one unit of gain. Use the wrapped phase
in the source bin record when it is defined. The adapter
keeps real and imaginary gain components as fractions.
It scales the squared magnitude for dB. A nonzero
linear magnitude outside finite binary64 range is
unavailable. The exact components and dB remain
available. Reference and response unit labels describe
the supplied samples. Apply tap calibration before
forming the paired spectra.

| Bin evidence | Mathematical result and status |
| --- | --- |
| $P_x=0$ | Both estimates unavailable. Status \`unexcited\`. |
| $P_x>0$, $P_y=0$ | H1 is zero, with level $-\infty$ dB. H2, phase, and coherence are unavailable. Status \`zero_output\`. |
| $P_x,P_y>0$, $C=0$ | H1 is zero and coherence is zero. H2 and phase are unavailable. Status \`zero_cross\`. |
| $P_x,P_y>0$, $C\ne0$ | Both estimates exist. Apply the declared quality gates. |

The rows above identify measured spectral states. Check
the excitation and numerical error before assigning a
physical cause to a null. Cross cancellation between
energetic segments can give a zero H1 and positive output
power.

Use \`TransferQuality\` to declare reference and response
density floors, a minimum coherence, and a minimum number
of energized pairs. Density floors use the squared units
of the respective tap per Hz. After the spectral states,
check those two floors, energized pairs, and coherence
in that order. An H2 cross-density floor acts after the
common gates and compares the magnitude of $C$ in cross
units per Hz. Equality meets a floor. Keep raw estimates
when a gate rejects qualification.

The minimum energized-pair count defaults to two. One
nonzero paired observation can yield unity coherence when
the other complete segments have zero power. A segment
count or coherence value alone gives limited evidence.
Record overlap and the usable levels when making a
repeatability or confidence claim.
[Paired Welch interpretation](../../audio-phase-coherence/references/PHASE_COHERENCE_CONTRACT.md#interpret-the-estimate)

## Timing

A delayed copy by $d$ samples gives
$H[k]=A\exp(-j2\pi kd/N)$. Its delay contributes
negative phase slope. An output advance of $a$ samples
adds $2\pi f a/F_s$ to phase when the compared signal
support is retained. Keep \`output_advance_samples\` and
the original tap intervals as metadata. The adapter
reports the measured complex response on the supplied
alignment.

For a delay estimate, pass the chosen complex response
and bin qualification to the group-delay procedure.
Use the recorded advance as the already applied input
advance of the slope profile. Add it to the delay of
the advanced response to recover the original tap delay.
Supply adjacent-edge evidence, a phase-branch bound,
and an aperture. Break the aperture at gaps, rejected
bins, or nulls. Confirm a first arrival against the
impulse response and sample clock.
[Group-delay support and offset restoration](../../audio-group-delay/references/GROUP_DELAY_CONTRACT.md#sampled-transfer) ·
[Executable fixtures](../../../tests/fixtures/AUDIO_TRANSFER_RESPONSE_GOLDENS.md)
