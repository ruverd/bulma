---
description: Ruver graph — grill → spec → tickets → TDD. MCP first, error if unavailable, no invent, then implement/ship
argument-hint: "<goal|ticket|resume> [--no-pr]"
---

# /ruver-feature-delivery

Alias: `/ruver-fd` · **Args:** `$ARGUMENTS` · User-facing chat in short English. Unslop always

## Load (progressive — do not load everything up front)

1. Always: `SKILL.md` + `PSTACK.md` + `VOICE.md` + `DECISION_POLICY.md` + `TOKEN_ECONOMY.md` + `MCP_CONTEXT.md` + `ROUTING.md` + `PRODUCT.md`
2. On demand: `GRILL.md` · `TDD.md` · `IMPLEMENTATION.md` · `CI_DELIVERY.md` ·
   `HANDOFF.md` · `BLOCKERS.md` · `UI_DESIGN_SYSTEM.md`
3. Fullstack: `FULLSTACK.md` (Orca only if `orca status` works)

## Orchestrator

### 0) Init / resume · `open_pr: true` unless `--no-pr`

If args contain **`resume`**:

1. Read `.ruver-feature-delivery/HANDOFF.md` + `STATE.md`.
2. **RECONCILE (required before any edge):** `git status` +
   `git log origin/<branch>..HEAD` + `gh pr list --head <branch>` + `gh pr checks`
   and compare with STATE. Rules: unverified "done" becomes "unknown" and is re-checked;
   PR already exists → skip create and go to ci_watch; ticket code present with
   STATE=pending → dispatch reviewer (not coder).
3. **Do not** re-fetch MCP if `mcp_gate: passed` and files exist.
4. Run only HANDOFF **Next steps** until CI green.
5. TOKEN_ECONOMY.md.

If **limit near** mid-run:

1. Write HANDOFF (template).
2. Do not `git add` `$RUVER_ROOT` files.
3. User: open **Grok** (or Claude) on the same branch → `/ruver-fd resume`.
4. Stop this runtime cleanly (`handed_off`).

### 1) MCP verify + load (`ruver-fd-context`) — **before implementing**

For each **detected** source (tracker URL, Figma, Sentry, Notion, …):

1. **Verify** the project MCP is reachable.
2. If **critical** and **unreachable** → **STOP** (do not invent, do not coder): print the
   exact **«ERROR: MCP unreachable»** template from `MCP_CONTEXT.md` — single source,
   do not write your own variant. Speak it in English.
3. STATE: `mcp_gate: failed` + `mcp_gate_error`.
4. If ok: full fetch → `*-context.md`; tracker → `feature/<id-lowercase>` (JOBS.md).
5. `mcp_gate: passed` only with critical sources ok.

**If `mcp_gate: failed` → end the run.** No implement triage, no ship.

### 2) Triage → path + scope (only if mcp_gate ∈ {passed, passed_partial})

### 3) Path (GRAPH.md)

- `full_feature` → grill (main thread) → spec → tickets → implement TDD
- `debug_fix` → diagnose → one TDD ticket
- `light_change` → one ticket
- `fullstack` → sibling from PRODUCT.md, same branch, git worktrees (Orca optional)

Grill DECIDE internally. ASK last resort. Do not interview the tree.
**UI:** repo DS; Figma if present; else recent same-type refs.

### 3b) Blocker (missing contract / ticket / BE) — `BLOCKERS.md`

If a dependency is missing:

1. **Advance** tickets that do not depend on the blocker.
2. Tracker MCP: create a **Draft** issue (if none exists) with an
   **explicit dependency** description to the current ticket.
3. `blockedBy` / `blocks` relation.
4. `save_comment` on the blocking ticket with the consumed **contract**:
   method/path, auth, params, request/response, TypeScript, UI use.
5. STATE `waiting_blocker` → one `get_issue` check; if still open, end the session.
6. Re-fetch the contract → resume implement.

Do not invent a "ready" endpoint. Tell the user in English (draft link).

### 4) Reviewer → tester → blast → thermo → ship → **CI green**

1. Final reviewer (whole diff) + tester hard gate — if not already covered in
   the ticket loop (IMPLEMENTATION.md). Shipper **refuses** without those gates in STATE.
2. Quality thermo fix all.
3. Shipper: commit + push + draft PR
   (no Co-Authored-By / trailers). Reviewers and assignee per PRODUCT.md.
4. **`ruver-fd-ci` / CI_DELIVERY.md:**
   - `gh pr checks` (source of truth)
   - pending → poll
   - fail → fix + push + re-check (until green or escalate)
5. Fullstack: **both** PRs green.
6. **`status: done` / "delivered" only with CI green.**
7. Never merge. Short English summary (S/D/P) with PR + green checks.

### Token economy

- MCP/plan contexts in **files**; subagent gets only the ticket + paths
- Do not re-paste the whole tracker-context; do not re-fetch MCP if gate passed
- Chat without narrating every tool (`TOKEN_ECONOMY.md`)
