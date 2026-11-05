# Synthetic audio analysis provenance — independently derived expectations

The fixtures below use no recordings, personal metadata, private paths or device identifiers. Their integer/rational expectations are computed from the declared model, *not* from the Python validator. See [the focused tests](../test_audio_analysis_provenance_reference.py), [contract](../../skills/audio-analysis-provenance/references/PROVENANCE_CONTRACT.md) and [oracle](../../skills/audio-analysis-provenance/scripts/reference_provenance.py).

| Step | Independent input/coordinate reasoning | Expected provenance observation |
| --- | --- | --- |
| Synthetic source | Start `2^54+23`, end `2^54+31` (8 frames), nominal rate 44,100 Hz, ordered L/R | Source `capture-e1` has discrete half-open span of eight frames; no JS-float rounding |
| Source coverage | `[start,start+4)` observed, `[start+4,start+5)` gap, `[start+5,start+8)` synthetic silence | Exactly partition eight frames, and `gap`/`synthetic_silence` must remain visible downstream |
| Rational resample | `48000/44100=160/147`, source interval duration `8/44100` seconds | Output `ceil(8*160/147)=ceil(1280/147)=9` frames, origin `100`, epoch `analysis-e2`, rate 48 kHz; do **not** equate absolute input and output indices |
| Analysis | PSD activity consumes nine derived frames `[100,109)` with `window=hann`, `nfft=8`, scaling/density declared, result normalized in `fs2_per_hz` | Analysis must reference input entity and bounded frame interval, algorithm and version, units/normalization and an explicit unquantified uncertainty |
| Visualization | Render consumes PSD, creates waterfall with `x_unit=s`, `y_unit=db_fs2_per_hz`, `transform=db10`, `db_reference=one-fs2-per-hz` | Display transformation has its own provenance and cannot modify claimed PSD units or erase the source gap |
| Digest | Declared source SHA-256 = `sha256(b"public-std-lib-test-vector-8-frames")` | Matching only if those exact supplied bytes are hashed; a changed byte gives mismatch, but still no authentication of source/algorithm |
| Deterministic record | Same nested dictionaries with reversed key insertion order | Custom sorted-UTF-8 JSON encodes byte-identically; changing `window=hann` to `window=blackman` must change SHA-256 graph fingerprint |
| Unknown origin | Replace declared source ID and claim with `null`, add `unknown_origin` to all downstream limitations | Graph remains internally consistent and explicitly unverified; cannot claim reproducibility |
| Truncation | Replace last source segment with `truncated`, carry that status to every dependent entity | Graph accepts known incomplete span only when it remains labelled; missing flags must be rejected |
| Hostile graph | Two derived audio entities each produced by a process that uses the other | Directed cycle rejected even if each node has one generator and every ID exists |
| Inconsistent clock | Claimed 147/160 rate map for actual 44.1→48 kHz metadata | Reject as contradictory, not interpret rate conversion through guessed phase |

**Evidence interpretation:** These premises are mathematical/indexing or declared-graph invariants. They do not verify signal calculations, actual playback/sensor timestamps, software execution, source authenticity, W3C PROV ontology export or RFC 8785 canonicalization. The oracle deliberately has no raw audio or external trust-service dependency.
