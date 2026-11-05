---
name: audio-stream-buffering
description: Design, audit and verify sample-indexed audio ring buffers, producer/consumer scheduling, exact queue latency, underrun/overrun recovery, callback timing, backpressure, atomic epoch resets and independently tested FIFO fixtures without claiming real-time safety.
---

# Audio stream buffering — never hide missing time

## Activate when

Use for audio buffering, frame FIFO/ring buffers, callback blocks, producer-consumer handoff, queue occupancy, backpressure, latency, underruns/overruns (xrun), glitch diagnosis, input/output discontinuities, startup and shutdown, and the boundary between an audio callback and a background worker. Follow the [stream-buffer contract](references/STREAM_BUFFER_CONTRACT.md) and the [independently specified trace fixtures](../../tests/fixtures/AUDIO_STREAM_BUFFERING_TRACES.md).

Load [audio-timebase-sync](../audio-timebase-sync/SKILL.md) for exact sample epochs and external device clocks; [audio-channel-mapping](../audio-channel-mapping/SKILL.md) for channel identity; [audio-sample-formats](../audio-sample-formats/SKILL.md) for PCM frame/byte accounting; [audio-resampling](../audio-resampling/SKILL.md) when producers/consumers run at **different sample rates**. Reuse [math-dimensional-analysis](../math-dimensional-analysis/SKILL.md), [math-numerical-analysis](../math-numerical-analysis/SKILL.md), and [math-verification](../math-verification/SKILL.md) selectively for rate arithmetic, bounds and independent oracles. Do not duplicate the general math core.

## Engineering procedure

1. **Describe the boundary and clocks.** Declare capture/source versus decoded versus output/playback clocks; sample rate as exact rational Hz, channel count and meaning, frame representation (planar/interleaved), stream epoch and integer sample origin. Define producer and consumer ownership. Byte count, sample count and sample-**frame** count are not interchangeable. A ring FIFO itself does not reconcile drifting hardware clocks or resample channels.
2. **Budget real constraints before selecting capacity.** Derive frame capacity from a measured/assumed jitter and scheduling budget, nominal frame rate, maximum producer burst, expected callback request, and buffering delay. For a queue with `N` **retained** frames at `Fs` Hz, `N/Fs` seconds is its nominal occupancy latency contribution—not an end-to-end DAC/ADC delay or guaranteed maximum. Record high- and low-watermarks and policies for saturation. Do not require callback block size to divide the ring capacity or assume callbacks always have identical frame counts.
3. **Choose an explicit overflow policy.** `reject` must fail an oversized producer block atomically (honest backpressure). `drop_oldest` may accept a bounded producer block, but must record exact discarded sample coordinates, causing a **hole** in the playback timeline. Do not silently compress playback time by skipping old frames. Do not imply that discard-newest or blocking callback writes are always safe; those are separate, explicitly designed policies.
4. **Choose an explicit underflow policy.** `reject` returns no output and changes no state if requested samples are unavailable. `silence` fills missing playback positions with exactly accounted synthetic zero samples. Distinguish dropped **past** frames (`overrun_gap`) from missing **future** frames (`underrun_silence`). Both may appear with genuine source data in one callback; return exact ordered spans. After synthesizing *future* frames, reject any subsequently arriving source block with old sample coordinates—late data must never be retroactively presented as timely.
5. **Enforce sample-clock invariants.** Store `[read_cursor, stored_start, write_cursor)` in exact integer sample coordinates: `read_cursor <= stored_start <= write_cursor`, `write_cursor - stored_start <= capacity`, and producer writes begin at `write_cursor`; consumer reads begin at `read_cursor`. All positions are half-open intervals. A callback partition must not alter sample sequence or synthetic-span attribution when the event schedule is equivalent. A ring wrap affects storage slots, **not** stream time or channel order.
6. **Keep failure transactional.** Validate channel plane count, equal frame sizes, finite data, numeric types, producer/consumer position, capacity and overflow/underflow choices *before* changing cursors or publishing results. When an epoch changes after a seek, rate/channel reconfiguration, device restart or discontinuity, allocate/initialize new state and require a never-reused identifier. Do not splice old FIFO contents into a new epoch.
7. **Respect actual audio callback constraints.** PortAudio warns against allocation, file I/O, blocking operations and unbounded processing inside its high-priority callback; transfer work via an appropriate FIFO and measure deadline misses. JACK's documented lock-free ringbuffer is **single-writer/single-reader**, not an MPMC solution. A Python reference using allocated lists and dictionaries is **not** lock-free, thread-safe, no-allocation, real-time scheduling safe, or proof of native atomic memory ordering. Production implementations need backend-specific synchronization/memory-order reviews, allocation and page-fault discipline, callback deadline/CPU tests and dropout telemetry. Test behavior for variable callback sizes, device startup, complete/abort semantics and backpressure under actual load.
8. **Use bounded independent fixtures, then actual integration tests.** Run [the standard-library oracle](scripts/reference_stream_buffer.py) and [36 focused tests](../../tests/test_audio_stream_buffering_reference.py): exact FIFO, wrap, channel preservation, independent `deque` and coordinate-keyed models, chunking, drop-oldest with documented loss, reject atomicity, silence without retroactive source arrivals, rational latency, epochs, malformed/nonfinite samples, and large (>2^53) sample indices. These are simulated queue-semantics checks only; they do **not** establish actual hardware glitches, throughput, output latency or multi-thread race correctness.
9. **Evaluate the full live system separately.** Record xrun counts, capture/input buffer timestamps, output hardware timestamps, queue-depth distributions, callback scheduling jitter, deadline margin, device clock drift, p99/p99.9 tail latency, and audible/discontinuity evidence. Make explicit whether latency is capture-to-application, queue-only, application-to-DAC, or full round-trip. Run stress with slow producers and variable callbacks; validate actual container channel/rate interpretation. No synthetic reference test substitutes for these observations.

## Verification and acceptance

```sh
python3 tools/validate_seed.py
python3 -m unittest discover -s tests -v
# On an actual checkout:
git diff --check
```

The oracle models **1–8 channels**, **1–256 stored frames**, **1–256 frames per read**, a single logical producer and consumer, and exact rational rates from 2–384 kHz. It does not provide an actual sound-device callback, a lock-free SPSC/MPMC transport, or production throughput guarantees.

**Accept** a solution only when it declares queue capacity/watermarks, frame clock and epoch, ownership/concurrency assumptions, overflow and underrun policies, silence/data provenance, latency units, atomic failure behavior, quantitative verification and remaining real-device risks. **Reject** any solution that masks a dropped time interval or retroactively accepts old samples as if they arrived on time.

## Primary references

- [PortAudio stream callback contract and underflow/overflow flags](https://files.portaudio.com/docs/v19-doxydocs/portaudio_8h.html) — callback deadline and host-supplied time/status metadata.
- [PortAudio callback guidelines](https://files.portaudio.com/docs/v19-doxydocs-dev/writing_a_callback.html) — predictable runtime, blocking/allocations and scheduling.
- [JACK ringbuffer API](https://jackaudio.org/api/ringbuffer_8h.html) — explicit single-writer/single-reader, ring read/write spaces and nonblocking usage.
