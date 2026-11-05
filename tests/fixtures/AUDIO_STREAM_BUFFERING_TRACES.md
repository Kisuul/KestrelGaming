# Independent frame-buffering trace fixtures

**Provenance:** Derived from explicit integer sample-coordinate arithmetic rather than the implementation's slot-indexing formula. The fixed 2026-11-04 traces below are used alongside a separate `collections.deque` FIFO reference model (400 seeded random actions) and a separate dictionary indexed by absolute sample coordinate (200 seeded actions) in [test_audio_stream_buffering_reference.py](../test_audio_stream_buffering_reference.py), seed `20261104`. No NumPy, SciPy, audio interface or nondeterministic timing dependency is needed.

For an epoch whose first frame is 100, rate=48,000 Hz, capacity=4, two channels:

| Event | Expected source timeline | Expected effect | Loss or synthetic provenance |
| --- | --- | --- | --- |
| push frames `[100,104)` | `[x100,x101,x102,x103]` | occupancy 4, free 0 | none |
| push `[104,106)` with overflow **reject** | unchanged | `ValueError`, producer cursor still 104 | no partial write |
| push `[104,106)` with **drop_oldest** | `[x102,x103,x104,x105]` | occupancy 4, `write_cursor=106`, `stored_start=102`, `read_cursor=100` | dropped span `[100,102)` |
| pull `[100,106)` after drop with **silence** | `[0,0,x102,x103,x104,x105]` | occupancy 0, `read_cursor=106` | span `(overrun_gap,100,2)` followed by `(input,102,4)` |
| push `[100,102)` then pull `[100,104)` with **silence** | `[x100,x101,0,0]` | `read_cursor=write_cursor=104` | span `(input,100,2)` followed by `(underrun_silence,102,2)` |
| next producer push begins at 102 after that silence | unchanged | `ValueError` | late data may not rewrite already presented coordinates |
| next producer push begins at 104 | `[x104,…]` | allowed | new timely source data |

**Counterexample checks**:

- Mistakenly using 96,000 *stereo samples* as 96,000 audio frames at 48 kHz doubles the computed capacity/latency.
- A circular buffer full at capacity 4 that first discards 2 frames must not slide retained `[x102…]` into playback times 100–101 without declaring the hole.
- A consumer call that needs 3 frames when only 2 are available and policy is `reject` must not consume the two available frames before failing.
- Filling silence for a future missing interval does not grant permission to insert late packets retroactively; the next acceptable source coordinate becomes the end of the output request.
- Ring slot modulo arithmetic at `2**61 + 19` must never be used to calculate elapsed seconds in floating-point; integer sample positions and `Fraction(frame_count, Fs)` remain exact.
- Callback partitions that change only chunk boundaries, while retaining the same producer/consumer event order and capacity, must yield identical source samples and coherent metadata.

**Numeric accuracy:** Samples in fixtures are exactly representable simple binary64 values; no tolerance-based output amplitude comparison is required. All expected occupancies, sample coordinates, gap lengths, and nominal seconds are integer/rational. These fixtures test queue semantics, not measured real-time performance or audio-device behavior.

Primary background: [PortAudio callback reference](https://files.portaudio.com/docs/v19-doxydocs/portaudio_8h.html), [PortAudio callback execution restrictions](https://files.portaudio.com/docs/v19-doxydocs-dev/writing_a_callback.html), and [JACK SPSC ringbuffer API](https://jackaudio.org/api/ringbuffer_8h.html).
