---
name: bulma-triage
category: graph
description: >
  Graph: investigate a QA failure, classify PR_BUG / EXISTING_BUG /
  NEW_BUG / NOT_A_BUG / BLOCKED, route via the bus. Use when
  /bulma-triage, or a TRIAGE_REQUEST envelope arrives.
argument-hint: "<QA handoff or PR url>"
---

# Bug Triage (graph)

Orchestrator. Investigate first. Decide second. Act third.
Not a ticket bot. Use the session model; high effort if the host
exposes it ([bulma-host](../bulma-host/SKILL.md)).

**REQUIRED:** [GRAPH.md](GRAPH.md) · [STATE.schema.md](STATE.schema.md) ·
bus PROTOCOL.md · `bulma-memory` ·
[DISK.md](../bulma-bus/DISK.md) (`.bulma-*` is **global**, never git root)

Chat: `bulma-memory`. Unslop always. PR link required. Init `.bulma-triage/STATE.md`. Walk GRAPH.
Classify **each** finding. `NEW_BUG` → tracker issue (LINEAR.md).
`PR_BUG` → `TRIAGE_RESULT` + pop to QA. Do **not** switch to
developer. Do **not** spawn `bulma_developer`.

Not `bulma-fd-triage` (that router picks fd paths).
