---
name: audio-timebase-sync
description: Design and verify exact audio sample-frame clocks, frame interval timestamps, gaps/overlaps, explicit stream epochs, rational sample-rate conversions and separately labelled device/UI clock correlations without inventing continuity or precise hardware timing.
---

# Audio timebase synchronization — samples first, clocks explicitly

## Activate when

Use for sample-index timestamps, frame and hop positions, timestamp drift, callback chunk boundaries, capture-versus-playback timing, audio/UI synchronization, resampling time domains, seeks, gaps, resets and channel/rate reconfiguration. Use [audio-dsp-core](../audio-dsp-core/SKILL.md) for signal-path architecture, [audio-spectrogram-waterfall](../audio-spectrogram-waterfall/SKILL.md) for STFT window geometry, and [audio-dsp-test-fixtures](../audio-dsp-test-fixtures/SKILL.md) for repeatable chunk fixtures. Load [math-dimensional-analysis](../math-dimensional-analysis/SKILL.md) only for broader unit conversion or timebase questions, and [math-numerical-analysis](../math-numerical-analysis/SKILL.md) only for numeric precision limits.

Follow [the timebase and epoch contract](references/TIMEBASE_CONTRACT.md).

## Procedure

1. **Name every clock and its authority.** Distinguish input-sample capture position, decoded/media presentation position, post-resampler output-sample index, playback-device output time, stream callback invocation time, and UI/monotonic performance time. Record the measurement tap, clock domain, sample-rate numerator/denominator, origin/epoch identifier, channel layout and whether a hardware timestamp is an estimate. Never silently treat these clocks as identical.
2. **Represent sample positions exactly.** Use integer sample indices and rational sample rates for deterministic analysis. A block with start `s`, count `N > 0` covers integer samples `[s, s+N)`; its duration is `N/fs`, while the first-to-last *sample timestamp span* is `(N-1)/fs`. The nominal sample-coordinate center is `(2*s+N-1)/2`. Preserve `center_sample_twice=2*s+N-1` at origins greater than `2**53` rather than relying on floating seconds.
3. **Make continuity an assertion.** Require each incoming block's absolute `start_sample` to equal the previous `end_sample_exclusive` in one epoch. A larger start is a gap; a smaller start an overlap/replay or out-of-order block. Report the observed/expected coordinates and reject before changing valid state. **Never fill a missing block with zeros and then call it measured silence.**
4. **Treat epoch changes as explicit data.** Seek, restart, known drop, changed channel layout, sample-rate change, changed decoder/resampler clock or a deliberate timeline discontinuity must begin a new uniquely identified epoch. The first block of a new epoch begins at its declared origin. A pause with no blocks is *not* evidence of inserted silence or elapsed sample time; whether its device clock continues is a separate observation.
5. **Distinguish mapping from quantization.** Sample-count to seconds is an exact rational under an assumed rate. For source and destination rates, a source offset `n` maps to `n * destination_rate / source_rate` target-sample positions: this can be fractional and is **not** an output-sample allocation algorithm. Require an explicit rounding and resampler phase policy before choosing integer output indices.
6. **Correlate independent clocks cautiously.** Use a timestamp anchor with its originating epoch, exact sample index, clock-domain identifier, and *capture/playback/callback* meaning. Mapping another sample by `t_anchor + (s-s_anchor)/fs` is a nominal interpolation/extrapolation, **not a measured clock-drift estimate, latency calibration, or wall-clock truth**. If anchors disagree or clocks drift, measure uncertainty, update anchor models and account for latency rather than silently forcing continuity.
7. **Protect consumer timestamps.** Export integer start/end/center coordinates and epoch IDs to spectra, meters, recorders and visual consumers. Renderer cadence must not change numerical sample time. Preserve invalid/gap status across ring buffers and historical arrays. On the Web Audio API, `getOutputTimestamp()` correlates audio context time with estimated performance time; in PortAudio, ADC input, callback-current, and DAC output timestamps have different meanings. Do not equate either API's callback time with a guaranteed sample hardware timestamp.
8. **Verify with independent cases.** Run the [small reference epoch tracker](scripts/reference_timebase.py) and [regressions](../../tests/test_audio_timebase_reference.py): large integer origins, exact rational 44.1/48-kHz conversion, odd/even frame centers, arbitrary block partitions, gap/overlap rejection without state mutation, seek/rate/channel reset, no-op pause, and explicit device-anchor labels. Compare analytic values independently, not only against the tracker itself.

## Acceptance gate

Every observation specifies a clock/epoch, rate, units, sample-span boundaries, center convention, continuity/validity state, and where relevant external anchor provenance/uncertainty. Deterministic reference tests are **not** hardware synchronization measurements, resampler phase validation, callback-jitter profiling or production UI-integration evidence. Declare any unmeasured output latency and drift.

## Primary sources

- [Web Audio API getOutputTimestamp specification](https://www.w3.org/TR/webaudio/#dom-audiocontext-getoutputtimestamp) — audio context/performance clock correlation and accuracy caveats.
- [PortAudio callback timing and latency guidance](https://github.com/PortAudio/portaudio/wiki/BufferingLatencyAndTimingImplementationGuidelines) — ADC/callback/DAC timestamp semantics and scheduling jitter.
- [FFmpeg AVFrame timestamp and time_base](https://ffmpeg.org/doxygen/trunk/structAVFrame.html) — media presentation timebase is a separate domain from raw sample offsets.
