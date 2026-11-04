# Audio sample clocks, epochs and timestamp mapping

Companion to [audio-timebase-sync](../SKILL.md). The [small oracle](../scripts/reference_timebase.py) is intentionally independent of real hardware, resamplers, audio backends, callback scheduling and the UI. It demonstrates exact coordinate conventions and state guards, **not synchronized device behavior**.

## Coordinates and units

Define one *epoch* with unique identifier E, an integer first-sample origin `o >= 0`, fixed positive rational sample rate `fs = numerator/denominator` (samples/second), and a fixed positive channel count. All sample positions in E are integer coordinates. A received block `(start=s, frames=N)` covers exactly `[s, s+N)` and may be accepted only when its start equals the epoch's next expected coordinate.

- Block duration: `N/fs` seconds; original-sample timestamp span for N >= 1 is `(N-1)/fs`. Neither equals generic "wall-clock latency".
- Nominal first-sample time since epoch origin: `(s-o)/fs`.
- Exclusive-end boundary time since origin: `(s+N-o)/fs`.
- Exact nominal sample-coordinate center: `(2*s+N-1)/2`; exact epoch-relative center time: `(2*s+N-1-2*o)/(2*fs)`.
- The center is the midpoint between the *first and last sample timestamps*, matching Kestrel's STFT convention. For even N it is half-integer; it is **not** the midpoint of the [start,end) time span, which would be `s+N/2`.
- All core reference conversions return `fractions.Fraction`, not a rounded double. Convenience floating seconds may be added by consumers **only** with a declared precision policy.

## Discontinuities and epochs

The tracker rejects a start greater than expected as `gap` (count of skipped/missing sample indices), or less than expected as `overlap` (duplicate, replay or out-of-order positions). Rejections are atomic: the expected next-sample index and last valid span remain unchanged, so the caller can diagnose and choose a policy. An explicit `reset_epoch` must change epoch ID; it declares a new origin, and may declare a new sample rate and channel count. A seek/restart/gap/reconfiguration must not reuse the same epoch ID because historical observations would then have ambiguous timestamps.

A pause without any incoming samples leaves the sample cursor unchanged. If a device continues to generate samples during a pause, those samples are not automatically present or continuous on this measurement tap; account for them explicitly. The reference cannot detect gaps for which no source-provided sample indices/status exist. Upstream callback indices and known overrun status must be trustworthy.

## Mapping rate domains

If a source rate is `48000/1` samples/s, a target rate `44100/1` samples/s, and the source sample **offset** is 1, the target offset is the **fractional position** `147/160` sample; offset 160 maps to target 147. This mapping does not allocate samples, estimate actual resampling group delay, select which output sample is nearest, or guarantee source/destination clock lock. Treat drift and clock-domain changes separately.

## External timestamp correlation

An external anchor records `epoch_id`, `sample_index`, `clock_domain`, `clock_kind` and `time_seconds`. For any sample position within that epoch, nominally map

`t_external(s) = t_anchor + (s - s_anchor)/fs`.

The reference accepts exact-rational anchor seconds, returns exact-rational nominal seconds, and rejects anchors from other epochs or unnamed/incorrect clock domains. This calculation says **nothing** about hardware timestamp error, independent device clock drift, callback jitter, transport latency, or resampler delay. These require dedicated measurements, a model and reported uncertainty. Extrapolation beyond the anchor can be less reliable than nearby interpolation.

The Web Audio API's `AudioContext.getOutputTimestamp()` associates audio context time with estimated performance time. PortAudio's callback time info distinguishes input ADC time, callback invocation time and output DAC time. FFmpeg's media `pts/time_base` is yet another timeline and must not be treated as sample indices without a documented mapping.

## Acceptance fixtures

| Input | Independent expected result |
| --- | --- |
| 1000 frames at fs=48000 | duration = 1/48 s; first-to-last span = 999/48000 s |
| Even 4-frame block, origin 2^54 | exact doubled center = 2*origin+3; relative center = 3/96000 s |
| Odd 5-frame block starting at 40 | doubled center = 84; center at sample 42 |
| Contiguous partitions [3,7,11] versus [21] | same end-exclusive coordinate and exact elapsed time |
| Start 13 after expected 10 | gap of 3; tracker unchanged until explicit reset |
| Start 8 after expected 10 | overlap of 2; tracker unchanged until explicit reset |
| New epoch ID with origin 100 and fs=44100 | first valid block starts at 100; no implicit continuity to old epoch |
| Source offset 1 at 48k mapped to 44.1k | fractional position 147/160, **not** integer zero or one until explicit quantization |
| Nominal output anchor 2 s at sample 1000, fs=48000 | sample 1480 maps to 201/100 s; remains an estimate of output clock, not calibrated latency |
| Input block with wrong declared channel count | rejected without advancing cursor |
| Pause with no source blocks | unchanged cursor; no evidence that an external clock paused |

## Unverified layers

The script is a small **state/reference implementation**, not an audio scheduler, jitter estimator, hardware correlator, or transport decoder. Live sound-card and Web Audio tests, variable-clock drift, resampler group delay, timestamp quantization on different runtimes, buffer-overrun provenance, and display/recording integration remain unverified.

Sources: [W3C Web Audio API](https://www.w3.org/TR/webaudio/), [PortAudio timing](https://portaudio.com/docs/v19-doxydocs-dev/structPaStreamCallbackTimeInfo.html), [FFmpeg AVFrame](https://ffmpeg.org/doxygen/trunk/structAVFrame.html).
