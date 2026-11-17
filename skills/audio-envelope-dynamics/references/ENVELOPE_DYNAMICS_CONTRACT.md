# Envelope dynamics contract — bounded educational reference

## Scope and provenance

The reference implements a causal discrete-time envelope *model* over already decoded normalized PCM, not a standardized metering instrument or a realtime dynamics processor. Its amplitude and RMS followers are stateful, sample-clocked and channel-aware. The gain-control demonstrator operates on requested positive attenuation **in dB**, separate from PCM detection and separate from audio gain application. No sidechain delay, gating hysteresis, lookahead, makeup gain, oversampling, audio output, true-peak limiter or hardware calibration is implemented.

There is no established IEC/EBU/ITU standard prescribing the attack and release time convention of every generic envelope follower. Adjacent IEC standards cover [volume indicators](https://webstore.iec.ch/en/publication/1216) and [peak programme meters](https://webstore.iec.ch/en/publication/1205). The [2012 AES compressor tutorial](https://aes.org/publications/elibrary/elibrary-page/?id=16354) analyzes several architectures; [JUCE BallisticsFilter](https://docs.juce.com/master/classjuce_1_1dsp_1_1BallisticsFilter.html), [FFmpeg compand](https://ffmpeg.org/ffmpeg-filters.html) and [W3C DynamicsCompressorNode](https://www.w3.org/TR/2026/WD-webaudio-1.1-20260922/) illustrate differing timing/transfer conventions. These documents do not certify this reference. See the [skill](../SKILL.md) for routing.

## Detector targets, state and time constants

- Input samples `x_i[n]` are signed, finite binary64-compatible PCM amplitudes relative to a declared nominal digital full-scale amplitude of one. Headroom greater than one is permitted.
- Peak target `d_i[n] = |x_i[n]|`. A raw *signed* one-pole filter is not this envelope.
- RMS/mean-square target `p_i[n] = x_i[n]**2`. Exponential RMS state is `e_i[n] = sqrt(q_i[n])`, where `q_i[n]` obeys the energy-domain one-pole equation. It is **not** finite-window RMS.
- `max` linking computes `d[n] = max_i |x_i[n]|` and processes one shared state. When `detector=rms`, this represents exponential RMS of the **maximum instantaneous channel power**, **not** sum-channel or average-channel RMS. `independent` maintains one state for every channel.
- Both detectors include DC, preserve polarity invariance and have no leading or trailing padding.

The canonical convention, `one_e`, defines a **residual-error** time constant `tau` in seconds. For a sample rate `fs` in Hz:

```
alpha = exp(-1/(fs*tau))
beta = 1 - alpha = -expm1(-1/(fs*tau))
```

For `tau=0`, `beta=1` and the state tracks its target exactly. At each sample, use attack `beta_a` when `d > e_previous`, release `beta_r` when `d < e_previous`, or unchanged `e` and phase `steady` when equal. `beta` is calculated once per epoch and is applied at every input sample. It is not a frame-based relaxation coefficient.

For a peak follower:

```
e_new = e_old + beta*(d - e_old)
```

For the RMS follower, attack and release compare the **magnitude** `d=|x|` to the old RMS amplitude `e_old`, and the mathematical energy equation is:

```
q_new = (1-beta)*q_old + beta*d*d
```

The reference evaluates its square root using `hypot(sqrt(1-beta)*e_old, sqrt(beta)*d)` to avoid overflow from squaring finite, large PCM samples. With `beta=1`, the reference assigns `d` directly to avoid unnecessary last-bit rounding. Inputs are never silently denormal-flushed; binary64 rounding can nevertheless make very small nonzero updates have no observable effect.

Alternative **named** conventions use the same recurrence but a different exponent factor `c`:

| Convention | Meaning of `time_seconds=T` | `c` in `alpha=exp(-c/(fs*T))` |
| --- | --- | --- |
| `one_e` | Step error decays to `1/e` at `T`; rise is 63.212% | 1 |
| `rise_90` | Step rises 90% by `T` | `ln(10)` |
| `residual_minus60_db` | Step amplitude error reaches −60 dB, i.e. 0.001, at `T` | `ln(1000)` |

The W3C's compressor describes the time to change *gain* by 10 dB, and JUCE uses a separate coefficient law. Neither is interchangeable with Kestrel's canonical time parameter without a full design/topology comparison.

### Analytic checkpoints

For a constant target `A` and zero initial envelope, an **amplitude peak** follower has `e[n] = A*(1-alpha**(n+1))`; on release from `A` to zero it has `e[n] = A*alpha**(n+1)`. A constant target `A` in RMS mode gives `r[n] = A*sqrt(1-alpha**(n+1))`, assuming only attack samples. The first update takes place at the first sample index `origin`, so a 1000 Hz reference with 100 ms `one_e` attack reaches the 1/e residual checkpoint after **100 processed samples**, at index `origin+99`.

For abrupt changes that cross the old state, re-evaluate attack versus release *each sample*. A branch choice cannot be inferred from `x[n]-x[n-1]`. A zero target following a high envelope uses release, even if the input value is negative or a DC component is present.

## Compressor and expander gain computer

The pure hard-knee functions accept detector **levels in dBFS** (`L`), a finite dBFS threshold (`T`) and a finite ratio (`R >= 1`). With amplitude `A >= 0`, `L=20 log10(A)` and `A=0` is explicitly `-inf` dBFS. No display floor is used for threshold decisions.

- Compressor: `G_c=0` for `L<=T`; otherwise `G_c=-(1-1/R)*(L-T)` dB. At `R=1` the gain request is zero. This is a feed-forward **static** map.
- Downward expander: `G_e=0` for `L>=T`; otherwise `G_e=-(R-1)*(T-L)` dB. This defines the ratio as the *output/input dB slope below threshold*, not an unspecified `1:R` control. A true silent level asks for `-inf` dB gain when `R>1`.
- Nonfinite arithmetic in the finite branch raises an error instead of manufacturing an infinite result; `-inf` silence is an explicit sentinel only in these pure gain maps. A gain-smoothing stream **does not accept infinite requested attenuation**. The caller must define a finite attenuation floor or an explicit mute state before sending such a request. That is a design choice with audible consequences.

`GainReductionStream` accepts finite **positive attenuation depth** `D=-G` in dB (nonnegative), and smooths it with the same `one_e` family. Increasing `D` is the attack phase, decreasing `D` is the release phase. It emits `applied_reduction_db=D_smooth`, `gain_db=-D_smooth`, `gain_linear=10**(-D_smooth/20)`. Applying gain is out of scope. Smoothing the detector amplitude before the static dB curve is **not equivalent** to smoothing a gain request afterward. A simple static limiter curve or a soft knee does not certify a reconstructed true-peak ceiling. The demo has no lookahead or added processing latency because it produces no audio stream.

## Input API, clock and failure contract

`EnvelopeConfig(sample_rate_hz, channel_labels, source_tap, detector, link, attack_seconds, release_seconds, convention='one_e', initial_envelope=0)` accepts 1–32 unique, nonblank channel names; positive integer `fs` up to 1 GHz; valid nonnegative finite times and initial state; `peak` or `rms`; and `independent` or `max`. `EnvelopeStream(config, epoch_id, start_sample)` processes one sample per channel for each integer frame. `push(start_sample, planes, epoch_id)` accepts one equal-length tuple/list for each labeled channel and returns `EnvelopeFrame(sample_index, detector_targets, envelopes, phases)` per processed frame. Empty chunks yield an empty tuple and leave state/cursor unchanged. All samples must be finite; NaN/Inf are rejected even when upstream format permits a larger-than-one finite value.

`GainReductionStream(sample_rate_hz, attack_seconds, release_seconds, epoch_id, start_sample, convention)` is a separate sample-indexed stateful stream. `push(start_sample, requested_reduction_db, epoch_id)` returns `GainFrame(sample_index, requested_reduction_db, applied_reduction_db, gain_db, gain_linear, phase)` per sample.

- All sample coordinates are exact Python integers, including start positions beyond `2**53`. A processed chunk occupies `[start, start+frames)`. Each output records its corresponding input sample index. The first element belongs to `start`, not `start+1`.
- Every push requires exact continuity and its declared epoch. Gaps, overlaps, seeks and changed PCM context require an explicit `reset_epoch` with a new never-before-used nonblank ID. Envelope changes of detector, link, time convention, sample rate, channel labels or tap require new `EnvelopeConfig` in a fresh epoch. The gain follower's time parameters are fixed for its lifetime; create a new gain follower to change them.
- All validation and arithmetic run against a working copy; on any failure the original state and clock remain unchanged. Rejected epochs are not recorded as used. Output and state changes commit only after all frames succeed.
- Inputs and output use finite Python floats. The chosen time weight is computed with `expm1`; positive `tau` for which `beta` underflows to zero is rejected. A finite target may still yield zero observable update due to final binary64 rounding. This is not a meter accuracy or a perceptual guarantee.
- The reference validates and allocates on every callback. Large chunks use memory proportional to `channels × frames`; per-sample returned tuples are not suitable for a real-time audio callback. Audio application, buffering, lookahead, hardware clocks and host latency reporting require a separate integration design.

## Independent fixture and review plan

The [golden ledger](../../../tests/fixtures/AUDIO_ENVELOPE_DYNAMICS_GOLDENS.md) fixes analytic constants independently of implementation outputs. [Targeted tests](../../../tests/test_audio_envelope_dynamics_reference.py) cover step/release, time conversions, high precision Decimal energy recurrence, huge and tiny binary64 PCM, polarity/DC, stereo-link semantics, exact sample positions beyond `2**53`, chunk equivalence, reset and atomic rejection, compressor/expander knee and gain control. CI tests are mathematical **contract** checks, not IEC/EBU conformance tests.

Adversarial review should prioritize coefficient precision at huge `tau`, equality/near-equality attack/release branching, `beta=1` exact assignment, near-maximum RMS energy without intermediate `x*x`, channel permutation and anti-phase, stream operation after late invalid samples, and negative-gain/mute semantics. The test suite must not calculate its own expected outputs by calling the reference algorithm.
