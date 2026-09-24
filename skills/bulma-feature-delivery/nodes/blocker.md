# Node: blocker_handler

**Verb:** unblock-prep + wait
**Capability:** tracker MCP write (issue draft, comments, relations); read get_issue; **no** inventing API
**When:** dependency gap (contract, open ticket, missing BE)

## Mission

1. **Advance** everything that does not depend on the blocker.
2. Guarantee a blocking ticket (**draft** if it does not exist) with an **explicit dependency**.
3. **Comments** with the contract (endpoint, params, body, response, TS types).
4. **Loop** until the blocker is Done.
5. Resume the graph.

Follow [BLOCKERS.md](../BLOCKERS.md).

## Steps

1. Identify what blocks (endpoint? ticket? decision?).
2. List tickets still implementable → return `advanced_slices` to
   the orchestrator (**it** dispatches the coders; this node does not spawn subagents).
3. `save_issue` draft (if needed) + `blockedBy` on the current ticket.
4. `save_comment` with a detailed contract on the BE/blocking ticket.
5. STATE `waiting_blocker` + `blockers[].last_check`.
6. Check `get_issue` **once**; if still open → `result: still_waiting` and **end the
   session** (user re-runs `/bulma-fd resume` when Done; never sleep/poll in-session).
7. On resume with Done: re-fetch comments/contract; return `result: unblocked`.

## Output

```text
result: unblocked | still_waiting | blocked_mcp | canceled
blocker_ids: [DEV-…]
draft_created: bool
advanced_slices: [...]
```

## Hard rules

- Tracker MCP only, never a vendor CLI.
- Draft is **never** empty: description with dependency + contract.
- Do not implement the blocked part "by feel".
- Chat (`bulma-memory`): tell the user what is waiting and the draft link. tracker comment stays English.
