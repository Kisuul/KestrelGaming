"""Bounded, strict audio-provenance graph oracle (schema kestrel-audio-provenance/1).

Stdlib-only: models declared history, never establishes truthful capture or software
execution. Its deterministic UTF-8 JSON is NOT RFC 8785/JCS and is not PROV-O.
"""
from __future__ import annotations

from fractions import Fraction
from hashlib import sha256
import json
import math
import re

SCHEMA = "kestrel-audio-provenance/1"
MAX_ENTITIES = 32
MAX_ACTIVITIES = 32
MAX_AGENTS = 16
MAX_BYTES = 131072
MAX_SEGMENTS = 128
MAX_FRAME_SPAN = 65536
MAX_SAMPLE_INDEX = (1 << 64) - 1
TOKEN = re.compile(r"[a-z][a-z0-9._-]{0,63}\Z")
DECIMAL = re.compile(r"(?:0|[1-9][0-9]*)\Z")
DIGEST = re.compile(r"[a-f0-9]{64}\Z")
SENSITIVE = re.compile(r"(?:[A-Za-z]:\\|/home/|/Users/|/mnt/|(?:[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}))", re.I)
BAD_KEYS = {"password", "secret", "access_token", "private_key", "email", "raw_audio", "gps", "full_path", "recording_bytes"}
QUALITY = {"observed", "derived", "gap", "truncated", "synthetic_silence", "unknown"}
FLAGS = {"gap", "truncated", "synthetic_silence", "unknown", "unknown_origin",
         "uncalibrated", "clock_unverified", "algorithm_unavailable", "uncertainty_unquantified"}


class ProvenanceError(ValueError):
    """Invalid or contradictory declaration (no implicit repairs)."""


def _fail(message: str):
    raise ProvenanceError(message)


def _exact_keys(value, required, optional=(), where="object"):
    if type(value) is not dict:
        _fail(f"{where}: expected JSON object")
    required, optional = set(required), set(optional)
    if required - value.keys() or value.keys() - required - optional:
        _fail(f"{where}: missing/unexpected keys")


def _list(value, name, minimum=0, maximum=MAX_SEGMENTS):
    if type(value) is not list or not minimum <= len(value) <= maximum:
        _fail(f"{name}: invalid list length")


def _token(value, name):
    if type(value) is not str or TOKEN.fullmatch(value) is None:
        _fail(f"{name}: expected short privacy-safe identifier")


def _string(value, name):
    if type(value) is not str or not value or len(value) > 128 or SENSITIVE.search(value):
        _fail(f"{name}: empty/overlong/potentially sensitive string")


def _decimal(value, name, max_value=MAX_SAMPLE_INDEX, positive=False):
    if type(value) is not str or len(value) > 21 or DECIMAL.fullmatch(value) is None:
        _fail(f"{name}: expected unsigned canonical decimal string")
    number = int(value)
    if number > max_value or (positive and number == 0):
        _fail(f"{name}: out of bounds")
    return number


def _ordered_tokens(value, name, max_count=8):
    _list(value, name, 1, max_count)
    for x in value:
        _token(x, name)
    if len(value) != len(set(value)):
        _fail(f"{name}: duplicate label")


def _flags(value, name):
    _list(value, name, 0, 20)
    if len(set(map(str, value))) != len(value) or any(type(x) is not str or x not in FLAGS for x in value):
        _fail(f"{name}: invalid or duplicate limitation")


def _map_string(value, name, limit=24):
    _exact_keys(value, [], value.keys() if type(value) is dict else [], name)
    if len(value) > limit:
        _fail(f"{name}: too many parameters")
    for k, v in value.items():
        _token(k, f"{name}.key")
        _string(v, f"{name}.{k}")


def _rate(value):
    _exact_keys(value, ["num", "den"], where="sample_rate")
    n = _decimal(value["num"], "rate.num", 10**9, positive=True)
    d = _decimal(value["den"], "rate.den", 10**9, positive=True)
    if math.gcd(n, d) != 1:
        _fail("sample rate must be reduced exact rational")
    return Fraction(n, d)


def _identity(value):
    _exact_keys(value, ["declared_id", "sha256_claim", "scope"], where="identity")
    claimed = value["declared_id"]
    if claimed is not None:
        _token(claimed, "identity.declared_id")
    digest, scope = value["sha256_claim"], value["scope"]
    if (digest is None) != (scope is None):
        _fail("digest and byte scope must be present together")
    if digest is not None:
        if type(digest) is not str or DIGEST.fullmatch(digest) is None:
            _fail("invalid SHA-256 claim")
        _token(scope, "identity.scope")


