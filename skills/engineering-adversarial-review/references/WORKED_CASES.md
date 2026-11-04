# Worked adversarial cases — synthetic, bounded teaching fixtures

These cases are deliberately synthetic and **not** claims about Kestrel's real application code or shipped math procedures. Execute from repository root:

```sh
python3 skills/engineering-adversarial-review/scripts/fixture_probe.py
python3 -m unittest tests/test_engineering_adversarial_review.py -v
```

The fixture probe imports files under `fixtures/baseline/` and `fixtures/head/`. It does not edit them, run a network command or change any application. Its fixed independent acceptance rules are in the probe, not imported from the head implementation. Fixture tests demonstrate **detectability**; they are not evidence that an LLM auditor will detect the defects.

## A: All unit checks green, cross-boundary invariant broken

**Accepted contract:** Names written using one spelling must be retrievable using any case variant; both storage and lookup normalize case.

- Baseline: `put("Alpha", 7)` and `get("ALPHA")` returns `7`.
- Head: `get` no longer normalizes the lookup key, yet lower-case unit checks still pass.
- Independent oracle: perform write-read using differing case, not a same-case mock.
- Expected finding: new cross-boundary regression in `head/case_a.py`. Minimum fix: restore symmetric normalization, add cross-boundary acceptance test.
- Tempting wrong review: "All tests green, names can be retrieved." The unit fixtures use a non-discriminating lowercase input.

## B: A weakened tolerance hides a wrong answer

**Accepted contract:** `gain(1.0)` equals `2.0` within an absolute error of `1e-9`, independently recorded before the diff.

- Baseline: multiplication by `2.0` with `TOLERANCE=1e-9`.
- Head: multiplication by `2.04` plus widening `TOLERANCE` to `0.1`. The amended unit test passes.
- Independent oracle: expected value `2.0` and locked `1e-9` tolerance, checked without reading the head's tolerance.
- Expected finding: new accuracy regression plus test-integrity violation; severity depends on the real application's importance.
- Tempting wrong review: "Unit suite is green; the changed tolerance is part of the implementation." Acceptance tolerances require independent justification.

## C: A real failure that was *not introduced* by the PR

**Accepted contract:** Decoding empty CSV produces an empty list, `[]`.

- Baseline and head: `decode_csv("")` both return `None` (a pre-existing defect).
- Head changes `encode_csv` only; decoder is unchanged and normal-input unit checks pass.
- Independent oracle finds the defect in **both** revisions.
- Expected review: a separate pre-existing issue or scope-appropriate note, **not** a regression attributed to this PR.
- Tempting wrong review: "The latest PR broke empty input." The timeline does not support that claim.

## D: Clean decoy with misleading comment

**Accepted contract:** `double_integer(n)` for integers in `[-100,100]` returns the exact mathematical double.

- Baseline: `n+n`; head: `2*n`. Head contains a misleading `FIXME` comment claiming negatives are unsafe.
- Independent oracle: exact integer doubling across declared domain. Both pass; there is no confirmed defect.
- Expected review: **no finding**; optional note that comment contradicts code, but not a functional bug.
- Tempting wrong review: invent a bug because the comment or a planted warning says one exists.

## Interpreting results

The passing fixture suite establishes only that the fixed synthetic specimens exhibit their declared outcomes and that a separate checking procedure can discriminate them. It does not establish reliable autonomous review on arbitrary PRs, real-world regression attribution, or correctness outside the toy domains. Behavioral evaluation must supply fresh, varied tasks with answer keys withheld from the participant.
