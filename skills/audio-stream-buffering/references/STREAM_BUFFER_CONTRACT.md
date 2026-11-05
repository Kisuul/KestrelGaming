# Ring-buffer reference contract: sample-frame provenance and queue lifecycle

This contract accompanies [audio-stream-buffering](../SKILL.md), [the reference module](../scripts/reference_stream_buffer.py) and [the frozen test scenarios](../../../tests/fixtures/AUDIO_STREAM_BUFFERING_TRACES.md). It is an educational bounded **single-logical-producer/single-logical-consumer model**, not a real-time audio engine, a thread-safe lock-free queue, a standards meter or a device timing oracle.

## 1. Frame, time and capacity definitions

- **Frame:** one sample per channel, at one sample-time coordinate. A two-channel 48 kHz stream has 48,000 frames/second and 96,000 individual channel samples/second; it is *not* 96,000 audio frames/second.
- **Epoch clock:** `rate_hz: Fraction` with 2,000 ≤ Fs ≤ 384,000 Hz, `origin_sample` a nonnegative integer, and a never-reused `epoch_id`. The source and output sample indices are in the same declared clock domain for this model. Different clock domains require explicit sync/resampling; no hardware drift is estimated here.
- **Planar samples:** one finite `int`/`float` list per channel; every channel has equal nonempty length. Input blocks contain at most the capacity and at most 256 frames. Identity copy does not clamp amplitudes above ±1, quantize, resample or mix channels.
- **Capacity:** 1–256 retained *frames*, not individual samples or bytes. A consumer request can be 1–256 frames, larger than capacity only when its explicit concealment policy can satisfy the remaining requested time with synthesized silence. The reference preallocates value slots but allocates return data on every operation; no callback-safe claim follows.

An output block `[s, s+N)` covers **N sample intervals** even if its last `N-k` entries are synthetic zeros. Exact nominal start time relative to origin is `(s-origin_sample)/Fs` seconds. Queue occupancy alone gives `buffered_frames/Fs`; end-to-end or output DAC latency includes scheduling, transport, processing and device factors not represented in this ratio.

## 2. Invariants and storage shape

`FrameRing` retains exact integers:

- `read_cursor`: next output sample frame to present;
- `stored_start`: oldest *actually retained* source frame, which may exceed `read_cursor` if a prior producer overrun discarded unplayed frames;
- `write_cursor`: next expected producer frame to accept.

Always require `read_cursor <= stored_start <= write_cursor`, `0 <= write_cursor-stored_start <= capacity`, `free = capacity - buffered`, `pending_overrun_gap = stored_start-read_cursor`. `playable_frames = buffered` only when no pending gap; otherwise zero. The physical slot for sample-coordinate `n` is `n % capacity`, but ring wrapping **does not** shift the frame timeline. Intentionally do not use 32-bit wrapping counters or floating times to infer order.

### Producer `push(start_sample, planes)`

Requires `start_sample == write_cursor`, exactly matched nonempty planar frames, all finite representable binary64 samples, and `N <= capacity`.

- **`overflow_policy=reject`:** if `buffered + N > capacity`, raise `ValueError`; the entire previous state remains unchanged. This is a *notification/backpressure model*, not a blocking write.
- **`overflow_policy=drop_oldest`:** let `D=max(0,buffered + N - capacity)`; discard exactly `[stored_start,stored_start+D)`, advance `stored_start` by D, and write the incoming frames. `read_cursor` remains unchanged; therefore missing output positions remain a visible `overrun_gap` until the consumer explicitly recovers them. The producer report declares dropped range, count and queue occupancy. The sample clock is **not** compressed.
- Input bursts larger than capacity always reject—even in drop mode—because this bounded oracle does not silently drop an unspecified prefix of the *new* block. Actual production policy may choose another deliberate rule.

### Consumer `pull(start_sample, frames)`

Requires `start_sample == read_cursor`, `1 <= frames <= 256`, and uses ordered **nonoverlapping** spans:

1. `overrun_gap` over missing *past* positions `[start, min(end,stored_start))`;
2. `input` over retained positions `[max(start,stored_start), min(end,write_cursor))`;
3. `underrun_silence` over missing *future* positions `[max(start,write_cursor), end)`.

Each span contains its `kind`, exact `start_sample` and positive `frames`; total length is the requested frame count. Output always has exactly `frames` samples per channel *if pull succeeds*. The record declares source frames, overrun-gap frames, future underrun frames and `synthetic_audio`; it does **not** call inserted zeros real source silence.

