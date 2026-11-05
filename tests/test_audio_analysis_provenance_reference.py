"""Analytic and adversarial fixtures for bounded audio provenance declarations."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/audio-analysis-provenance/scripts"))
from reference_provenance import (
    SCHEMA, ProvenanceError, validate_graph, canonical_bytes, graph_fingerprint,
    parse_graph, verify_entity_bytes, inspect_lineage,
)

BASE = 2**54 + 23
SOURCE_BYTES = b"public-std-lib-test-vector-8-frames"


def audio(identifier, origin, start, end, rate, epoch, clock, coverage, limits, channels=None, claim=None):
    return {
        "id": identifier, "kind": "audio", "origin": origin,
        "identity": {"declared_id": identifier if origin == "source" else None,
                     "sha256_claim": claim, "scope": "synthetic_pcm_bytes" if claim else None},
        "timebase": {"epoch": epoch, "clock_domain": clock,
                     "rate": {"num": str(rate), "den": "1"},
                     "start": str(start), "end": str(end),
                     "channels": ["l", "r"] if channels is None else channels,
                     "sample_format": "f32-planar"},
        "coverage": [{"start": str(a), "end": str(b), "status": kind}
                     for a, b, kind in coverage], "limitations": limits[:],
    }


def activity(identifier, kind, uses, generates, parameters, rate_mapping=None):
    result = {"id": identifier, "kind": kind, "uses": uses[:],
              "generates": generates[:], "algorithm": {"id": kind + "-v1", "version": "v1.0.0"},
              "parameters": parameters, "assumptions": ["nominal-clocks"],
              "responsible_agent": "dsp-agent"}
    if rate_mapping is not None:
        result["rate_mapping"] = rate_mapping
    return result


def fixture():
    src = audio("e_src", "source", BASE, BASE + 8, 44100, "capture-e1", "decoded-44100",
                [(BASE, BASE + 4, "observed"), (BASE + 4, BASE + 5, "gap"),
                 (BASE + 5, BASE + 8, "synthetic_silence")],
                ["gap", "synthetic_silence"], claim=sha256(SOURCE_BYTES).hexdigest())
    buf = audio("e_src_48k", "derived", 100, 109, 48000, "analysis-e2", "analysis-48000",
                [(100, 109, "derived")], ["gap", "synthetic_silence"])
    measured = {
        "id": "e_psd", "kind": "analysis", "identity": {"declared_id": "psd-result", "sha256_claim": None, "scope": None},
        "measurement": {"quantity": "power_spectral_density", "unit": "fs2_per_hz",
                        "normalization": "density", "uncertainty": {"state": "unquantified", "description": "no-calibration-available", "bound": None, "bound_unit": None}},
        "basis": [{"entity": "e_src_48k", "start": "100", "end": "109"}],
        "limitations": ["gap", "synthetic_silence", "uncertainty_unquantified"],
    }
    visual = {"id": "e_waterfall", "kind": "visualization",
              "identity": {"declared_id": None, "sha256_claim": None, "scope": None},
              "display": {"kind": "waterfall", "x_unit": "s", "y_unit": "db_fs2_per_hz", "transform": "db10", "db_reference": "one-fs2-per-hz"},
              "limitations": ["gap", "synthetic_silence", "uncertainty_unquantified"]}
    mapping = {"source_entity": "e_src", "target_entity": "e_src_48k", "up": "160", "down": "147",
               "source_anchor": str(BASE), "target_anchor": "100"}
    return {"schema": SCHEMA, "entities": [src, buf, measured, visual],
            "activities": [activity("a_src", "resample", ["e_src"], ["e_src_48k"],
                                    {"filter": "kaiser", "up": "160", "down": "147"}, mapping),
                           activity("a_analysis", "analyze", ["e_src_48k"], ["e_psd"],
                                    {"nfft": "8", "window": "hann", "scaling": "density"}),
                           activity("a_render", "render", ["e_psd"], ["e_waterfall"],
                                    {"color_map": "viridis", "gamma": "1"})],
            "agents": [{"id": "dsp-agent", "role": "software", "version": "v1.0.0"}]}


class ProvenanceTests(unittest.TestCase):
    def assertBad(self, graph):
        with self.assertRaises(ProvenanceError):
            validate_graph(graph)

    def test_source_analysis_visualization_lineage(self):
        rec = fixture()
        validate_graph(rec)
        audit = inspect_lineage(rec, "e_waterfall")
        self.assertEqual(audit["source_entities"], ["e_src"])
        self.assertEqual(audit["activities"], ["a_src", "a_analysis", "a_render"])
        self.assertEqual(set(audit["limitations"]), {"gap", "synthetic_silence", "uncertainty_unquantified", "unverified_content"})
        self.assertEqual(audit["reproducible"], "not_demonstrated")
        self.assertEqual(audit["upstream_entities"], ["e_psd", "e_src", "e_src_48k", "e_waterfall"])

    def test_exact_rational_clock_mapping_across_2pow53(self):
        rec = fixture()
        validate_graph(rec)
        src = rec["entities"][0]["timebase"]
        target = rec["entities"][1]["timebase"]
        self.assertEqual(Fraction(int(target["rate"]["num"]), int(src["rate"]["num"])), Fraction(160, 147))
        self.assertEqual(Fraction(8*160, 147), Fraction(1280, 147))
        self.assertEqual(int(target["end"]) - int(target["start"]), 9)
        self.assertEqual(int(src["start"]), BASE)
        self.assertNotEqual(src["epoch"], target["epoch"])
        self.assertNotEqual(src["clock_domain"], target["clock_domain"])
        self.assertEqual(int(src["end"]) - int(src["start"]), 8)

    def test_reordered_map_keys_have_identical_record_bytes(self):
        first = fixture()
        second = json.loads(json.dumps(first))
        def reverse_map(obj):
            if type(obj) is dict:
                return {key: reverse_map(value) for key, value in reversed(list(obj.items()))}
            return [reverse_map(x) for x in obj] if type(obj) is list else obj
        second = reverse_map(second)
        self.assertEqual(canonical_bytes(first), canonical_bytes(second))
        self.assertEqual(graph_fingerprint(first), graph_fingerprint(second))
        self.assertEqual(parse_graph(canonical_bytes(second)), first)

    def test_changed_algorithm_parameters_change_record_digest(self):
        before = fixture()
        after = deepcopy(before)
        after["activities"][1]["parameters"]["window"] = "blackman"
        validate_graph(after)
        self.assertNotEqual(graph_fingerprint(before), graph_fingerprint(after))
        self.assertNotEqual(canonical_bytes(before), canonical_bytes(after))

    def test_content_digest_claim_requires_actual_bytes(self):
        rec = fixture()
        before = inspect_lineage(rec, "e_src")
        self.assertEqual(before["reproducible"], "not_demonstrated")
        self.assertIn("unverified_content", before["limitations"])
        good = verify_entity_bytes(rec, "e_src", SOURCE_BYTES)
        self.assertEqual(good["status"], "matches_claim")
        self.assertEqual(good["actual_sha256"], sha256(SOURCE_BYTES).hexdigest())
        self.assertEqual(verify_entity_bytes(rec, "e_src", SOURCE_BYTES + b"tampered")["status"], "mismatch")
        self.assertEqual(verify_entity_bytes(rec, "e_src_48k", b"any bytes")["status"], "unclaimed")
        self.assertEqual(inspect_lineage(rec, "e_waterfall")["reproducible"], "not_demonstrated")

    def test_display_transform_changes_only_record_fingerprint(self):
        rec = fixture()
        after = deepcopy(rec)
        after["entities"][3]["display"]["gamma"] = "2"
        self.assertNotEqual(graph_fingerprint(rec), graph_fingerprint(after))
        self.assertEqual(rec["entities"][2], after["entities"][2])
        self.assertEqual(verify_entity_bytes(rec, "e_src", SOURCE_BYTES)["status"], "matches_claim")

    def test_missing_origin_still_traceable_not_authentic(self):
        rec = fixture()
        rec["entities"][0]["identity"] = {"declared_id": None, "sha256_claim": None, "scope": None}
        for e in rec["entities"]:
            e["limitations"].append("unknown_origin")
        validate_graph(rec)
        summary = inspect_lineage(rec, "e_waterfall")
        self.assertIn("unknown_origin", summary["limitations"])
        self.assertIn("unverified_content", summary["limitations"])
        self.assertEqual(summary["reproducible"], "not_demonstrated")

    def test_source_segments_cannot_have_hidden_gap(self):
        rec = fixture()
        rec["entities"][0]["coverage"][1] = {"start":str(BASE+5), "end":str(BASE+6), "status":"gap"}
        self.assertBad(rec)
        rec = fixture()
        rec["entities"][0]["coverage"][1]["end"] = str(BASE+6)
        self.assertBad(rec)
        rec = fixture()
        rec["entities"][0]["coverage"][2]["end"] = str(BASE+7)
        self.assertBad(rec)

    def test_provenance_flags_are_transitive_and_mandatory(self):
        for index in (1, 2, 3):
            rec = fixture()
            rec["entities"][index]["limitations"].remove("gap")
            with self.subTest(index=index):
                self.assertBad(rec)
        for index in (1, 2, 3):
            rec = fixture()
            rec["entities"][index]["limitations"].remove("synthetic_silence")
            with self.subTest(index=index):
                self.assertBad(rec)

    def test_truncation_cannot_disappear_in_chain(self):
        rec = fixture()
        src = rec["entities"][0]
        src["coverage"][-1] = {"start":str(BASE+5),"end":str(BASE+8),"status":"truncated"}
        src["limitations"] = ["gap", "truncated"]
        for e in rec["entities"][1:]:
            e["limitations"] = ["gap", "truncated"] + (["uncertainty_unquantified"] if e["kind"]=="analysis" else [])
        validate_graph(rec)
        self.assertIn("truncated", inspect_lineage(rec,"e_waterfall")["limitations"])

    def test_rate_mismatch_and_wrong_sample_count_fail(self):
        changes = (
            lambda x:x["activities"][0]["rate_mapping"].update({"up":"147","down":"160"}),
            lambda x:x["entities"][1]["timebase"].update({"end":"108"}),
            lambda x:x["entities"][1]["timebase"].update({"rate":{"num":"47999","den":"1"}}),
            lambda x:x["activities"][0]["rate_mapping"].update({"source_anchor":"0"}),
            lambda x:x["entities"][1]["timebase"].update({"epoch":"capture-e1"}),
            lambda x:x["entities"][1]["timebase"].update({"channels":["r","l"]}),
        )
        for change in changes:
            rec = fixture()
            change(rec)
            with self.subTest(change=change):
                self.assertBad(rec)

    def test_basis_range_cannot_cross_unowned_entity_or_interval(self):
        for invalid in ({"entity":"e_src","start":str(BASE),"end":str(BASE+2)},
                        {"entity":"e_src_48k","start":"99","end":"102"},
                        {"entity":"e_src_48k","start":"100","end":"110"},
                        {"entity":"e_src_48k","start":"101","end":"101"}):
            rec=fixture()
            rec["entities"][2]["basis"][0]=invalid
            with self.subTest(invalid=invalid):self.assertBad(rec)

    def test_broken_links_and_missing_agent_fail(self):
        rec=fixture();rec["activities"][2]["uses"]=["missing"];self.assertBad(rec)
        rec=fixture();rec["activities"][2]["responsible_agent"]="not-registered";self.assertBad(rec)
        rec=fixture();rec["activities"][0]["generates"]=["missing"];self.assertBad(rec)
        rec=fixture();rec["entities"][1]["origin"]="source";self.assertBad(rec)

    def test_duplicate_entity_activity_agent_identifiers_fail(self):
        rec=fixture();rec["entities"][1]["id"]="e_src";self.assertBad(rec)
        rec=fixture();rec["activities"][1]["id"]="a_src";self.assertBad(rec)
        rec=fixture();rec["agents"][0]["id"]="e_src";self.assertBad(rec)
        rec=fixture();rec["activities"][1]["id"]="e_src";self.assertBad(rec)

    def test_provenance_cycle_rejected_even_with_valid_entity_kinds(self):
        rec=fixture()
        # Create a cycle across two DERIVED audio nodes under process activities.
        a=audio("e_a","derived",0,4,44100,"e-a","clock",[(0,4,"derived")],[])
        b=audio("e_b","derived",0,4,44100,"e-b","clock",[(0,4,"derived")],[])
        rec={"schema":SCHEMA,"entities":[a,b],"activities":[
            activity("a1","process",["e_a"],["e_b"],{}),
            activity("a2","process",["e_b"],["e_a"],{})],"agents":[{"id":"dsp-agent","role":"software","version":"v1"}]}
        self.assertBad(rec)

    def test_channel_reordering_must_have_explicit_mapping(self):
        rec=fixture()
        rec["activities"][0]["kind"]="process"
        rec["activities"][0].pop("rate_mapping")
        rec["entities"][1]["timebase"]["rate"]={"num":"44100","den":"1"}
        rec["entities"][1]["timebase"]["clock_domain"]="decoded-44100"
        rec["entities"][1]["timebase"]["channels"]=["r","l"]
        self.assertBad(rec)
        rec["activities"][0]["parameters"]["channel_map"]="r,l"
        validate_graph(rec)

    def test_synthetic_silence_activity_requires_explicit_segment(self):
        rec=fixture()
        rec["activities"][0]["kind"]="inject_silence"
        rec["activities"][0].pop("rate_mapping")
        rec["entities"][1]["timebase"]["rate"]={"num":"44100","den":"1"}
        rec["entities"][1]["timebase"]["clock_domain"]="decoded-44100"
        self.assertBad(rec)
        rec["entities"][1]["coverage"]=[{"start":"100","end":"109","status":"synthetic_silence"}]
        validate_graph(rec)

    def test_reject_noncanonical_decimal_rate_and_implicit_float(self):
        for replacement in ("01","1.0","-1","0","999999999999999999999999999"):
            rec=fixture();rec["entities"][0]["timebase"]["rate"]["den"]=replacement
            with self.subTest(value=replacement):self.assertBad(rec)
        rec=fixture();rec["activities"][1]["parameters"]["nfft"]=8;self.assertBad(rec)
        rec=fixture();rec["activities"][1]["parameters"]["gain"]=float("nan");self.assertBad(rec)

    def test_duplicate_json_keys_and_invalid_utf8_rejected(self):
        payload=canonical_bytes(fixture())
        corrupted=payload.replace(b'"schema":',b'"schema":"malicious","schema":',1)
        with self.assertRaises(ProvenanceError):parse_graph(corrupted)
        with self.assertRaises(ProvenanceError):parse_graph(b'\xff')
        with self.assertRaises(ProvenanceError):parse_graph(b'{}')
        with self.assertRaises(ProvenanceError):parse_graph(payload + b'garbage')

    def test_privacy_sensitive_metadata_rejected(self):
        for value in ("/home/user/recording.wav","C:\\private\\audio.wav","operator@example.org"):
            rec=fixture();rec["activities"][1]["parameters"]["source"]=value
            with self.subTest(value=value):self.assertBad(rec)
        rec=fixture();rec["activities"][1]["parameters"]["password"]="not-a-real-secret";self.assertBad(rec)
        rec=fixture();rec["entities"][0]["identity"]["declared_id"]="/var/private.wav";self.assertBad(rec)

    def test_claimed_identifier_not_digest_and_no_truth_certification(self):
        rec=fixture()
        rec["entities"][0]["identity"]["sha256_claim"]=None
        rec["entities"][0]["identity"]["scope"]=None
        validate_graph(rec)
        self.assertEqual(verify_entity_bytes(rec,"e_src",SOURCE_BYTES)["status"],"unclaimed")
        self.assertEqual(inspect_lineage(rec,"e_waterfall")["reproducible"],"not_demonstrated")
        self.assertIn("unverified_content",inspect_lineage(rec,"e_waterfall")["limitations"])

    def test_invalid_version_or_undeclared_measurement_failure(self):
        rec=fixture();rec["schema"]="v2";self.assertBad(rec)
        rec=fixture();rec["entities"][2]["measurement"].pop("unit");self.assertBad(rec)
        rec=fixture();rec["entities"][2]["measurement"]["uncertainty"]["state"]="unknown"
        rec["entities"][2]["limitations"].remove("uncertainty_unquantified");self.assertBad(rec)
        rec=fixture();rec["activities"][1]["algorithm"].pop("version");self.assertBad(rec)

    def test_quantified_uncertainty_requires_declared_exact_unit_bound(self):
        rec = fixture()
        unc = rec["entities"][2]["measurement"]["uncertainty"]
        unc.update({"state":"quantified", "description":"synthetic-absolute-bound",
                    "bound":{"num":"1","den":"1000"},"bound_unit":"fs2_per_hz"})
        rec["entities"][2]["limitations"].remove("uncertainty_unquantified")
        rec["entities"][3]["limitations"].remove("uncertainty_unquantified")
        validate_graph(rec)
        for bound, unit in [({"num":"1","den":"0"},"fs2_per_hz"),
                            ({"num":"2","den":"4"},"fs2_per_hz"),
                            ({"num":"1","den":"1000"},"fs"),
                            (None,"fs2_per_hz")]:
            case=deepcopy(rec)
            case["entities"][2]["measurement"]["uncertainty"].update({"bound":bound,"bound_unit":unit})
            with self.subTest(bound=bound,unit=unit): self.assertBad(case)
        case=fixture()
        case["entities"][2]["measurement"]["uncertainty"]["bound"]={"num":"1","den":"10"}
        self.assertBad(case)

    def test_only_predeclared_fields_allowed(self):
        rec=fixture();rec["entities"][2]["raw_audio"]=[0,1,2];self.assertBad(rec)
        rec=fixture();rec["secret"]="bogus";self.assertBad(rec)
        rec=fixture();rec["activities"][1]["use_partial_inputs"] = True;self.assertBad(rec)


    def test_injected_silence_must_not_change_channel_identity(self):
        rec = fixture()
        a = rec["activities"][0]
        a["kind"] = "inject_silence"
        a.pop("rate_mapping")
        src, dst = rec["entities"][:2]
        dst["timebase"] = deepcopy(src["timebase"])
        dst["timebase"]["channels"] = ["r", "l"]
        dst["coverage"] = [{"start":str(BASE),"end":str(BASE+8),"status":"synthetic_silence"}]
        with self.assertRaisesRegex(ProvenanceError, "channel"):
            validate_graph(rec)

    def test_nonresampling_process_must_not_invent_output_frames(self):
        rec = fixture()
        a = rec["activities"][0]
        a["kind"] = "process"
        a.pop("rate_mapping")
        src, dst = rec["entities"][:2]
        dst["timebase"] = deepcopy(src["timebase"])
        dst["timebase"]["end"] = str(BASE + 9)
        dst["coverage"] = [{"start":str(BASE),"end":str(BASE+9),"status":"derived"}]
        with self.assertRaisesRegex(ProvenanceError, "frame"):
            validate_graph(rec)

    def test_nonresampling_process_must_declare_sample_format_change(self):
        rec = fixture()
        a = rec["activities"][0]
        a["kind"] = "process"
        a.pop("rate_mapping")
        src, dst = rec["entities"][:2]
        dst["timebase"] = deepcopy(src["timebase"])
        dst["timebase"]["sample_format"] = "s16-interleaved"
        dst["coverage"] = [{"start":str(BASE),"end":str(BASE+8),"status":"derived"}]
        with self.assertRaisesRegex(ProvenanceError, "format"):
            validate_graph(rec)


if __name__ == "__main__":
    unittest.main()