def _audio(entity):
    _exact_keys(entity, ["id", "kind", "origin", "identity", "timebase", "coverage", "limitations"], where="audio")
    if entity["origin"] not in ("source", "derived"):
        _fail("audio origin must be source/derived")
    tb = entity["timebase"]
    _exact_keys(tb, ["epoch", "clock_domain", "rate", "start", "end", "channels", "sample_format"], where="timebase")
    for field in ("epoch", "clock_domain", "sample_format"):
        _token(tb[field], f"timebase.{field}")
    _rate(tb["rate"])
    _ordered_tokens(tb["channels"], "timebase.channels")
    start = _decimal(tb["start"], "timebase.start")
    end = _decimal(tb["end"], "timebase.end")
    if not 0 < end - start <= MAX_FRAME_SPAN:
        _fail("invalid half-open audio frame span")
    _list(entity["coverage"], "coverage", 1, MAX_SEGMENTS)
    cursor = start
    for seg in entity["coverage"]:
        _exact_keys(seg, ["start", "end", "status"], where="coverage segment")
        x, y = _decimal(seg["start"], "coverage.start"), _decimal(seg["end"], "coverage.end")
        if x != cursor or y <= x or y > end or type(seg["status"]) is not str or seg["status"] not in QUALITY:
            _fail("coverage must partition the entire half-open span without holes/overlap")
        if entity["origin"] == "derived" and seg["status"] == "observed":
            _fail("derived samples cannot be labelled original observations")
        if entity["origin"] == "source" and seg["status"] == "derived":
            _fail("source samples cannot be labelled derived")
        cursor = y
    if cursor != end:
        _fail("coverage must end at audio span end")
    if entity["origin"] == "source" and entity["identity"]["declared_id"] is None and "unknown_origin" not in entity["limitations"]:
        _fail("unidentified source must declare unknown_origin")
    return tb


def _analysis(entity):
    _exact_keys(entity, ["id", "kind", "identity", "measurement", "basis", "limitations"], where="analysis")
    meas = entity["measurement"]
    _exact_keys(meas, ["quantity", "unit", "normalization", "uncertainty"], where="measurement")
    for field in ("quantity", "unit", "normalization"):
        _token(meas[field], f"measurement.{field}")
    unc = meas["uncertainty"]
    _exact_keys(unc, ["state", "description", "bound", "bound_unit"], where="uncertainty")
    if unc["state"] not in ("quantified", "unquantified", "unknown"):
        _fail("uncertainty.state unsupported")
    _string(unc["description"], "uncertainty.description")
    if unc["state"] == "quantified":
        _exact_keys(unc["bound"], ["num", "den"], where="uncertainty.bound")
        numer = _decimal(unc["bound"]["num"], "bound.num", 10**12)
        denom = _decimal(unc["bound"]["den"], "bound.den", 10**12, positive=True)
        if math.gcd(numer, denom) != 1 or unc["bound_unit"] != meas["unit"]:
            _fail("uncertainty bound must be reduced, exact and in measurement units")
    else:
        if unc["bound"] is not None or unc["bound_unit"] is not None:
            _fail("unknown/unquantified uncertainty must have null bound and unit")
        if "uncertainty_unquantified" not in entity["limitations"]:
            _fail("non-quantified uncertainty must be in limitations")
    _list(entity["basis"], "basis", 1, 8)
    for part in entity["basis"]:
        _exact_keys(part, ["entity", "start", "end"], where="basis")
        _token(part["entity"], "basis.entity")
        a, b = _decimal(part["start"], "basis.start"), _decimal(part["end"], "basis.end")
        if a >= b:
            _fail("analysis basis must be a positive half-open span")


def _visualization(entity):
    _exact_keys(entity, ["id", "kind", "identity", "display", "limitations"], where="visualization")
    _map_string(entity["display"], "display")
    if not {"kind", "x_unit", "y_unit", "transform"} <= entity["display"].keys():
        _fail("visualization must declare display kind and axes/transform")


def _kind(entity):
    _exact_keys(entity, ["id", "kind", "identity", "limitations"], ["origin", "timebase", "coverage", "measurement", "basis", "display"], "entity")
    _token(entity["id"], "entity.id")
    _identity(entity["identity"])
    _flags(entity["limitations"], "entity.limitations")
    kind = entity["kind"]
    if kind == "audio":
        return _audio(entity)
    if kind == "analysis":
        _analysis(entity)
    elif kind == "visualization":
        _visualization(entity)
    else:
        _fail("entity.kind must be audio, analysis or visualization")
    return None


