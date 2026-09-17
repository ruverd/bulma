---
name: ruver-feature-delivery
category: engine
description: >
  Use when delivering a ticket, bug, or chore end-to-end (implementation
  through draft PR with CI green) via /ruver-feature-delivery or /ruver-fd, or
  when resuming a run whose HANDOFF.md exists. Spine: grill -> spec -> tickets
  -> implement(tdd) -> review.
---

# Ruver feature delivery

Orchestrator. Chat: `ruver-memory`. Unslop. **No product code on the main thread.**

Load now:

- [GRAPH.md](GRAPH.md)
- [STATE.schema.md](STATE.schema.md)
- [ROUTING.md](ROUTING.md)
- [PRODUCT.md](PRODUCT.md)
- [VOICE.md](VOICE.md)
- [PSTACK.md](PSTACK.md)
- [DECISION_POLICY.md](DECISION_POLICY.md)
- `ruver-bus` [DISK.md](../ruver-bus/DISK.md)
- `ruver-memory`

Spine (bundled primitives):

```
grill-with-docs → to-spec → to-tickets → implement(/tdd) → code-review
```

Adapted grill: [GRILL.md](GRILL.md). ASK the user only as a last resort.

## Quick start

```text
/ruver-fd ABC-123
/ruver-fd ABC-123: extra note
/ruver-fd login button does nothing
/ruver-fd resume
/ruver-fd … --no-pr
```

Checkout is `feature/<id-lowercase>`.
Worktree and branch rules: [JOBS.md](../ruver-bus/JOBS.md) §Worktree.

## Orchestrator loop

**Resume:** read STATE + HANDOFF, **RECONCILE** (replay HANDOFF invariants; git/gh vs STATE). Continue at the current node. Skip a settled node only when its invariants match. If `waiting_user`, the user message is the ASK answer. Do not re-init. Do not re-grill settled decisions unless an AC line contradicts them. Missing `risk` on a v4 STATE → `normal`.

**Fresh:**

1. Init STATE under `$RUVER_ROOT/.ruver-feature-delivery/`. Load `ruver-memory`.
2. `mcp_context` then `triage`. Critical MCP down → STOP. Do not invent.
3. Walk GRAPH. Grill / spec / tickets on the main thread. `plan_critic` on the main thread unless `risk=elevated` (then one read-only spawn). Spawn **one** node subagent at a time for implement / review / diagnose / tester / evidence / quality / shipper.
4. Never merge. Draft PR only from `shipper`.
5. Near context limit → `handoff`.

## Paths

| path / scope | When | How |
|---|---|---|
| **full_feature** | new behavior | grill → spec → tickets → plan_critic (skip if `risk=low`) → TDD implement |
| **debug_fix** | bug | diagnose → one TDD ticket |
| **light_change** | chore | one ticket → one coder |
| **`scope: fullstack`** | FE and BE, sibling resolved | same branch, git worktrees ([FULLSTACK.md](FULLSTACK.md); Orca optional) |

Ship: review → tester → evidence → blast (not light unless `risk=elevated`) → **thermo fix all** → commit → push → draft PR
(reviewers and assignee: [PRODUCT.md](PRODUCT.md))
→ **CI 100% green** (only then **delivered**).

## Intelligence

1. Route with evidence. Not full_feature on every bug.
2. DECIDE micro-choices. ASK only last-resort policy.
3. Bug: root cause **before** the fix. If it is a feature, re-route to grill.
4. Implementation **only** in a subagent. Main does not edit product code.
5. TDD on every behavior change. Thermo fix all before PR.
6. UI: DS of the repo; Figma if present; else copy recent same-type screens.
7. Discover the repo first (PRODUCT.md). Critical tracker URL offline → error and stop. Local goal does not need a tracker.
8. Blocker: advance what you can → Draft a tracker issue + contract comment → `waiting_blocker`.
9. Tokens: [TOKEN_ECONOMY.md](TOKEN_ECONOMY.md).
10. Limit near: [HANDOFF.md](HANDOFF.md).

## Files

Load on demand. This list is the index.

```
ruver-feature-delivery/
├── SKILL.md GRAPH.md ROUTING.md PSTACK.md GRILL.md VOICE.md
├── DECISION_POLICY.md TDD.md IMPLEMENTATION.md
├── MCP_CONTEXT.md LINEAR.md BLOCKERS.md FULLSTACK.md PRODUCT.md
├── UI_DESIGN_SYSTEM.md CI_DELIVERY.md HANDOFF.md TOKEN_ECONOMY.md
├── STATE.schema.md
├── nodes/   templates/   adapters/
```
