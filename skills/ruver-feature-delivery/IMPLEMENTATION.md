# Implementation

Main thread **never** edits product code. One fresh `ruver-fd-coder` per ticket (or re-fix of the same ticket).

## Prompt the coder with

- Goal
- Spec excerpt + recorded decisions (not the grill chat)
- **Full ticket text** (do not say "read STATE and pick")
- Confirmed seams
- Neighbor file paths
- If UI: DS paths + 2–5 recent same-type screens
- Review/test findings when re-fixing

Keep the prompt to about one or two screens. Do not paste GRAPH.md,
`why`, or the parent tool catalog.
[TOKEN_ECONOMY.md](TOKEN_ECONOMY.md). Spawn payload:
[ruver-host](../ruver-host/SKILL.md) `spawn_worker`.

## Coder

Follow [nodes/implement.md](nodes/implement.md) and [TDD.md](TDD.md).

Return status is required. `DONE` without TDD evidence is `NEEDS_CONTEXT` to the parent.

If the coder wants a different design: `NEEDS_CONTEXT`. Parent DECIDE from spec + repo. ASK only last-resort policy. Coder does not silently redesign.

## After each ticket

1. Orchestrator runs the ticket's test command. Exit code into `.ruver-feature-delivery/gates.log`. Red → re-dispatch coder (≤ `test_fix_loops`).
2. Fresh `ruver-fd-reviewer`. Diff + done criteria + `gates.log`. Either
   `spec_verdict` or `quality_verdict` fail → same ticket (≤ `review_fix_loops`).
   Graph pass only if both pass.
3. Loops exhausted → ticket `blocked` + escalate. Never skip ahead.
4. Tester hard gate after the ticket (or after the last ticket, per GRAPH).
5. Next ticket only after this one passed review + tester.

## MCP precondition

Do not dispatch implementers if `mcp_gate: failed`.

## What the orchestrator may do

Read STATE, git status, logs. Update STATE. Dispatch. Answer `NEEDS_CONTEXT` with a repo fact. One English ASK if policy says so.

## What the orchestrator may not do

Edit `src/` or product tests "to get ahead". Collapse N tickets into one coder. Skip review. Run two coders in parallel on the same tree.

## Model hints

| Role | Preference |
|---|---|
| Mechanical coder (1–2 files, clear ticket) | mid/fast |
| Multi-file integration | frontier |
| Triage / tester | mid |
| Slice reviewer | mid |
| Final review / quality | frontier |

## STATE

```markdown
- ISO | node=implement | ticket=N | subagent=fresh | result=DONE|BLOCKED
- ISO | node=review | ticket=N | spec_verdict=pass|fail | quality_verdict=pass|fail
```
