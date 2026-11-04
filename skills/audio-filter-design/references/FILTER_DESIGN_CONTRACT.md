# FIR/IIR filter design: exact conventions, numerical limits and verification contract

This reference contract belongs to [audio-filter-design](../SKILL.md). The [Python reference](../scripts/reference_filter_design.py) is a **bounded equal-rate discrete-time numerical oracle**, not a realtime engine, standards meter, room EQ optimizer, or arbitrary-order filter design library. Physical acoustic and psychoacoustic success are separate claims.

## 1. Required engineering specification

Declare source/output sample rate F_s (Hz), audio sample amplitude reference, channel identity, target passband(s) and stopband(s) as numeric frequency intervals in **Hz**, allowed passband deviation from nominal 0 dB, minimum stopband attenuation, transition widths, phase and group delay/latency requirements, coefficient/runtime precision, intended environment and failure policy. For peaking EQ, the passband target need not be 0 dB: **do not use the unity-band checker as a peaking-EQ acceptance test**.

The exact rate and cutoff API accepts Python `Fraction` in 2,000–384,000 Hz, and each cutoff must satisfy **0 < cutoff < F_s/2**. FIR edges must be an ascending tuple of one (LP/HP) or two (BP/BS). Requiring a rational *input specification* does not make floating coefficients or actual hardware clocks exact. The reference accepts only 5–129 **odd** FIR taps; no Type-II FIR with a Nyquist zero is silently generated. The FIR uses **Hann, Hamming or Blackman** windows. No arbitrary specification synthesis, Remez/minimax design, analog prototype design, automated order search, min-phase conversion or generalized FIR equalizer is in scope.

## 2. FIR reference mathematics

For sample rate F_s, desired ideal lowpass cutoff f_c and relative index `k=n−(N−1)/2`, use

`LP(k;f_c) = 2 f_c/F_s · sinc(2(f_c/F_s)k)` with `sinc(t)=sin(pi·t)/(pi·t)`, `sinc(0)=1`.

Construct ideal filters **before** windowing:

- Lowpass: `LP(k;f_c)`.
- Highpass: `δ[k] − LP(k;f_c)`.
- Bandpass: `LP(k;f_high) − LP(k;f_low)`.
- Bandstop: `δ[k] − LP(k;f_high) + LP(k;f_low)`.

Multiply by the explicitly selected symmetric **N-point window**, then scale so the designed passband reference has **unit amplitude**: DC for LP/BS, centered-phase Nyquist for HP, and band midpoint `(f_low+f_high)/2` for BP. Copy symmetric coefficient pairs exactly; enforce odd-tap linear-phase Type-I symmetry. The `FIRDesign` reports **causal group delay exactly `(N−1)/2` sample intervals** away from frequency-response nulls, and `delay_seconds = delay_samples/F_s`. Unlike the centered acausal sample-rate-conversion oracle, this FIR implementation outputs immediately but has **nonzero phase delay and startup transient**. A finite-window FIR can have stopband leakage; normalizing its Nyquist magnitude does not force an exactly zero DC response for HP.

The windowed-sinc cutoff is an **approximate half-amplitude, −6.0206 dB** crossover for a sufficiently resolved transition. It is not the -3.0103 dB Butterworth Q corner. Short windows and edges too near endpoints can shift its actual crossing; no continuous-band tolerance is guaranteed by design.

## 3. Biquads, poles and normalized IIR state

