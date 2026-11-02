---
schema: 1
id: 2026-11-02-central-memory
kind: decision
scope: shared
status: active
evidence: user-stated
author: Codex
created: 2026-11-02
updated: 2026-11-02
sources: "Kisuul's 2026-11-02 request to implement the Kestrel agent contract in Kisuul/KestrelGaming as common memory."
---

# Central memory home

## Summary

KestrelGaming is the common home for Kestrel agents' long-term memory and reusable
skills. Use Markdown text files. Keep agent memory systems out of application repositories.

## Evidence

The user explicitly requested common memory so agents do not clutter a project
repository with their own long-term skill and memory systems, and requested that the
Kestrel contract be implemented in this repository.

The owner/repository namespace, scoped indexes, record metadata, and separate handoffs
are implementation choices for that objective, not additional quoted user requirements.
This record does not grant ongoing write authority to unrelated projects or later tasks.

## Revisit when

The user changes the designated memory home, access model, storage format, or desired
separation between shared memory and project-owned documentation.
