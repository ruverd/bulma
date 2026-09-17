---
name: ruver-lstm
category: graph
description: >
  Graph: author-side of review. Ingest a PR, review, inline thread, or
  issue-comment URL, verify with receiving-code-review, patch should-fix on the
  same branch, and reply on every comment. Use when /lstm, /ruver-lstm,
  CHANGES_REQUESTED, or LSTM_REQUEST.
argument-hint: "<PR | review | comment URL> [--force]"
---

# Ruver LSTM (graph)

Looks shit to me. Orchestrator for **incoming** review, not `/ruver-reviewer`.

Never merge. Same PR. Same branch. Draft stays draft. No new PR.

**REQUIRED:** [GRAPH.md](GRAPH.md) · [ARGS.md](ARGS.md) ·
[STATE.schema.md](STATE.schema.md) ·
[ruver-host](../ruver-host/SKILL.md) ·
`receiving-code-review` ·
`unslop` · `ruver-memory` ·
[GITHUB.md](references/GITHUB.md) ·
bus [PROTOCOL.md](../ruver-bus/PROTOCOL.md) ·
[DISK.md](../ruver-bus/DISK.md) ·
fd [DECISION_POLICY.md](../ruver-feature-delivery/DECISION_POLICY.md)

Init `.ruver-lstm/STATE.md`. Walk GRAPH (**admit** first).
Busy main or 2+ PRs → worktree + `general-purpose` worker per PR.
Worktree and branch rules: [JOBS.md](../ruver-bus/JOBS.md) §Worktree.

Orchestrator does **not** write product code. **patch** spawns
`ruver-fd-coder` (TDD). **prove** runs the fd reviewer (spec + quality)
and tester before **reply**. Grill only when the fix is complicated.
ASK last resort: [DECISION_POLICY.md](../ruver-feature-delivery/DECISION_POLICY.md).

Chat: `ruver-memory`. Unslop always. Every GitHub reply
(thread, skip reason, COMMENT review, dismiss message) is English,
rewritten with bundled `unslop` before POST. Never POST the first draft.

Reply is not optional. Every analyzed comment gets 👍 and a thread
reply. Do not dismiss `CHANGES_REQUESTED` until **prove** passed (or
the run was skip-only). Then re-request if a fix landed.
See [reply.md](nodes/reply.md).

Do not spawn `ruver_developer` / `ruver_reviewer` / `ruver_qa`.
