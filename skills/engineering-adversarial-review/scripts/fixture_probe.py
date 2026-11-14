#!/usr/bin/env python3
"""Read-only, stdlib-only synthetic adversarial-review fixture probe.

Run from any directory. Exit nonzero when the fixed expected contrast fails.
This tests fixtures, *not* an agent's review skill or any production code.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
ACCEPTED_GAIN = 2.0
ACCEPTED_GAIN_ABS_ERROR = 1e-9
SUPPORTED_INTEGERS = range(-100, 101)
CASES = ("a", "b", "c", "d")


def _hash_fixture_sources() -> dict[str, str]:
    return {str(path.relative_to(FIXTURES)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(FIXTURES.glob("*/case_*.py"))}


def _load(revision: str, case: str):
    path = FIXTURES / revision / f"case_{case}.py"
    spec = importlib.util.spec_from_file_location(f"review_fixture_{revision}_{case}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load fixture: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _unit_checks(case: str, module) -> bool:
    """Plausible local unit checks; intentionally insufficient in A/B/C."""
    if case == "a":
        store = module.NameStore()
        store.put("Alpha", 7)
        return store.get("alpha") == 7
    if case == "b":
        return abs(module.gain(1.0) - ACCEPTED_GAIN) <= module.TOLERANCE
    if case == "c":
        return (module.decode_csv("a,b") == ["a", "b"] and
                module.encode_csv(["a", "b"]) == "a,b")
    if case == "d":
        return module.double_integer(3) == 6
    raise AssertionError("Unknown fixture")


def _independent_acceptance(case: str, module) -> bool:
    """Independent, fixed expectations defined in WORKED_CASES.md."""
    if case == "a":
        store = module.NameStore()
        store.put("Alpha", 7)
        return store.get("ALPHA") == 7
    if case == "b":
        return abs(module.gain(1.0) - ACCEPTED_GAIN) <= ACCEPTED_GAIN_ABS_ERROR
    if case == "c":
        return module.decode_csv("") == []
    if case == "d":
        return all(type(module.double_integer(value)) is int and
                   module.double_integer(value) == 2 * value
                   for value in SUPPORTED_INTEGERS)
    raise AssertionError("Unknown fixture")


def evaluate() -> dict:
    before = _hash_fixture_sources()
    rows = []
    for case in CASES:
        base, head = _load("baseline", case), _load("head", case)
        b_unit, h_unit = _unit_checks(case, base), _unit_checks(case, head)
        b_accept = _independent_acceptance(case, base)
        h_accept = _independent_acceptance(case, head)
        if b_accept and not h_accept:
            classification = "introduced-regression"
        elif not b_accept and not h_accept:
            classification = "pre-existing-defect"
        elif b_accept and h_accept:
            classification = "no-confirmed-defect"
        else:
            classification = "baseline-only-failure-resolved"
        rows.append({"case": case.upper(), "baseline_unit_green": b_unit,
                     "head_unit_green": h_unit,
                     "baseline_acceptance": b_accept,
                     "head_acceptance": h_accept,
                     "classification": classification})
    if before != _hash_fixture_sources():
        raise RuntimeError("Fixture inputs unexpectedly changed during probe")
    return {"fixture_set": "synthetic-only", "rows": rows,
            "read_only_source_check": "PASS"}


EXPECTED = {
    "A": (True, True, True, False, "introduced-regression"),
    "B": (True, True, True, False, "introduced-regression"),
    "C": (True, True, False, False, "pre-existing-defect"),
    "D": (True, True, True, True, "no-confirmed-defect"),
}


def verified(result: dict) -> bool:
    return all((row["baseline_unit_green"], row["head_unit_green"],
                row["baseline_acceptance"], row["head_acceptance"],
                row["classification"]) == EXPECTED[row["case"]]
               for row in result["rows"]) and len(result["rows"]) == len(EXPECTED)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="JSON instead of table")
    args = parser.parse_args()
    result = evaluate()
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("SYNTHETIC ONLY — not a real code audit or behavioral evaluation")
        for row in result["rows"]:
            print(f"{row['case']}: units {row['baseline_unit_green']}/{row['head_unit_green']}, "
                  f"acceptance {row['baseline_acceptance']}/{row['head_acceptance']}, "
                  f"{row['classification']}")
        print("Read-only fixture content:", result["read_only_source_check"])
    return 0 if verified(result) else 1


if __name__ == "__main__":
    raise SystemExit(main())
