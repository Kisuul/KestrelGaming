---
name: audio-resampling
description: Design, audit and verify rational audio sample-rate conversion with explicit anti-alias FIR response, exact output time coordinates, group delay, boundary and stream epoch policy, independently checked fixtures and declared implementation limits.
---

# Audio resampling — change the sample grid without inventing sound

## When to activate

Load for sample-rate conversion (SRC), anti-alias filtering, interpolation or decimation, capture-to-playback rate differences, polyphase FIR choices, resampler phase, group delay or callback chunk consistency. This skill owns audio SRC semantics. Load [audio-timebase-sync](../audio-timebase-sync/SKILL.md) to relate source/output sample epochs and clock domains, [audio-sample-formats](../audio-sample-formats/SKILL.md) only for quantization or PCM conversion, and [audio-dsp-test-fixtures](../audio-dsp-test-fixtures/SKILL.md) for repeatable signals. Use [math-dimensional-analysis](../math-dimensional-analysis/SKILL.md) for new rate/unit problems, [math-numerical-analysis](../math-numerical-analysis/SKILL.md) for finite-arithmetic error, and [math-verification](../math-verification/SKILL.md) for oracle independence. Do not load unrelated math skills automatically.

Read the [resampling and stream contract](references/RESAMPLING_CONTRACT.md) and [independent golden-vector provenance](../../tests/fixtures/AUDIO_RESAMPLING_EXTERNAL_GOLDENS.md).

## Procedure

1. **Define the stream, not just the ratio.** Record origin and epoch, source/destination rates as exact positive rationals in Hz, number and labels of channels, input sample representation, processing tap, output clock domain and what conversion should mean. SRC changes discrete-time sampling density; it is *not* time stretching, pitch shifting, device clock drift estimation, channel remapping or sample-format conversion. Nominal rates do not establish hardware clock lock.
2. **Reduce the exact ratio.** Let destination/source=L/M in lowest integer terms. 44,100→48,000 Hz is L=160, M=147; reverse is L=147, M=160. For N consecutive source frames this reference returns ceil(NL/M) output frames; frame m has source-relative coordinate mM/L. An output sample coordinate is not the same unit as an input coordinate. Never compute cumulative phase using floating-point seconds or reset phase at arbitrary callback boundaries.
3. **Choose and characterize the anti-alias filter.** Upsample by L, low-pass to the *lower* of source/destination Nyquist, then decimate by M. Suppress images and aliases; no bare linear interpolation or drop-every-other-sample shortcut. This educational reference uses an odd symmetric Kaiser-windowed sinc, beta=5, half-length H=10 max(L,M) on the intermediate grid, cutoff 1/max(L,M) relative to that grid's Nyquist, with tap sum normalized to L. It is a finite **design choice**, not a universal accuracy/performance profile. Measure passband ripple, transition and stopband response against each intended sample-rate pair.
4. **Account for phase and delay.** Linear-phase filter delay is H/L source sample intervals or H/M destination intervals. The reference produces centered, timestamp-compensated output: output m is labelled at mM/L of the input epoch. However, this **requires future samples**: zero timestamp shift is not zero buffering latency. Boundary-filtered output can differ from the value of the first input sample despite sharing its nominal time coordinate.
5. **Declare boundaries.** Offline reference adopts zero extension outside its finite epoch and exposes per-output `boundary_affected` flags when a filter tap requires nonexistent source samples. A streaming input block is *not* end-of-stream; hold outputs until their full future support arrives. Only explicit `finalize()` permits right-edge zero extension. A boundary flag never proves silence was observed.
6. **Protect the stream epoch.** `push(start_sample, planar_samples)` must receive contiguous integer source coordinates; gaps, overlaps/replays, channel mismatch, invalid/nonfinite data, numeric overflow and reference bounds reject atomically. Seek, rate or channel reconfiguration requires a new, never-reused epoch ID and an explicit destination origin. A paused source with no blocks cannot establish playback-device elapsed time or sample continuity.
7. **Keep amplitude and channels honest.** Resampling can produce overshoots above normalized full scale. Do not silently clamp, downmix antiphase channels, reinterpret PCM normalization or infer speaker assignment. Dither, quantization, remapping, limiting and codec transport belong to separate domain procedures.
8. **Use independent evidence.** Run [the bounded standard-library reference](scripts/reference_resampling.py) and [22 analytic/metamorphic/regression tests](../../tests/test_audio_resampling_reference.py): rational clock alignment, impulse, DC, 2k passband and 18k stopband decimation checks, antiphase stereo, fragmented callbacks, atomic rejection and frozen SciPy vectors. Optionally run [the live SciPy differential harness](scripts/check_scipy_resampling.py) with pinned dependencies and seed. The reference and SciPy **share an intended filter design**; agreeing numerical outputs is not a proof of high-fidelity audio quality.
9. **Earn production readiness separately.** Profile the actual backend across supported rate/channel combinations, input overruns and missing samples, long-running phase, clock drift, CPU/latency, audible artifacts, resampler group delay and output device timing. Reference success is not measured host behavior, calibrated instrument performance or normative compliance.

## Verification commands

From the repository root:

```sh
python3 tools/validate_seed.py
python3 -m unittest discover -s tests -v
python3 skills/audio-resampling/scripts/check_scipy_resampling.py --seed 20261104 --cases 24
```

The first two are standard-library only. The last is **optional**, requiring separately installed SciPy and NumPy. Record which commands actually ran, the backend versions and the exact revision.

## Acceptance gate

Document source/destination rates and output origin; exact reduced L/M and phase; FIR/window/stopband assumptions; filter group delay and required lookahead; boundary/epoch/continuity policies; channel and numeric behavior; independently checked fixtures; known uncertainty and unverified integration. The provided oracle is limited to **1–256 source frames, ≤8 channels, reduced factors ≤320 and ≤4096 output frames**. It retains complete input epochs and is not an efficient production polyphase engine.

## Primary references

- [SciPy resample_poly](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.resample_poly.html) — rational up/down, centered FIR and boundary extension.
- [SciPy upfirdn](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.upfirdn.html) — FIR, polyphase structure and edge modes.
- [PortAudio timing guidelines](https://github.com/PortAudio/portaudio/wiki/BufferingLatencyAndTimingImplementationGuidelines) — callbacks and devices occupy different timing domains.
