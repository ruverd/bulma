# Linear via the project's MCP

Use this file only when [PRODUCT.md](PRODUCT.md) set `tracker: linear`.
**Only** the `linear-server` (or the equivalent name in this project). **No** `orca linear`.

A bare `ABC-123` with Linear MCP **offline** is a local goal, not this
hard gate. This gate fires when the user pasted a `linear.app` URL.

## Fetch

```
get_issue(id, includeRelations: true)
list_comments(issueId) → paginate to the end
get_issue on related / parent / children / blocks / blockedBy
extract_images if screenshots matter
```

## Child discovery

For a resolved single issue, query `list_issues(parentId: <parent UUID or ID>)`
and follow every returned cursor while `hasNextPage` is true. Request
`parentId`, `statusType`, and `archivedAt` in addition to identity and task
fields. Verify each child's actual parent against the resolved parent's
identifiers. Linked issues and IDs in the description do not count as children.
On a verified parent, load each eligible child's description and comments,
and call `get_issue(id, includeRelations: true)` to read `blocks` and
`blockedBy`. Normalize both directions into `depends_on` using the resolved
issue identifiers. Preserve external edges and the parent's acceptance.

Pass the verified rows to the [stack planner](../bulma-developer/STACKED.md#plan-and-state).
Record its result under `delivery_mode`. Failure reading a page or child
relationship is incomplete discovery, so retry or block the parent before
checkout. An unavailable Linear connector for a bare ID retains the existing
tracker fallback until the ID actually resolves to a Linear issue. Skip child
discovery for an assigned stack member. Its own ticket requirements and
dependencies still use the normal fetch above.

## Branch

[JOBS.md](../bulma-bus/JOBS.md) §Worktree. Always
`feature/<id-lowercase>` (`DEV-4525` → `feature/dev-4525`). Do not
checkout the issue `gitBranchName`.

Checkout before implementing. Shipper checks the branch.

## Persistence

`.bulma-feature-delivery/tracker-context.md` + STATE `tracker_*` fields.
This file is the **Linear adapter**, selected when `tracker: linear`. The
field names are vendor-neutral so another tracker can fill the same slots.

If `tracker: linear` (a Linear URL) and MCP `linear-server` fails / is offline / needs auth:

1. **Do not** invent AC / description / comments.
2. **Do not** implement.
3. Emit the error in English (template in [MCP_CONTEXT.md](MCP_CONTEXT.md)):

```text
## ERROR: MCP unreachable
Could not reach Linear MCP (linear-server) for ticket <ID>.
...
```

4. `result=blocked`, `mcp_gate=failed`.
