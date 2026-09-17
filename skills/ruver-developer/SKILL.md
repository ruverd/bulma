---
name: ruver-developer
category: graph
description: >
  Graph: deliver a ticket or a local goal via grill -> spec -> tickets -> TDD
  (ruver-feature-delivery), then MERGEABLE + bot_review + ruver-qa over the bus. Use when
  /developer, /ruver-developer, a ticket, or a QA_RESULT FAIL+PR_BUG. ASK the
  user only as a last resort.
argument-hint: "<ticket | goal | PR url | resume>"
---

# Ruver developer (graph)

You are the **orchestrator**. Chat: `ruver-memory`. Unslop always. You **do not** implement product code. Fd coder / fix node does.

**REQUIRED** (load now):

- [ARGS.md](ARGS.md) (ticket vs goal vs resume)
- [GRAPH.md](GRAPH.md)
- [STATE.schema.md](STATE.schema.md)
- [ruver-host](../ruver-host/SKILL.md)
- `ruver-bus` [PROTOCOL.md](../ruver-bus/PROTOCOL.md) · [DISK.md](../ruver-bus/DISK.md)
- `ruver-memory`
- delivery voice + policy: `../ruver-feature-delivery/VOICE.md` · `../ruver-feature-delivery/DECISION_POLICY.md` · `../ruver-feature-delivery/PSTACK.md`

Never merge. Stay Draft until **QA PASS**, then `gh pr ready`. Ready is not merge.
Worktree and branch rules: [JOBS.md](../ruver-bus/JOBS.md) §Worktree.

## Start

Parse `$ARGUMENTS` with [ARGS.md](ARGS.md) **before** anything else.

**Resume** (`resume` / same tracker id with existing STATE): replay invariants (ARGS.md), continue at the saved node. Skip finished only when invariants match. The current message is the answer if `waiting_user`. Do not re-init STATE. Do not re-grill settled decisions unless an AC line contradicts them.

**Goal or ticket** (free text, or tracker id/URL, no live STATE for that id):

1. Resolve `$RUVER_ROOT` ([../ruver-bus/DISK.md](../ruver-bus/DISK.md)).
2. Init `.ruver-developer/STATE.md` from [templates/STATE.md](templates/STATE.md).
3. **admit** ([nodes/admit.md](nodes/admit.md) / JOBS.md).
   Second job while another owns main → worktree + `general-purpose` worker. Do not abort QA.
4. Foreground: `QA_RESULT` FAIL + `PR_BUG` → mode **fix**; else **delivery**.
5. Walk GRAPH. Spawn **nodes**, never other graphs as subagents.
6. Outbound QA → enqueue-or-start (JOBS.md), never spawn `ruver_qa`.

`/ruver-developer <goal>`, `/ruver-developer ABC-123`, and `/ruver-developer resume` are first-class.

## Modes

| Input | Path |
|---|---|
| Goal / ticket / feature / bug / chore | `deliver` = run **ruver-feature-delivery** until CI green |
| `QA_RESULT` FAIL + `PR_BUG` | `fix` = existing PR branch only |

Delivery spine (inside fd): grill → spec → tickets → implement(TDD). Bugs go through diagnose first. TDD iron law. Thermo before PR.

## Extra gates (after delivery / after fix)

`CI green AND mergeability = MERGEABLE`. See [references/GATES.md](references/GATES.md).
Then **bot_review** ([nodes/bot_review.md](nodes/bot_review.md)).
Then envelope `QA_REQUEST`. See [references/QA_HANDOFF.md](references/QA_HANDOFF.md).

## Resume

Full rules: [ARGS.md](ARGS.md). STATE + delivery STATE/HANDOFF + bus stack. Do not restart delivery if already green.

```text
/ruver-developer the notification inbox on the dashboard
/ruver-developer ABC-123
/ruver-developer ABC-123: extra note
/ruver-developer resume
/ruver-developer resume: the answer is B
```