- **`underflow_policy=reject`:** any required frame missing from the requested timeline (past or future) makes the entire pull fail atomically with no changes to read/write cursors, counters or contents.
- **`underflow_policy=silence`:** synthesize zeros for missing intervals; label each distinct reason. Set `read_cursor=end`. If the consumer advanced *beyond* `write_cursor`, move `write_cursor=end` so the **next producer must begin at the post-silence cursor**. Set `stored_start=max(stored_start,end)` to release read frames. A late source write to synthesized history must reject rather than overwrite previously rendered audio. The total `underflow_silence` and `overrun_gap_silence` counters are separate from the actual producer-drop count; a producer can drop frames that have not yet been presented/synthesized.

**Important nuance:** A consumer may refuse a dropped gap even when later genuine source frames are already retained. `drop_oldest` is not automatically coupled to silence; if reject is selected, the application must deliberately reset/recover its epoch before proceeding.

## 3. Timeline examples and independent oracles

At Fs=48 kHz, origin=100, capacity=4, stereo:

- Fill frames 100–103, then `drop_oldest` push 104–105 => lose 100–101. Pull `[100,106)` with silence => `[0,0,x102,x103,x104,x105]`, spans `[overrun_gap(100,2),input(102,4)]`. This is **not** `[x102,x103,x104,x105]` shifted to time 100.
- Push only 100–101; pull `[100,104)` with silence => `[x100,x101,0,0]`, spans `[input(100,2),underrun_silence(102,2)]`. Next producer starts at **104**, never at 102. A late packet for 102 fails.
- Both policies reject => no write on overflow, no read on underflow; no partial cursor changes.

Tests contain a separately reasoned `collections.deque` FIFO oracle with randomized producer/consumer partitioning and an independent index-keyed dictionary oracle for overrun/concealment. Both compare actual samples/occupancy against independent representations instead of calling the same ring method to compute expectations. Frozen traces and negative policies are catalogued in [AUDIO_STREAM_BUFFERING_TRACES.md](../../../tests/fixtures/AUDIO_STREAM_BUFFERING_TRACES.md).

## 4. Discontinuities, resets, and concurrency

`reset_epoch(new_id, origin, *, capacity_frames, channels, rate_hz, overflow_policy, underflow_policy)` validates a wholly new configuration **before** mutating current state. It clears stale queued data, counters and physical slots, updates the expected time domain, and refuses every previously used epoch ID. Gaps/overlaps, seeks, format or device changes are not silently represented as ordinary contiguous blocks. Producer or consumer discontinuities require a declared fresh epoch or an explicit policy above.

**Concurrency warning:** The Python oracle allocates, uses Python objects, relies on ordinary method-call sequencing, and offers **no real SPSC lock-free, MPMC, realtime scheduling, memory barrier, atomic index, wait-free, priority inversion, race freedom, or ABA safety guarantee**. It is not appropriate inside a production audio callback. JACK's ring API requires fixed one-reader/one-writer ownership for its lock-free semantics; PortAudio warns about blocking/allocating in callbacks. A real backend must specify acquire/release ordering for its ring indices, possible cache-line contention, setup/lifecycle ownership, device scheduler timestamps, page faults, and high-water/low-water behavior. Test with concurrency sanitizers and real hardware callback traces as warranted.

## 5. Verification scope and unresolved engineering questions

The bounded suite verifies FIFO order, stereo independence, wrap, clock origin beyond `2^53`, exact rational nominal occupancy latency, variable chunking, lost-oldest accounting, partial timeline concealment, late packet rejection, atomically rejected invalid calls, and epoch reuse. It **does not** measure actual playback latency, throughput, hardware FIFO size, glitch rate, CPU deadline compliance, clock drift, denormal performance, memory locking, device underflow flags, or other hidden host buffers.

Follow [PortAudio callback documentation](https://files.portaudio.com/docs/v19-doxydocs/portaudio_8h.html), [PortAudio callback guidelines](https://files.portaudio.com/docs/v19-doxydocs-dev/writing_a_callback.html) and [JACK ringbuffer API](https://jackaudio.org/api/ringbuffer_8h.html) for real system implementation, while preserving the distinction between an API's reported input/output xrun flags and **this model's** separately labelled producer-overflow and consumer-underflow cases.
