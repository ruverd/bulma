# Implementation

Main thread **never** edits product code. One fresh `bulma-fd-coder` per
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
[bulma-host](../bulma-host/SKILL.md) `spawn_worker`.

## Coder

Follow [nodes/implement.md](nodes/implement.md) and [TDD.md](TDD.md).

Return status is required. `DONE` without TDD evidence is `NEEDS_CONTEXT` to the parent.

If the coder wants a different design: `NEEDS_CONTEXT`. Parent DECIDE from spec + repo. ASK only last-resort policy. Coder does not silently redesign.

## After each ticket

1. Run blast when required, then quality on the ticket's final implementation.
   Focused mode reuses the coder; deep mode uses a quality worker.
2. Fresh `bulma-fd-reviewer` receives diff, done criteria, existing TDD evidence
   and recurring lessons. Either verdict fail returns to the same ticket within
   `review_fix_loops`. Last remaining loop: **fresh** coder.
3. Tester executes the required commands once on the reviewed tree. Identical
   deterministic local checks may reuse evidence via bulma-bus PERFORMANCE.md.
   A failed check returns to implement within `test_fix_loops`.
4. UI + risk=elevated: capture Ticket After before the next ticket. Final evidence
   is recaptured after all code changes, on the validated tree.
5. Start the next ticket only after this ticket passed review and tester. Any
   edit affecting an earlier ticket requires its acceptance to be rechecked.
   After the last ticket, review affected cross-ticket contracts and validate
   the combined tree before final evidence and shipper.
6. Exhausted loops escalate. Never skip ahead or use stale evidence.

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
