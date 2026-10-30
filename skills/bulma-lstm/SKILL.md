---
name: bulma-lstm
category: graph
description: >
  Graph: author-side of review. Ingest a PR, review, inline thread, or
  issue-comment URL, verify with receiving-code-review, patch should-fix on the
  same branch, and reply on every comment. Use when /lstm, /bulma-lstm,
  CHANGES_REQUESTED, or LSTM_REQUEST.
argument-hint: "<PR | review | comment URL> [--force]"
---

# Bulma LSTM (graph)

Looks shit to me. Orchestrator for **incoming** review, not `/bulma-reviewer`.

Never merge. Same PR. Same branch. Draft stays draft. No new PR.

**REQUIRED:** [GRAPH.md](GRAPH.md) · [ARGS.md](ARGS.md) ·
[STATE.schema.md](STATE.schema.md) ·
[bulma-host](../bulma-host/SKILL.md) ·
`receiving-code-review` ·
`unslop` · `bulma-memory` ·
[GITHUB.md](references/GITHUB.md) ·
bus [PROTOCOL.md](../bulma-bus/PROTOCOL.md) ·
[DISK.md](../bulma-bus/DISK.md) ·
fd [DECISION_POLICY.md](../bulma-feature-delivery/DECISION_POLICY.md)

Init `.bulma-lstm/STATE.md`. Walk GRAPH (**admit** first).
Busy main or 2+ PRs → worktree + `general-purpose` worker per PR.
Worktree and branch rules: [JOBS.md](../bulma-bus/JOBS.md) §Worktree.

Orchestrator does **not** write product code. **patch** spawns
`bulma-fd-coder` per evidenced cause group (TDD), preserving per-comment acceptance. **prove** runs the fd reviewer (spec + quality)
and tester before **reply**. A human sign-off request also requires a bus
switch to `bulma-qa` for visual behavioral evidence, even without a code fix
([request_qa.md](nodes/request_qa.md)). QA evidence supports the human decision;
it never grants human approval. Grill only when the fix is complicated.
ASK last resort: [DECISION_POLICY.md](../bulma-feature-delivery/DECISION_POLICY.md).

Chat: `bulma-memory`. Unslop always. Every GitHub reply
(thread, skip reason, COMMENT review, re-review request) is English,
rewritten with bundled `unslop` before POST. Never POST the first draft.

Reply is not optional. Every analyzed comment gets 👍 and a thread
reply. After proven code changes, post a summary, resolve fixed conversations,
dismiss fully addressed CHANGES_REQUESTED reviews with evidence, and re-request
original reviewers unless their latest decisive status or the PR is APPROVED.
Skip-only runs reply and summarize without dismissing or re-requesting.
See [reply.md](nodes/reply.md). Then [learn.md](nodes/learn.md) records verified
causes, scoped prevention for coder/reviewer/QA and eligible improvement task
drafts. LSTM invocation alone does not prove a miss. Issue publication follows
[FEEDBACK.md](../bulma-bus/FEEDBACK.md), defaulting to local drafts.

Do not spawn `bulma_developer` / `bulma_reviewer` / `bulma_qa`.
