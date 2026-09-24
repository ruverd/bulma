---
name: bulma-reviewer
category: graph
description: >
  Graph: review a PR/branch via /bulma-code-review, classify CI/test
  failures, optionally bus a REVIEW_RESULT. Use when /reviewer,
  /bulma-reviewer, or a REVIEW_REQUEST envelope
  arrives.
argument-hint: "<PR url | owner/repo#N | branch>"
---

# Bulma Reviewer (graph)

Orchestrator. Never merge. Chat: `bulma-memory`. Unslop always.

**REQUIRED:** [GRAPH.md](GRAPH.md) · [STATE.schema.md](STATE.schema.md) ·
bus PROTOCOL.md · skill `bulma-code-review` · `bulma-memory` ·
[DISK.md](../bulma-bus/DISK.md) (`.bulma-*` is **global**, never git root)

Init `.bulma-reviewer/STATE.md`. Walk GRAPH (**admit** first).
`code_review` is the engine: spec-first, patch bind, high-risk critic.
Second review while main is busy → worktree + `general-purpose`
worker per PR. `--force` if CI red. Pending required CI waits 5m
(no PR comment) via `wait_ci`. Draft / conflict / CI-red DEFER is
expected.
Worktree and branch rules: [JOBS.md](../bulma-bus/JOBS.md) §Worktree.

Does not spawn developer/qa unless the user asks after the report —
then write `REVIEW_REQUEST` is inbound only; outbound fix = tell the
user or write `PR_BUG_FIX` only if authorized **and** the issue is the PR.

Not the fd node `bulma-fd-reviewer`.
