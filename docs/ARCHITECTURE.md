# Bulma architecture

Command pages: [commands/](commands/README.md).

Five graphs share one session. They do not nest. They pass work through
files on the bus.

```
developer ⇄ qa ⇄ triage
     ⇄ reviewer
     ⇄ lstm
```

The **main thread** is the only graph runner. Outbound work writes an
envelope under `$BULMA_ROOT/.bulma-bus/`, pushes the stack, and loads
the target graph. Graphs never `spawn_worker` another graph
(`load_graph` on this thread). See [GRAPH_ENGINEER.md](GRAPH_ENGINEER.md)
and [bulma-host](../skills/bulma-host/SKILL.md).

Worker subagents (`bulma-fd-coder`, `bulma-fd-tester`, …) implement
product code. They are not graphs.

## Disk

```bash
slug=$(git rev-parse --show-toplevel | sed 's|^/||; s|/|-|g')
BULMA_ROOT="${BULMA_HOME:-$HOME/.bulma}/$slug"
```

Every `.bulma-*` directory lives under `$BULMA_ROOT`. See
`../skills/bulma-bus/DISK.md`.

## /bulma-developer

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
   request_qa  ──bus──►  /bulma-qa
        │
   apply_qa
        │
   PASS → ready
   FAIL+PR_BUG → fix
```

Delivery spine inside `bulma-feature-delivery`:

```
grill-with-docs → spec → tickets → implement (TDD) → review → CI
```

Bugs go through diagnose first. The orchestrator does not write product
code. `bulma-fd-coder` does, one ticket at a time.

## /bulma-qa

```
PR from args or QA_REQUEST
  → admit          one slot; else enqueue
  → plan           happy + user-break from the diff, before any click
  → execute        agent-browser or HTTP; record evidence
  → triage?        product suspicion → bus → /bulma-triage
  → verdict        comment + evidence + QA_RESULT
```

A backend PR still runs. Prove the changed endpoints with an HTTP
still, or by walking the FE screens that call them. Unit tests or
`git show` are not a complete execute.

## /bulma-lstm

Looks shit to me. Author side of review. Same PR, same branch.

```
URL | resume | LSTM_REQUEST
  → admit
  → resolve comments
  → rebase if DIRTY / CONFLICTING
  → verify (claim_true + fix_ok_here)
  → patch should-fix (bulma-fd-coder, TDD)
  → prove (spec + quality + tester)
  → 👍 + unslopped reply on every comment
  → resolve + dismiss CHANGES_REQUESTED + re-request
```

Never opens a new PR. Draft stays draft.

## Reviewer vs LSTM vs code-review

| Name | Who | Job |
|---|---|---|
| `/bulma-reviewer` | reviewer | Run `/bulma-code-review`, report. |
| `/bulma-code-review` | engine | Deep/light review, one artifact per PR. |
| `/bulma-lstm` | author | Consume that review and patch. |

## Goal loop

`/bulma-goal` uses `schedule_wake` (`bulma-host`) until the draft PR is
CI-green, MERGEABLE, and has a QA comment with evidence on the head
SHA. CI is often longer than a tool timeout, so the loop polls
instead of `gh pr checks --watch`.

## Bulma overlay

`/bulma` is not a sixth bus graph. It runs before a graph (pick the target
from args and `world.sh`) and around it (Jev at the forks in
`skills/bulma/HOOKS.md`). The target still owns its edges, envelopes and
loop caps; bulma never appears on `STACK.md`. Every Jev answer is logged to
`$BULMA_ROOT/.bulma-core/DECISIONS.tsv` with the graph's own answer, and
`bulma.py report` turns that into thresholds. Without `TYPESAFE_API_KEY`
`/bulma` stops; the graphs run as before.

## Invariants

- Never merge. Mark the PR ready only after QA PASS.
- Chat follows `bulma-memory` (default English). Forge text stays English. Unslop always.
- ASK the user only as a last resort.