The [W3C Audio EQ Cookbook](https://www.w3.org/TR/audio-eq-cookbook/) is a 2021 **Working Group Note** adapted from Robert Bristow-Johnson; our subset implements 2nd-order lowpass, highpass, notch and peaking EQ using the normalized Q formulation. It is **not** the same as octave-bandwidth parameterization. Define `ω0=2π f0/F_s`, `c=cos(ω0)`, `alpha=sin(ω0)/(2Q)` and for peaking `A=10^(gain_dB/40)`.

| Kind | Unnormalized numerator `(b0,b1,b2)` | Denominator `(a0,a1,a2)` |
| --- | --- | --- |
| Lowpass | `((1−c)/2, 1−c, (1−c)/2)` | `(1+alpha, −2c, 1−alpha)` |
| Highpass | `((1+c)/2, −(1+c), (1+c)/2)` | `(1+alpha, −2c, 1−alpha)` |
| Notch | `(1, −2c, 1)` | `(1+alpha, −2c, 1−alpha)` |
| Peaking | `(1+alpha A, −2c, 1−alpha A)` | `(1+alpha/A, −2c, 1−alpha/A)` |

Normalize **all five remaining coefficients** by `a0` and use `H(z)=(b0+b1 z^-1+b2 z^-2)/(1+a1 z^-1+a2 z^-2)`. The stable denominator poles are the solutions to `z²+a1 z+a2=0`. Reject any pole with magnitude ≥ `1−1e−10` as a conservative finite-precision reference rule, not a general theorem guaranteeing float stability under all parameters. Q must be 0.2–20; peaking gain −24 to +24 dB. For isolated Q=1/√2 LP/HP, `|H(f0)|=1/√2`, i.e. **−3.0103 dB**; for other Q values resonance can exceed 0 dB. For peaking EQ `H(f0)` targets the specified dB gain. A notch has a response zero at f0: phase/group delay at the null are *undefined*.

For up to **four** independently stable SOS in a `SOSDesign`, response multiplies section-by-section. The small Python reference uses **transposed direct-form II** per-channel sections, not a high-order direct-form polynomial. SOS ordering, headroom between stages, denormal behavior, fixed-point saturation and time-varying coefficients require independent production analysis.

Nearest-even coefficient quantization to a binary fractional-bit grid (4–30 bits) is an **illustration**; after rounding, we re-evaluate pole stability. Passing pole radius tests does not prove fixed-point overflow, limit-cycle freedom, perceptual equivalence, or correct coefficient automation. If rounding destabilizes poles or produces too small a margin, the reference rejects it.

## 4. Frequency response, group delay and sampled acceptance

All frequency arguments passed to `frequency_response` are exact rational Hz in `[0,F_s/2]`; internally they are converted to floating radian/sample `ω=2π f/F_s`. Complex response uses `z^-1=cos(ω)−i sin(ω)` and multiplies SOS transfer functions. **Magnitude dB is `20 log10(|H|)`**, not the `10 log10` power convention. The local group-delay estimate uses symmetric phase difference `−arg(H(ω+h)/H(ω−h))/(2h)` and refuses DC, Nyquist or near-zero magnitude; for a symmetric FIR with no response zero it recovers `(N−1)/2` samples. A finite phase slope is not constant-delay proof for an arbitrary IIR.

`sampled_band_check` takes one to four explicitly bounded passband and stopband intervals, each evaluated on **3–1025 equally spaced points** inclusive of endpoints. It returns min/max passband **0-dB deviation**, worst stopband dB, the actual number of samples checked, and a boolean `meets_sampled_targets`. A passing boolean proves only those **finite grid points**, not a bound between points or robustness under varying sample rates, parameter drift, coefficient quantization, or input precision. Do not report the result as rigorous all-frequency verification. For special amplitude targets or multimode EQ, compute explicit per-frequency acceptance criteria instead.

## 5. Streaming and failure contract

`FilterStream(plan,epoch_id,origin_sample,channels)` takes one to eight planar float channels. Each `push(start_sample, planes)` must have the exact expected **integer** input origin, **1–256 frames per channel**, equal plane lengths and finite real samples; it outputs exactly the same frame count at the same rate and epoch. FIR history is zero-initialized; IIR state is two scalars per SOS and per channel. The reference computes with **temporary cloned state**; if any channel or internal section overflows, rejects without advancing cursor, accepted block count or stored state. The reference **never clamps values over ±1**, although it reports over-reference samples when ±1 is the chosen reference; an over-reference value is not itself proof of source clipping.

Seek, gap, overlap, rate change, layout change, filter change or other stream discontinuity requires a **new, never reused epoch ID** via `reset_epoch`, which clears history/state. Silent pauses do not advance the cursor; the oracle relies on truthful source indices and does not recover missing samples. No zero-phase filtfilt, state interpolation, crossfade, sample-rate conversion or real device clock synchronization is supplied. Early causal output samples contain filter startup transient; phase delay does not automatically retime sample coordinates. Neither repeated startup zeros nor filter group delay can be assumed to be actual device latency.

## 6. Evidence matrix and limitations

| Claim tested | Evidence | Important limitation |
| --- | --- | --- |
| Ideal FIR prototypes, chosen windows, scaling | Symmetric taps, DC/Nyquist and band center; frozen SciPy `firwin` examples for 4 filter families | Windowing does not guarantee ideal stopbands or all-cutoff accuracy |
| Distinct corner conventions | FIR ~−6 dB; Butterworth biquad Q=1/√2 at ~−3 dB | Specific small fixtures; actual topology matters |
| IIR formula and stability | Frozen SciPy Butterworth coefficients, analytic notch/peaking gain, exact poles, rejecting unit-circle and quantized failures | Does not establish robustness of every dtype/backend |
| Response and delay | Complex response, linear-phase FIR delay, IIR variable delay, null rejection and sampled-band pass/fail | Finite sampled grid, no global worst-case certification |
| Causal filtering | Impulse, step, stereo state separation and chunk partition invariance | Tiny Python test reference, not callback realtime benchmark |
| Failure semantics | Bad arguments, gaps, overlaps, NaN/Inf, overflow and reconfiguration reject atomically | Depends on source-provided timestamps; no hardware clock validation |
| External verification | Frozen NumPy 2.3.5 / SciPy 1.17.0 values and separately runnable seeded SciPy differential | Shared design family, independent arithmetic backend; no optimality proof |

Reference constraints: sample rate 2–384 kHz, odd FIR 5–129 taps, ≤4 SOS, 1–8 planar channels, ≤256 frames/callback; no runtime dependency beyond Python standard library. Later integration tests must measure the actual audio engine's frequency response, pass/stopband density and max deviation, phase/ringing, coefficient change behavior, peak headroom, CPU/jitter/latency under load, device channel ordering and realtime fault handling. **Do not promote bounded numerical validation to production or normative instrument conformance.**

See [frozen independent test provenance](../../../tests/fixtures/AUDIO_FILTER_DESIGN_EXTERNAL_GOLDENS.md), [37 standard-library tests](../../../tests/test_audio_filter_design_reference.py), and the [optional live SciPy differential](../scripts/check_scipy_filter_design.py). Cross-reference [audio-resampling](../../audio-resampling/SKILL.md) for multirate filtering and [math numerical analysis](../../math-numerical-analysis/SKILL.md) for extreme finite arithmetic.