def _activity(activity):
    _exact_keys(activity, ["id", "kind", "uses", "generates", "algorithm", "parameters", "assumptions", "responsible_agent"], ["rate_mapping"], "activity")
    _token(activity["id"], "activity.id")
    if activity["kind"] not in ("resample", "process", "inject_silence", "analyze", "render"):
        _fail("activity.kind not supported")
    _ordered_tokens(activity["uses"], "activity.uses", 8)
    _ordered_tokens(activity["generates"], "activity.generates", 8)
    if set(activity["uses"]) & set(activity["generates"]):
        _fail("activity may not consume and regenerate the same entity id")
    _exact_keys(activity["algorithm"], ["id", "version"], where="algorithm")
    _token(activity["algorithm"]["id"], "algorithm.id")
    _token(activity["algorithm"]["version"], "algorithm.version")
    _map_string(activity["parameters"], "parameters")
    _list(activity["assumptions"], "assumptions", 0, 16)
    for a in activity["assumptions"]:
        _token(a, "assumption")
    if len(set(activity["assumptions"])) != len(activity["assumptions"]):
        _fail("duplicate assumption")
    if activity["responsible_agent"] is not None:
        _token(activity["responsible_agent"], "responsible_agent")
    if activity["kind"] == "resample":
        if "rate_mapping" not in activity:
            _fail("resampling requires rate_mapping")
    elif "rate_mapping" in activity:
        _fail("rate_mapping only valid for resample")


