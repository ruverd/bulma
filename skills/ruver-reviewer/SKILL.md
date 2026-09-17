---
name: ruver-reviewer
category: graph
description: >
  Graph: review a PR/branch via /ruver-code-review, classify CI/test
  failures, optionally bus a REVIEW_RESULT. Use when /reviewer,
  /ruver-reviewer, or a REVIEW_REQUEST envelope
  arrives.
argument-hint: "<PR url | owner/repo#N | branch>"
---

# Ruver Reviewer (graph)

Orchestrator. Never merge. Chat: `ruver-memory`. Unslop always.

**REQUIRED:** [GRAPH.md](GRAPH.md) · [STATE.schema.md](STATE.schema.md) ·
bus PROTOCOL.md · skill `ruver-code-review` · `ruver-memory` ·
[DISK.md](../ruver-bus/DISK.md) (`.ruver-*` is **global**, never git root)

Init `.ruver-reviewer/STATE.md`. Walk GRAPH (**admit** first).
`code_review` is the engine: spec-first, patch bind, high-risk critic.
Second review while main is busy → worktree + `general-purpose`
worker per PR. `--force` if CI red. Pending required CI waits 5m
(no PR comment) via `wait_ci`. Draft / conflict / CI-red DEFER is
expected.
Worktree and branch rules: [JOBS.md](../ruver-bus/JOBS.md) §Worktree.

Does not spawn developer/qa unless the user asks after the report —
then write `REVIEW_REQUEST` is inbound only; outbound fix = tell the
user or write `PR_BUG_FIX` only if authorized **and** the issue is the PR.

Not the fd node `ruver-fd-reviewer`.
