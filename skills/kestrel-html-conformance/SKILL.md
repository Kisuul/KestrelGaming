---
name: kestrel-html-conformance
description: Create, modify, or review HTML for Kestrel. Write standards-conforming markup, run the official W3C Nu Html Checker on the exact deliverables, remediate diagnostics, and refuse to claim validation success without a completed zero-error check.
---

# Lesson 1 — Writing HTML compliant with the W3C Nu Validator

## When to activate

Use for any task that **creates, changes, generates, templates, or ships HTML** (including `.html`, `.htm`, `.xhtml`, `.xht`, single-file applications, server-generated pages, and HTML rendered from templates). Read this before editing markup. The goal is an operational, repeatable *validation gate*, not a claim that a checker can prove every aspect of Web conformance.

## Required procedure

1. **Identify the real artifact.** Locate source HTML and the exact emitted/deployed HTML, templates, render paths, and build steps. Identify which URLs, routes, or states emit distinct documents. Record what is in scope. Never infer validity from source templates alone when rendering can change markup.
2. **Author clean HTML.** Use the HTML doctype for HTML documents; specify document language and character encoding; provide a meaningful `<title>` and viewport metadata as appropriate. Use semantic elements and headings, valid parent/child content models, correct nesting and closing rules, unique IDs, supported attributes and values, labeled form controls, and meaningful image alternatives. Encode `&` and `<` when required in text or attributes, quote attribute values, and avoid obsolete presentational markup. For `.xhtml`/`.xht`, preserve XML well-formedness and correct MIME/grammar; do not force the HTML parser. Where user intent requires custom elements or unusual attributes, check applicable standards rather than guessing.
3. **Select the official checker.** Prefer a locally installed [Nu Html Checker](https://github.com/validator/validator) (`vnu` or official `vnu.jar`), especially for private code and repeatable CI; use the [W3C hosted checker](https://validator.w3.org/nu/) for authorized public/non-sensitive material or an approved self-hosted service. Verify checker availability; do not replace it with a regex, browser render, linter, or self-assessment. Do not silently fetch/install dependencies or upload private HTML to third-party services.
4. **Validate the actual output.** Build first when applicable. Run the [fail-closed wrapper](scripts/check_html.py) against explicit files or the output directory. Confirm nonempty scope, the command and checker used, output revision/build, and exit status. For dynamic routes, authenticated responses, or browser-mutated markup, obtain representative **rendered** documents under authorized conditions and validate each; do not treat checking a base template as checking its output. Document any routes/states not exercised.
5. **Repair and repeat.** Fix **all error-level diagnostics**, then rerun the *full affected set*, not only the file that initially failed. Investigate each warning; resolve those that affect correctness or the requirements. Never use `--exit-zero-always`, ignore/filter rules, suppressed error levels, or blanket exemptions to turn failures green. If a checker cannot run, crashes, times out, or cannot inspect a document, classify the result **INDETERMINATE / BLOCKED**, not passed. If the warning policy is strict, use `--warnings-as-errors`.
6. **Gate delivery.** Only report **VALIDATED** when the official checker actually ran successfully over a nonempty, enumerated set of final artifacts with zero reported errors; include files/routes checked, checker/version when available, command, result, and omissions. If material output was untested or generated after the last check, status is **PARTIAL / UNVERIFIED**, not validated. Require a project CI validation gate for ongoing HTML work; preserve project-local policy and inspect changes to CI separately.

## Commands

From a checkout where this repository is available, with `vnu` on PATH:

```sh
python3 /path/to/KestrelGaming/skills/kestrel-html-conformance/scripts/check_html.py dist/
```

Or with the [official `vnu.jar`](https://github.com/validator/validator/releases/tag/latest) and Java 17+:

```sh
python3 /path/to/KestrelGaming/skills/kestrel-html-conformance/scripts/check_html.py --jar /path/to/vnu.jar dist/index.html
```

Optional stricter gate: append `--warnings-as-errors`. Use actual paths. HTML embedded inside strings (`.js`, `.py`, etc.) must be **materialized into HTML documents** before checking. If generated HTML cannot be enumerated or extracted, disclose the gap; do not claim complete coverage.

## Acceptance criterion and evidence

**Pass** = official Nu checker ran to completion with exit code 0 over all enumerated, final HTML documents, without suppressing errors. The wrapper fails closed for missing checker, missing inputs, and empty matches. **Fail** = any validator error or nonzero checker result. **Indeterminate** = checker unavailable or unable to give reliable evidence. Warnings are reported and investigated, but are not automatically conformance failures unless strict mode/policy requires it.

Record: target repo/commit; source vs built/routed output; files and route/state coverage; checker distribution/version and invocation; number checked; pass/fail/indeterminate; unresolved warnings and gaps. Revalidate whenever emitted markup changes. The official checker itself explicitly [does not offer certification or a perpetual guarantee](https://validator.nu/about.html); passing this gate is **evidence of a successful check at that revision**, not proof of accessibility, security, visual correctness, or every specification requirement.

For examples, CI integration, diagnostic policy, and evaluation cases, read [validation reference](references/VALIDATION.md). Follow Kestrel's [verification contract](../../kestrel/VERIFICATION.md) and [permissions guidance](../../kestrel/PERMISSIONS.md).
