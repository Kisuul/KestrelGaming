# Project profile — Kisuul/KestrelGaming

This repository is the shared contract, memory, and skill home for Kestrel agents.
Its original description is “Synthetic organization meant to exist within the
UCSH framework. Agency is sacrosanct!” No additional definition of UCSH is assumed.

The indexed [project record](../memory/projects/kisuul/kestrelgaming/PROFILE.md)
holds source and provenance. Profiles are observations and conventions, not access grants.

## Source and commands

| Item | Location or command | Effects |
| --- | --- | --- |
| Contract | `KESTREL.md` | Markdown; retained from supplied seed |
| Protocols and templates | `kestrel/` | Guidance and reusable record forms |
| Durable records | `memory/` | Markdown with flat frontmatter |
| Reusable procedures | `skills/` | `SKILL.md` plus optional host metadata |
| Validator | `python3 tools/validate_seed.py` | Read-only; no network or third-party dependencies |
| Regression tests | `python3 -m unittest discover -s tests -v` | Temporary fixtures; Python may write ignored bytecode |
| Whitespace check | `git diff --check` | Read-only |
| CI | `.github/workflows/validate.yml` | Runs the validator and tests; no write token permissions |
| Build / deployment | None | No application runtime to build or deploy |

Python 3.9+ is the supported validation runtime. Use UTF-8, relative Markdown links,
lowercase directory slugs, and short source-backed records. Templates are examples,
not completed work. There are no generated memory indexes to rebuild.

## Change boundaries

Normal authorized maintenance includes records, indexes, templates, and relevant
validation. Contract, scope, verification, and CI changes deserve a deliberate diff
review because they change how later agents operate. Follow the current user's
authorization and actual repository controls for committing, pushing, and merging;
this profile grants no blanket authority over this or any other repository.

Do not store credentials, private transcripts, raw tool output, or unrelated personal
details. Visibility was private at initialization; verify it again before adding
content whose suitability depends on audience. No license is selected by this change.
