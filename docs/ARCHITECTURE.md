# Ruver architecture

Command pages: [commands/](commands/README.md).

Five graphs share one session. They do not nest. They pass work through
files on the bus.

```
developer ⇄ qa ⇄ triage
     ⇄ reviewer
     ⇄ lstm
```

The **main thread** is the only graph runner. Outbound work writes an
envelope under `$RUVER_ROOT/.ruver-bus/`, pushes the stack, and loads
the target graph. Graphs never `spawn_worker` another graph
(`load_graph` on this thread). See [GRAPH_ENGINEER.md](GRAPH_ENGINEER.md)
and [ruver-host](../skills/ruver-host/SKILL.md).

Worker subagents (`ruver-fd-coder`, `ruver-fd-tester`, …) implement
product code. They are not graphs.

## Disk

```bash
slug=$(git rev-parse --show-toplevel | sed 's|^/||; s|/|-|g')
RUVER_ROOT="${RUVER_HOME:-$HOME/.ruver}/$slug"
```

Every `.ruver-*` directory lives under `$RUVER_ROOT`. See
`../skills/ruver-bus/DISK.md`.

## /ruver-developer

```
goal | ticket | resume | QA_RESULT FAIL+PR_BUG
        │
     admit
        │
   ┌────┴─────┐
   ▼          ▼
deliver      fix
 (fd)    (same PR)
   │          │
   └────┬─────┘
        ▼
    mergeable          CI green AND mergeable
        │
    bot_review         skip if no bot; else wait / lstm
        │
   request_qa  ──bus──►  /ruver-qa
        │
   apply_qa
        │
   PASS → ready
   FAIL+PR_BUG → fix
```

Delivery spine inside `ruver-feature-delivery`:

```
grill-with-docs → spec → tickets → implement (TDD) → review → CI
```

Bugs go through diagnose first. The orchestrator does not write product
code. `ruver-fd-coder` does, one ticket at a time.

## /ruver-qa

```
PR from args or QA_REQUEST
  → admit          one slot; else enqueue
  → plan           happy + user-break from the diff, before any click
  → execute        agent-browser or HTTP; record evidence
  → triage?        product suspicion → bus → /ruver-triage
  → verdict        comment + evidence + QA_RESULT
```

Backend-only PRs with no UI sibling: HTTP the changed endpoints.
Unit tests or `git show` are not a complete execute.

## /ruver-lstm

Looks shit to me. Author side of review. Same PR, same branch.

```
URL | resume | LSTM_REQUEST
  → admit
  → resolve comments
  → rebase if DIRTY / CONFLICTING
  → verify (claim_true + fix_ok_here)
  → patch should-fix (ruver-fd-coder, TDD)
  → prove (spec + quality + tester)
  → 👍 + unslopped reply on every comment
  → resolve + dismiss CHANGES_REQUESTED + re-request
```

Never opens a new PR. Draft stays draft.

## Reviewer vs LSTM vs code-review

| Name | Who | Job |
|---|---|---|
| `/ruver-reviewer` | reviewer | Run `/ruver-code-review`, report. |
| `/ruver-code-review` | engine | Deep/light review, one artifact per PR. |
| `/ruver-lstm` | author | Consume that review and patch. |

## Goal loop

`/ruver-goal` uses `schedule_wake` (`ruver-host`) until the draft PR is
CI-green, MERGEABLE, and has a QA comment with evidence on the head
SHA. CI is often longer than a tool timeout, so the loop polls
instead of `gh pr checks --watch`.

## Invariants

- Never merge. Mark the PR ready only after QA PASS.
- Chat follows `ruver-memory` (default English). Forge text stays English. Unslop always.
- ASK the user only as a last resort.
