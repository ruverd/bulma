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
Its [preflight](../bulma-code-review/references/PREFLIGHT.md) reads all review
context before pass selection and again before publication, pins the reviewed
head, and verifies CI execution. A sensitive-path list is named in the
review body and does not defer. An unresolved thread whose author approved
this head is not an open concern. Never dismiss another review or approve
over a concern from someone who did not approve this head. Every review
POST runs behind the engine's `scripts/gate.py`; an APPROVE it rejects is
never sent. The engine dismisses its own approval when the head moves or a
later pass DEFERs, and posts a COMMENT instead of a second bot approval.
Review preserves the user's checkout. Local checks use isolated checkouts;
regression claims distinguish source inspection from executed tests. Changes
that depend on another deployment include counterpart and rollout checks via
the engine's [evidence rules](../bulma-code-review/references/EVIDENCE.md).
Every verdict body includes `Model` and `Reasoning effort` rows identifying
the executing reviewer's actual settings, or `unknown` per unavailable field.
Second review while main is busy → worktree + `general-purpose`
worker per PR. `--force` if CI red. Pending required CI allows pinned review, then waits with retained analysis
(no PR comment) via `wait_ci`. Draft / conflict / CI-red DEFER is
expected.
Worktree and branch rules: [JOBS.md](../bulma-bus/JOBS.md) §Worktree.
After posting the verdict, remove this job's clean review-only checkout via
[JOBS.md review cleanup](../bulma-bus/JOBS.md#review-cleanup). Pending CI or
failed publication keeps it for resume.

Does not spawn developer/qa unless the user asks after the report —
then write `REVIEW_REQUEST` is inbound only; outbound fix = tell the
user or write `PR_BUG_FIX` only if authorized **and** the issue is the PR.

Not the fd node `bulma-fd-reviewer`.

Verified external concerns feed [FEEDBACK.md](../bulma-bus/FEEDBACK.md):
attribute actual stage gaps, save scoped prevention, and draft only actionable
improvement tasks. A request for changes or LSTM invocation alone proves no
miss. Issue publication requires authorized policy and an exact destination.
