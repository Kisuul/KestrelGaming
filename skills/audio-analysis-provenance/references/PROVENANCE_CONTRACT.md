# Kestrel audio-provenance graph / version 1

This contract is a *strict educational declaration and validation model*, not a PROV-DM/PROV-O conformance implementation, a JSON Canonicalization Scheme (RFC 8785) encoder, a provenance authentication system or a comprehensive digital signal processing archive. It is inspired by the distinction between **entity**, **activity**, and **responsible agent** from [W3C PROV-DM (2013)](https://www.w3.org/TR/prov-dm/); PROV-O maps that framework into OWL2/RDF ([PROV-O](https://www.w3.org/TR/prov-o/)). The reference uses its own narrow JSON schema with no RDF export or W3C constraints validator.

## Wire model and types

Top-level object has exactly `schema`, `entities`, `activities`, and `agents`; `schema` is the literal `kestrel-audio-provenance/1`. Lists have an enforced small bound, identifiers are lowercase ASCII slug tokens unique *globally across all node categories*. The graph is a DAG with edges from an activity's `uses` entity IDs to its `generates` entity IDs. Each non-source entity has exactly one generating activity. Declared source audio has no generating activity. Other activity types and unknown JSON fields fail closed; unknown values are represented only in explicitly allowed fields.

**Audio entity** (`kind=audio`, `origin=source|derived`): `id`, `identity`, `timebase`, `coverage`, `limitations`. `timebase` contains exact `epoch`, `clock_domain`, `rate={num,den}` in rational Hz, `start` and `end` sample coordinates, ordered channel IDs and `sample_format`. `start`, `end`, `num`, and `den` are **canonical unsigned decimal strings**; rates must be positive and reduced. Sample indices are ≤2^64−1; `[start,end)` must have 1–65,536 frames. Source and destination epochs/domains are distinct; index equality across them does not imply clock synchronization. A source with no declared identifier **must** carry `unknown_origin`.

`coverage` consists of consecutively adjoining `[start,end)` intervals that **exactly partition** the audio entity's span. Statuses: `observed` (original source samples), `derived` (processed, not independently observed), `gap` (known unavailable span), `truncated` (end/interval known incomplete), `synthetic_silence` (generated zeros), `unknown` (status unavailable). Derived audio cannot be relabelled `observed`; source audio cannot be `derived`. **Any** of `gap`, `truncated`, `synthetic_silence`, `unknown`, `unknown_origin` must be reflected as limitations in every downstream entity, conservatively across its full ancestry. This prevents laundering known gaps via a resampler or a plot, but may over-report risks when a downstream window samples only a clean subset. Do not reinterpret a missing span as acoustic silence.

**Analysis entity** (`kind=analysis`): `measurement={quantity,unit,normalization,uncertainty}`, explicit `basis=[{entity,start,end},...]` audio frame ranges, identity and limitations. Each basis must lie inside an audio entity **actually used by the generating analysis activity**; it cannot refer to a different or out-of-bounds sample/clock domain. The underlying entity supplies the epoch, rate and channel labels, preventing accidental duplication of contradictory timebase copies. The analysis activity must declare algorithm ID/version, measurement parameters such as window/nfft/hop/filter or selection policy as applicable, and limitations. Empty/missing measurement units or unknown basis are rejected, not guessed.

`uncertainty={state,description,bound,bound_unit}` has `state=quantified|unquantified|unknown`. For a quantified uncertainty, `bound` is an exact reduced **nonnegative** rational `{num,den}` with `bound_unit` *identical to the measurement's unit*; for either non-quantified state, both are `null` and `uncertainty_unquantified` must be an entity limitation. A *declared* bound is not a calibrated or empirically demonstrated uncertainty. Future confidence, covariance and systematic uncertainty models are deliberately out of scope.

**Visualization entity** (`kind=visualization`): `display` is an explicitly named string map containing at least `kind`, `x_unit`, `y_unit`, `transform`; optional additional keys can state color map and dB reference. A `render` activity links an analysis entity to the display entity. Display transformations do not retroactively change the measurement's values/units or input clock; the provenance record distinguishes a rendered chart from its DSP result.

**Identity, agents, and activities:** Every entity's `identity` has exactly `declared_id` (slug or null), `sha256_claim` (64 lowercase hexadecimal characters or null), and `scope` (slug naming exactly which byte encoding is claimed, or null). Missing/invalid digest scope is rejected. **No graph field asserts verified contents**; content verification is an actual separate call with the bytes supplied. Optional `agents=[{id,role,version}]` represent responsible software identities **as claims**. Every activity records `id`, `kind`, `uses`, `generates`, `algorithm={id,version}`, `parameters` map (short string values), `assumptions` slug list and nullable `responsible_agent`. Allowed activities are `resample`, `process`, `inject_silence`, `analyze`, and `render`. The supported one-input/one-output transforms forbid silent channel reordering and rate changes. A `process` that changes channel identities must state a `channel_map` matching output order; no numeric channel remix proof is attempted. `inject_silence` must visibly label synthetic output intervals. All raw data or arbitrary untyped metadata fields are disallowed.

## Rate and sequence contracts

A `resample` activity uses a single audio entity and generates a single derived audio entity, with `rate_mapping={source_entity,target_entity,up,down,source_anchor,target_anchor}`. The output/input rate ratio must equal the **reduced** exact `up/down`; anchors equal the starts of the respective declared intervals. The v1 frame-allocation policy is `N_out=ceil(N_in·up/down)` for a bounded complete record. Resampling **requires a distinct destination epoch**, and preserves channel identity; any channel mapping must be a different activity. This verifies metadata consistency, not polyphase phase error, filter delay, actual captured samples or physical device clock alignment. For 8 source frames at 44,100 Hz, 160/147 predicts **9 output frames** at 48,000 Hz; source sample start may exceed 2^53 and be unrelated numerically to output sample start.

A non-resampling `process`/`inject_silence` must preserve declared rate and named clock domain. A `process` changing channel order without an explicit `channel_map` is rejected. The declaration does *not* prove an algorithm actually performed the specified mapping. Every output has at most one generator; cycles, missing entities/agents and duplicate IDs are rejected by DAG validation.

## Deterministic JSON: exact scope and limits

The oracle's custom deterministic encoding is:

1. Validate the entire object and graph first. Reject JSON float values, booleans, unknown keys, duplicate object keys in parsed input, binary payloads, unsafe metadata fields, overlong strings and overlarge graphs.
2. Use Python `json.dumps(graph, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)` and encode the resulting text as UTF-8. Object key order is ignored; **array order is meaningful** (e.g. channel and activity order). Unicode is *not normalized* and should not be treated as equivalent across codepoint forms.
3. Hash these exact encoded **claim-record bytes** with SHA-256 using `hashlib.sha256`. The resulting `graph_fingerprint` changes when a version, algorithm parameter, segment, uncertainty or display configuration changes.

This format is **not RFC 8785 JCS**: it does not implement ECMAScript's full numeric formatting, UTF-16 property ordering or JCS/I-JSON conformance checks. The schema uses canonical decimal **strings** for sample coordinates and exact rationals to avoid binary64 time rounding. `parse_graph` also rejects UTF-8 and duplicate JSON-key malformations. The SHA-256 value only supports comparing *serialized declarations*. It is not a signed audit log, authoritative timestamp, proof of software execution, source authenticity or truth of a measured PSD.

`verify_entity_bytes(graph, entity_id, content_bytes)` computes SHA-256 from actual supplied bytes and returns `matches_claim`, `mismatch`, or `unclaimed` with the actual digest. A matching result establishes **byte equality relative to the declared scope assuming the supplied bytes are the intended bytes**; the function cannot determine the physical source or whether the claim was fabricated. `inspect_lineage` always marks `unverified_content` on source entities regardless of whether they hold a *claimed* hash, and returns `reproducible: not_demonstrated`. Actual reproducibility requires re-access to input bytes, software/algorithm versions and dependencies, calibration context, the same parameters, and independent comparison of analysis values.

## Adversarial acceptance matrix

| Case / independent premise | Required behavior |
| --- | --- |
| Synthetic 8-frame PCM, epoch `capture-e1`, 44,100 Hz, start 2^54+23, two ordered channels | Exact 8-frame `[start,end)`; input index not rounded; gap `[+4,+5)` and injected silence `[+5,+8)` carried into lineage |
| Resample 44.1→48 kHz with L/M = 160/147 | Exact 9 output frames, separate output epoch `analysis-e2`, source-origin and output-origin anchors; wrong ratio/count rejected |
| PCM→resample→PSD→waterfall | Three ordered generating activities, explicit analysis input basis and visualization display axes; lineage lists gap/synthetic and admits reproduction unproven |
| Same graph with object key order reversed | Identical deterministic UTF-8 bytes and record hash |
| Changed window/nfft or display gamma | Different graph fingerprint; original content digest unaffected |
| Correct SHA claim vs actual synthetic bytes | `matches_claim`; modified bytes `mismatch`; no claim `unclaimed`; none establishes authenticity |
| Truncation or unknown source | Required explicit limitations reach derived analysis and visualization; absent flags fail |
| Unregistered agent, broken entity link, duplicate IDs, multiple producers, cyclic derivation | Reject, without trying to repair the graph |
| Noncanonical decimal, contradictory rate, impossible span, wrong basis domain, silent channel swap, malformed uncertainty | Reject before serialization |
| Raw path/email/token-shaped metadata and duplicate JSON keys | Reject, with documented best-effort privacy limits |

See [the 24 independent/adversarial tests](../../../tests/test_audio_analysis_provenance_reference.py) and [frozen trace derivation](../../../tests/fixtures/AUDIO_ANALYSIS_PROVENANCE_TRACES.md). Python standard library only, no real media/hardware, no cryptographic signature protocol, no proof that declared algorithms ran and no W3C/RFC conformance certification.

## Known design compromises and future decisions

- v1 is a bounded *graph declaration*, not a complete production streaming provenance/metadata database. Input/clock validity depends on truthful upstream declarations; the timebase model does not independently authenticate sample capture.
- Quality flags intentionally propagate conservatively along the **whole** ancestor graph. A more precise per-sample contamination mapping needs DSP-specific footprint and filter-delay computation, absent here.
- Raw sample payloads, private paths, emails, hardware IDs and person names are not needed. Slug/field restrictions and best-effort checks catch common unsafe metadata, not every sensitive string. Privacy review remains required.
- Output values themselves are not embedded or re-executed. Content scopes are declared strings; a future integration must define exact audio artifact byte encodings to make content digests comparable across runtimes.
- A future extended schema would need migration rules, archival policy, hashes or signatures over externally attested source artifacts, and independently checked RFC 8785 / W3C PROV mappings *if* interoperability actually requires those standards.

Primary references: [W3C PROV-DM](https://www.w3.org/TR/prov-dm/), [W3C PROV-O](https://www.w3.org/TR/prov-o/), [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785.html), [Python hashlib](https://docs.python.org/3/library/hashlib.html), [Python json](https://docs.python.org/3/library/json.html).
