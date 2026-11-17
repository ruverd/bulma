---
title: Gate approvals on blocking review evidence
author: Ruver
date: 2026-11-17
id: l-75010c6c
branch: codex/reviewer-thread-blockers
touches:
  - skills/bulma-code-review/scripts/gate.py
  - skills/bulma-code-review/references/PREFLIGHT.md
  - tests/bulma-code-review.sh
---

## Decided
An open thread alone does not defer a clean review. Preflight and the final approval gate share the rule: active GitHub change requests, applicable Medium-or-higher thread findings, and concerns backed by concrete evidence block approval. An approval on the current SHA covers that reviewer's own threads.

## Tried and ruled out
Treating every unresolved thread as blocking caused a clean Canva embed review with green CI and only an optional Low test suggestion to defer. A later COMMENTED review or a thread clearance cannot override a formal change request.

## Watch out
Use `gate.py --context-only` before pass selection and again before publishing. A semantic assessment binds to the cached conversation and head; recheck it after replies, edits, or a new SHA. Thread resolution stays with its author or the existing owner workflow. The COMMENT verdict remains rejected.
