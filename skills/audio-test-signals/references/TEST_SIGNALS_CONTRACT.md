# Audio test signal contract

[Stimulus](#choose-the-stimulus) · [Clock](#support-and-phase) ·
[Levels](#multitone-levels) · [Sweeps](#logarithmic-sweeps) ·
[Reference](#bounded-reference)

## Choose the stimulus

| Question | Stimulus and check |
| --- | --- |
| Does the analyzer recover scale? | Put a tone on an interior bin of the declared aperture. Check amplitude and RMS. Move the tone off bin to check leakage. |
| Where is the response? | Place a signed impulse at a known integer offset. Capture its leading interval and full response. Verify delay and polarity with a known filter. |
| Do tones interact? | Use distinct frequencies and known amplitude and phase. Choose the aperture and frequency spacing so the expected products can be resolved. |
| How does response vary with frequency? | Use a sweep with a declared excitation band. Verify the transfer method on a known filter. |
| How does the analyzer handle silence or noise? | Use a declared zero signal or a seeded noise fixture. Record the noise level, distribution, and bandwidth. Keep gaps in the capture provenance. |

Use the shared fixture bank for short portable cases. For
noise, retain the seed, generator version, and realized
samples. Report the measured level of the finite record.
Use distributional expectations when testing noise
statistics over repeated records.
[Fixture contract](../../audio-dsp-test-fixtures/references/FIXTURE_CONTRACT.md)

## Support and phase

Declare a sample epoch, exact rate $f_s$, channel order,
measurement tap, and units. Use an active start $s$ and
$N$ active sample frames on $[s,s+N)$. Express guards as
leading and trailing counts of generated zero frames.
Keep guard support separate from active support and from
missing observed input. Preserve the generated PCM and
track any fade, edit, resampling, or physical playback
that changes the signal delivered to the analyzer.
[Sample clock](../../audio-timebase-sync/references/TIMEBASE_CONTRACT.md) ·
[Signal provenance](../../audio-analysis-provenance/references/PROVENANCE_CONTRACT.md)

For a tone, compute $j=n-s$ with integer sample
coordinates. With exact $p/q=f/f_s$ cycles per sample,
reduce $jp$ modulo $q$ and combine it with the exact
initial phase in turns. Convert the resulting reduced
angle to radians. Keep the original $s$ and $N$ for all
subspan renders. A deliberate restart needs its own
phase anchor.

For a rectangular analysis aperture of $N$ samples, set
$f=kf_s/N$ with integer $k$ for a coherent tone. With
$0<2k<N$, RMS is $|A|/\sqrt{2}$. The observed peak can
depend on phase. A burst, fade, or different span changes
the applicable spectrum. Test an off-bin example under
the same aperture and compare the total power and its
distribution across bins.
[FFT calibration](../../audio-fft-spectrum/references/FFT_CALIBRATION.md) ·
[Coherent sampling](https://www.analog.com/en/resources/technical-articles/coherent-sampling-vs-window-sampling.html)

Use phase $\phi$ in radians. At DC, the value is
$A\sin\phi$. At $f=f_s/2$, the value is $(-1)^j A\sin\phi$.
A zero-phase sine gives digital zeros at both endpoints.
The even-length Nyquist bin and the DC
bin have one-sided peak scale $1/N$ with a rectangular
window. Use $2/N$ for interior bins, including the highest
bin of an odd transform.

## Multitone levels

For each channel with DC level $d$, use
$|d|+\sum_i |A_i|$ as a conservative peak bound on the
declared components. For distinct coherent interior tones,
mean square in the rectangular aperture is
$d^2+\sum_i A_i^2/2$. Correlated tones at the same frequency
need their combined phase and amplitude. Measure sample
peak as well as RMS. The same frequencies and RMS can give
different peaks when phases change.

The reference stores amplitude coefficients as finite
binary64 values. It sums their absolute represented
values exactly before applying an optional inclusive
peak limit. Set the gains explicitly when the bound
exceeds the planned headroom. The bound includes impulse
coefficients even when their offsets differ. Measure each
channel's peak over the rendered interval. Keep the
individual channels available when opposite polarities
cancel in a downmix.

## Logarithmic sweeps

Let $t=j/f_s$, $T=N/f_s$, and $g=\log(f_1/f_0)$.
Choose positive endpoints below Nyquist and qualify the
excited band for the measurement. The phase in radians
and instantaneous frequency are

$$
\phi(t)=\phi_0+2\pi f_0t\frac{\operatorname{expm1}(gt/T)}{gt/T},
\qquad
f(t)=f_0\exp(gt/T).
$$

Use `log1p` near equal endpoints and `expm1` for
$gt/T$ near zero. The ratio has limit one at zero. The
equal-endpoint case renders the corresponding tone. For
an ascending sweep the reference factors out the positive
exponential and evaluates it with the end frequency
anchor. This keeps the exponential argument nonpositive.
The last rendered sample is at $T-1/f_s$. The endpoint
frequency $f_1$ is defined at the exclusive boundary $T$.
The phase uses the active span even when the returned
record includes guards.
[SciPy chirp phase convention](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.signal.chirp.html)

Specify the taper or use the unfaded active span. Check the
actual spectrum because the finite aperture affects the
usable excitation band. Keep the realized excitation and
matching inverse or transfer model. Capture the response
through its tail. For a known linear FIR, compare the
complex quotient $Y/X$ to the filter using an adequate
transform length and bins with adequate excitation.
The fixture shows how truncation biases that comparison.

For harmonic-response separation, use a declared
exponential sweep and matched inverse. Verify the
assumed nonlinear model, order timing, and separation
with controlled signals before using captured data.
Measure actual level, timing, and response at the
target tap when the acceptance claim concerns playback.
[Farina's swept-sine method](https://angelofarina.it/Public/Papers/134-AES00.PDF) ·
[Müller and Massarani](https://publications.rwth-aachen.de/record/192865)

## Bounded reference

| Entry point | Contract |
| --- | --- |
| `Tone` | Set exact nonnegative Hz up to Nyquist, a signed amplitude, and exact initial phase in turns. |
| `Impulse` | Set an integer offset inside the active span and a signed amplitude. |
| `LogSweep` | Set positive exact start and end Hz below Nyquist, amplitude, and initial phase in turns. Normalized endpoints must be representable as positive binary64 values. |
| `ChannelSignal` | Supply the component tuple and optional active DC level. Its `peak_bound` gives the exact conservative bound. |
| `SignalPlan` | Supply a `ScopeEpoch`, active start and count, ordered channel recipes, guards, and optional peak limit. |
| `render_signal` | Render the whole planned record or an absolute subspan. Retain the original plan, generator identity, half-open block support, planar samples, and per-channel sample peaks. |

Use integers or rationals for frequency and phase and
integer sample boundaries. Amplitudes and limit values
accept integers and finite binary64 numbers. The reference
accepts up to 65,536 frames including guards, up to eight
channels per epoch, and up to 16 components per channel.
Its active span uses abrupt boundaries. Apply any taper
as a declared separate operation with its own checks.

Compare block positions and same-runtime subspan replays
exactly. Use numerical tolerances and separate oracles for
trigonometric values and spectral comparisons.
[Reference](../scripts/reference_test_signals.py) ·
[Frozen fixture values](../../../tests/fixtures/AUDIO_TEST_SIGNALS_GOLDENS.md) ·
[Executable checks](../../../tests/test_audio_test_signals_reference.py)
