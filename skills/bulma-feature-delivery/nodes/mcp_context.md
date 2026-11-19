# Node: mcp_context

**Verb:** gather + **verify**
**Capability:** repo discovery + MCP/CLI read + git branch
**When:** **always** at the start; **before** any implement

## Mission

1. Discover this repo ([PRODUCT.md](../PRODUCT.md)). Load `bulma-memory`.
2. Verify access for **detected** sources only.
3. If a **critical** source fails → error in the chat language and `blocked`. No inventing.

[PRODUCT.md](../PRODUCT.md) · [MCP_CONTEXT.md](../MCP_CONTEXT.md) ·
[LINEAR.md](../LINEAR.md) when `tracker: linear`

## Steps

1. Discover forge, tracker, toolchain, topology, QA tool, assignee,
   reviewers (PRODUCT.md §6). Write STATE (`reviewers`,
   `reviewers_status`, `assignee`, `chat_language` from `bulma-memory`).
2. Scan the goal for IDs/URLs.
3. For each **detected** source:
   - Pre-check: MCP or CLI (`gh` / `glab`) available?
   - Critical and unreachable → ERROR block (MCP_CONTEXT.md), `mcp_gate: failed`, **blocked**.
   - Ok → fetch → `*-context.md`.
4. When PRs are enabled and the selected tracker adapter supports
   [child discovery](../LINEAR.md#child-discovery), run it
   before choosing its work branch. Pass the planner's `mode` to STATE and
   hand the plan to **triage** when it is a stack. Resolve explicit stack
   requests with the same planner. Skip branch creation for a stack parent
   and for read-only or planning-only goals.
   Ordinary tracker delivery uses `feature/<id-lowercase>` per
   [JOBS.md](../../bulma-bus/JOBS.md). A stack member uses its assigned
   worktree, branch and start SHA. Never reset it to the default branch.
5. Re-scan the ticket body for more URLs.
6. `mcp-sources.md` + STATE.

## Output

```text
result: ok | partial | blocked | skipped
mcp_gate: passed | passed_partial | failed
forge / tracker / pkg / typecheck_cmd / test_cmd / qa_tool / scope
error: ...   # required if blocked; speak in the chat language
```

## Runtime note

If the runtime does not expose MCP to subagents, this node runs **on
the main thread**. Discovery is not product code.

## Hard rules

- **Never** invent content from an offline tracker.
- **Never** implement if `mcp_gate: failed` for a **critical** source.
- Local goal + no tracker URL → `mcp_gate: passed` (or `passed_partial`). Continue.
- Zero product code in this node.
