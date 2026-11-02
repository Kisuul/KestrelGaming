# Lesson 1 reference — author, validate, enforce

## Checker provenance

- [W3C Nu Html Checker](https://validator.w3.org/nu/) — interactive checking for HTML.
- [Official upstream source, releases and CLI](https://github.com/validator/validator) and [CLI option reference](https://github.com/validator/validator/blob/master/docs/vnu.1.md).
- [W3C HTML Checker programmatic API](https://validator.w3.org/docs/api.html) and [upstream POST-body API](https://github.com/validator/validator/wiki/Service-%C2%BB-Input-%C2%BB-POST-body): if authorized to send source to an HTTP service, POST the document bytes with `Content-Type: text/html; charset=utf-8` and `?out=json`. Interpret `type=error` as failure and `type=non-document-error` as indeterminate; warnings are informational unless local policy makes them fatal. Do not mistake a transport HTTP 200 for successful validation.
- [Checker limits](https://validator.nu/about.html) — errors and checks evolve; clean output is not certification.

## Starter document

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Example page</title>
</head>
<body>
  <main>
    <h1>Example page</h1>
    <p>Meaningful content.</p>
  </main>
</body>
</html>
```

It is a starter, not a substitute for checking actual generated pages. Even valid HTML is not proof of WCAG conformance, keyboard access, or correct app behavior.

## Typical repairs

| Diagnostic family | Investigation and repair |
| --- | --- |
| Invalid nesting or content model | Find the first bad parent/child relationship; repair markup at its source, not the browser-corrected DOM |
| Duplicate `id` | Give each element a stable unique identifier; update labels, fragment links and JS selectors |
| Invalid/obsolete attribute or element | Consult current HTML Standard and Nu messages; replace with conforming markup and CSS |
| Missing accessible name or alternative | Connect labels to inputs; provide task-appropriate `alt` text or empty `alt` for purely decorative images |
| Unescaped special character | Escape literal ampersands in URLs/attributes where required; escape less-than characters in text |
| Template/generator diagnostics | Repair the generator, rebuild, then validate produced HTML across representative states |

## Project-owned CI example

Use a locally available, reviewed and preferably version-pinned official Nu checker. The **target project's** CI should install or provision that checker in a controlled step. Then run a gate **after** the project's HTML build. This repository does not automatically modify other projects' CI.

```sh
# Example assumes vnu is provisioned on PATH and dist/ contains emitted HTML.
python3 /path/to/KestrelGaming/skills/kestrel-html-conformance/scripts/check_html.py dist/
```

In a standalone checkout with Java 17+, an equivalent official invocation is `java -jar /path/to/vnu.jar --skip-non-html dist/` (make sure the directory has HTML files). Pin the exact release or artifact digest for reproducible CI, and update intentionally; the upstream `latest` release tag moves.

If the project deploys only files that contain dynamic/in-memory HTML, add an extraction or browser-capture step that writes each relevant final HTML document to a temporary output directory **before** the gate. Verify both initial HTTP markup and material DOM states when the task depends on them. Do not claim untested states are covered.

## Skill evaluation scenarios

1. **Clean document:** a minimal complete page passes; report the exact command and version.
2. **Bad nesting:** `<p><div>wrong</div></p>` produces an error; fix and rerun.
3. **Duplicate ID:** two elements with the same `id` fail until identifiers are repaired.
4. **Missing checker:** CLI not installed → BLOCKED, never success.
5. **Empty build:** directory has no HTML → BLOCKED, never success.
6. **Template-only change:** a changed generator is not certified by validating just the template; check built output.
7. **Dynamic HTML:** detect and document uncovered pages/states rather than claiming all routes passed.
8. **Warning policy:** default gate reports warnings without automatic failure; stricter policy uses `--warnings-as-errors`.

These are **test specifications**, not claims that Kestrel or any target application's HTML has already passed the checker.
