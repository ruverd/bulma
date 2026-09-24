# Implementation

Main thread **never** edits product code. One fresh `ruver-fd-coder` per
ticket. Re-fix of the same ticket reuses that coder except on the last
`review_fix_loops` slot (fresh).

## Prompt the coder with

- Goal
- Spec excerpt + recorded decisions (not the grill chat)
- **Full ticket text** (do not say "read STATE and pick")
- Confirmed seams
- Neighbor file paths
- If UI: DS paths + 2–5 recent same-type screens
- Review/test findings when re-fixing
- **Recurring lessons**: the output of
  `python3 ../bulma/scripts/lessons.py --repo <STATE repo> --files <ticket files, comma list>`
  (path from this skill's directory), pasted as-is. It prints at most five of
  this repo's recurring review misses, each with its rule from
  [LESSONS.md](LESSONS.md). Empty output means paste nothing. A failed run is
  a chat note, never a reason to hold the spawn. Run it once per ticket, not
  on every re-fix.

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
2. Fresh `ruver-fd-reviewer`. Diff + done criteria + `gates.log` + the same
   recurring-lessons block the coder got. Either
   `spec_verdict` or `quality_verdict` fail → same ticket (≤ `review_fix_loops`).
   Graph pass only if both pass. Last remaining loop: **fresh** coder.
   Earlier loops re-dispatch the same coder.
3. Loops exhausted → ticket `blocked` + escalate. Never skip ahead.
4. Tester hard gate after the ticket (or after the last ticket, per GRAPH).
5. UI ticket (`qa_tool=agent-browser`) and `risk=elevated`: capture After
   of this ticket's route ([evidence.md](nodes/evidence.md) §Ticket After)
   before the next ticket. Missing After fails the ticket. Not a second QA
   execute. Skip on `low` / `normal` and on non-UI.
6. Next ticket only after this one passed review + tester (and ticket After
   when step 5 applies).

## MCP precondition

Do not dispatch implementers if `mcp_gate: failed`.
Do not dispatch implementers if GRAPH still owes `plan_critic` (full_feature
and `risk` is not `low`, and `plan_critic_verdict` is not `pass` / `skip`).

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