def validate_graph(graph: dict) -> None:
    """Reject contradictions, malformed metadata, non-DAG lineage and unsafe scope.

    Does not verify execution, file contents, sensor time, or authenticity.
    """
    _exact_keys(graph, ["schema", "entities", "activities", "agents"], where="graph")
    if graph["schema"] != SCHEMA:
        _fail("unknown graph schema")
    _list(graph["entities"], "entities", 1, MAX_ENTITIES)
    _list(graph["activities"], "activities", 0, MAX_ACTIVITIES)
    _list(graph["agents"], "agents", 0, MAX_AGENTS)
    # Restrict wire inputs to narrow deterministic JSON subset; no float, huge
    # JSON integers, hidden byte arrays or untyped objects.
    def walk(obj, depth=0):
        if depth > 24:
            _fail("maximum nesting exceeded")
        if type(obj) is dict:
            for key, v in obj.items():
                if type(key) is not str or key in BAD_KEYS or SENSITIVE.search(key):
                    _fail("unsafe metadata key")
                walk(v, depth + 1)
        elif type(obj) is list:
            for v in obj:
                walk(v, depth + 1)
        elif obj is not None and type(obj) not in (str, int):
            _fail("unsupported JSON scalar (float/bool/binary)")
        elif type(obj) is str and (len(obj) > 512 or SENSITIVE.search(obj)):
            _fail("overlong or potentially sensitive metadata")
    walk(graph)
    if type(graph["schema"]) is not str:
        _fail("invalid schema")
    entities = {}
    for e in graph["entities"]:
        _kind(e)
        if e["id"] in entities:
            _fail("duplicate entity id")
        entities[e["id"]] = e
    activities = {}
    for a in graph["activities"]:
        _activity(a)
        if a["id"] in entities or a["id"] in activities:
            _fail("duplicate graph identifier")
        activities[a["id"]] = a
    agents = {}
    for agent in graph["agents"]:
        _exact_keys(agent, ["id", "role", "version"], where="agent")
        for key in ("id", "role", "version"):
            _token(agent[key], f"agent.{key}")
        if agent["id"] in entities or agent["id"] in activities or agent["id"] in agents:
            _fail("duplicate graph identifier")
        agents[agent["id"]] = agent
    producer = {}
    dependencies = {eid: set() for eid in entities}
    for a in graph["activities"]:
        kind = a["kind"]
        if a["responsible_agent"] is not None and a["responsible_agent"] not in agents:
            _fail("dangling responsible agent")
        for eid in a["uses"] + a["generates"]:
            if eid not in entities:
                _fail("dangling entity reference")
        for output in a["generates"]:
            if output in producer:
                _fail("multiple generating activities for one entity")
            producer[output] = a
            dependencies[output].update(a["uses"])
        for eid in a["uses"]:
            if eid in a["generates"]:
                _fail("self-dependency")
        ins = [entities[x] for x in a["uses"]]
        outs = [entities[x] for x in a["generates"]]
        expected_in, expected_out = {
            "resample": ("audio", "audio"), "process": ("audio", "audio"),
            "inject_silence": ("audio", "audio"), "analyze": ("audio", "analysis"),
            "render": ("analysis", "visualization")}[kind]
        if any(e["kind"] != expected_in for e in ins) or any(e["kind"] != expected_out for e in outs):
            _fail("incompatible activity input/output entity kinds")
        if kind in ("resample", "process", "inject_silence") and (len(ins) != 1 or len(outs) != 1):
            _fail("bounded audio transform must have one source and one output")
        if kind == "resample":
            src, dst = ins[0], outs[0]
            mapping = a["rate_mapping"]
            _exact_keys(mapping, ["source_entity", "target_entity", "up", "down", "source_anchor", "target_anchor"], "rate_mapping")
            if mapping["source_entity"] != src["id"] or mapping["target_entity"] != dst["id"]:
                _fail("rate mapping does not reference exact activity endpoints")
            up, down = _decimal(mapping["up"], "mapping.up", 100000, True), _decimal(mapping["down"], "mapping.down", 100000, True)
            if math.gcd(up, down) != 1 or Fraction(up, down) != _rate(dst["timebase"]["rate"]) / _rate(src["timebase"]["rate"]):
                _fail("rate mapping contradicts exact rates")
            source_start, source_end = (int(src["timebase"][i]) for i in ("start", "end"))
            dest_start, dest_end = (int(dst["timebase"][i]) for i in ("start", "end"))
            if (_decimal(mapping["source_anchor"], "source_anchor") != source_start or
                    _decimal(mapping["target_anchor"], "target_anchor") != dest_start):
                _fail("bounded resampler must anchor the first sample of each interval")
            if dest_end - dest_start != (source_end - source_start) * up // down + (((source_end - source_start) * up) % down != 0):
                _fail("output frame count contradicts ceil(N*up/down) policy")
            if src["timebase"]["epoch"] == dst["timebase"]["epoch"]:
                _fail("resampling requires a distinct destination epoch")
            if src["timebase"]["channels"] != dst["timebase"]["channels"]:
                _fail("resample may not silently reorder/remix channels")
        if kind in ("process", "inject_silence"):
            src, dst = ins[0], outs[0]
            st, dt = src["timebase"], dst["timebase"]
            if st["rate"] != dt["rate"] or st["clock_domain"] != dt["clock_domain"]:
                _fail("non-resampling activity cannot silently change rate/clock")
            # The bounded v1 model has no trim/padding/delay operation: only
            # one-to-one frame mapping is supported without resampling.
            source_frames = int(st["end"]) - int(st["start"])
            output_frames = int(dt["end"]) - int(dt["start"])
            if source_frames != output_frames:
                _fail("non-resampling transform changes frame count")
            offset = int(dt["start"]) - int(st["start"])
            declared_offset = a["parameters"].get("sample_offset")
            if (offset != 0 or declared_offset is not None) and declared_offset != str(offset):
                _fail("sample offset change requires exact signed decimal sample_offset")
            if a["parameters"].get("output_epoch", st["epoch"]) != dt["epoch"]:
                _fail("epoch change requires explicit output_epoch")
            if a["parameters"].get("output_format", st["sample_format"]) != dt["sample_format"]:
                _fail("sample format change requires explicit output_format")
            if kind == "process":
                label = ",".join(dt["channels"])
                if st["channels"] != dt["channels"] and a["parameters"].get("channel_map") != label:
                    _fail("channel identity reorder requires explicit channel_map")
                if "channel_map" in a["parameters"] and a["parameters"]["channel_map"] != label:
                    _fail("channel_map contradicts destination channel order")
            if kind == "inject_silence" and st["channels"] != dt["channels"]:
                _fail("injected silence cannot change channel identity")
            if kind == "inject_silence" and not any(x["status"] == "synthetic_silence" for x in dst["coverage"]):
                _fail("injected silence must be explicitly marked")
    for e in graph["entities"]:
        eid = e["id"]
        p = producer.get(eid)
        if e["kind"] == "audio":
            if e["origin"] == "source" and p is not None:
                _fail("source audio must not claim a generating activity")
            if e["origin"] == "derived" and p is None:
                _fail("derived audio has no generating activity")
        elif p is None:
            _fail("analysis/visualization must have generating activity")
        if e["kind"] == "analysis":
            if p["kind"] != "analyze":
                _fail("analysis requires analyze activity")
            for basis in e["basis"]:
                ref = basis["entity"]
                if ref not in p["uses"] or entities[ref]["kind"] != "audio":
                    _fail("analysis basis must refer to used audio entity")
                tb = entities[ref]["timebase"]
                if not int(tb["start"]) <= int(basis["start"]) < int(basis["end"]) <= int(tb["end"]):
                    _fail("analysis basis outside declared audio timebase")
    colors = {}
    def visit(eid):
        if colors.get(eid) == 1:
            _fail("provenance cycle")
        if colors.get(eid) == 2:
            return
        colors[eid] = 1
        for parent in dependencies[eid]:
            visit(parent)
        colors[eid] = 2
    for eid in entities:
        visit(eid)
    # Every artifact must preserve visible quality-affecting lineage; inherit
    # conservatively across all inputs rather than making silence disappear.
    memo = {}
    def quality(eid):
        if eid in memo:
            return memo[eid]
        e = entities[eid]
        observed = set(e.get("limitations", []))
        if e["kind"] == "audio":
            observed.update(seg["status"] for seg in e["coverage"] if seg["status"] in FLAGS)
        for parent in dependencies[eid]:
            observed |= quality(parent)
        memo[eid] = observed
        return observed
    for eid, e in entities.items():
        needed = quality(eid) & {"gap", "truncated", "synthetic_silence", "unknown", "unknown_origin"}
        if not needed <= set(e["limitations"]):
            _fail(f"{eid}: output silently drops non-observed/unknown lineage")
    if len(json.dumps(graph, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")) > MAX_BYTES:
        _fail("provenance graph exceeds bounded byte limit")


def canonical_bytes(graph: dict) -> bytes:
    """Custom deterministic UTF-8 sorted-key JSON, NOT RFC 8785/JCS.

    Array order and Unicode codepoints are meaningful; never normalize.
    Values are schema-restricted, so floats and native binary are forbidden.
    """
    validate_graph(graph)
    return json.dumps(graph, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def graph_fingerprint(graph: dict) -> str:
    """SHA-256 of serialized claim *record*, not original audio bytes or truth."""
    return sha256(canonical_bytes(graph)).hexdigest()


def _unique_pairs(pairs):
    obj = {}
    for k, v in pairs:
        if k in obj:
            _fail("duplicate JSON object key")
        obj[k] = v
    return obj


def parse_graph(raw: bytes) -> dict:
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        _fail("invalid/oversized JSON bytes")
    try:
        record = json.loads(raw.decode("utf-8", errors="strict"),
                            object_pairs_hook=_unique_pairs,
                            parse_float=lambda _: _fail("floating JSON number is forbidden"),
                            parse_constant=lambda _: _fail("nonfinite JSON number forbidden"))
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ProvenanceError("invalid JSON provenance") from exc
    validate_graph(record)
    return record


def verify_entity_bytes(graph: dict, entity_id: str, content: bytes) -> dict:
    """Compare actual supplied bytes with a *declared* digest only.

    Does not establish who supplied bytes, physical origin or truth of analysis.
    """
    validate_graph(graph)
    if type(content) is not bytes:
        _fail("byte verification requires actual byte sequence")
    entities = {e["id"]: e for e in graph["entities"]}
    if entity_id not in entities:
        _fail("entity not found")
    ident = entities[entity_id]["identity"]
    actual = sha256(content).hexdigest()
    expected = ident["sha256_claim"]
    return {"entity": entity_id, "status": "unclaimed" if expected is None else
            ("matches_claim" if actual == expected else "mismatch"),
            "actual_sha256": actual, "claimed_sha256": expected,
            "scope": ident["scope"]}


def inspect_lineage(graph: dict, entity_id: str) -> dict:
    """Conservative declared lineage and exposure, never proof of reproducibility."""
    validate_graph(graph)
    entities = {e["id"]: e for e in graph["entities"]}
    if entity_id not in entities:
        _fail("entity not found")
    generating = {eid: a for a in graph["activities"] for eid in a["generates"]}
    visited = set()
    ordered_activities = []
    risks = set()
    input_entities = set()
    def walk(eid):
        if eid in visited:
            return
        visited.add(eid)
        e = entities[eid]
        risks.update(e["limitations"])
        if e["kind"] == "audio":
            risks.update(s["status"] for s in e["coverage"] if s["status"] in FLAGS)
            if e["origin"] == "source":
                input_entities.add(eid)
                # Even a syntactically valid SHA-256 *claim* has never been
                # tested against source bytes by this lineage query.
                risks.add("unverified_content")
        if eid in generating:
            a = generating[eid]
            for parent in a["uses"]:
                walk(parent)
            if a["id"] not in ordered_activities:
                ordered_activities.append(a["id"])
    walk(entity_id)
    return {"entity": entity_id, "upstream_entities": sorted(visited),
            "source_entities": sorted(input_entities),
            "activities": ordered_activities, "limitations": sorted(risks),
            "reproducible": "not_demonstrated", "record_sha256": graph_fingerprint(graph)}
