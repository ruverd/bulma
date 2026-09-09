# External context via the current project's MCP

**Rule:** information from external tools (Linear, Figma, Sentry, Notion, …)
enters **only through MCP of the current workspace/project**.

**Hard gate before implementing:**

1. **Verify** the MCP for the needed source is reachable.
2. If you **need** the source and **cannot** reach it → **ERROR and STOP**.
3. **Forbidden** to invent AC, design, stack, comments, or "remember" the ticket.
4. **Forbidden** to continue to triage/implement/ship with a **critical** source in fail.

**Also forbidden:** Orca Linear CLI, generic scrape as a substitute for MCP.

## When to run

Always at the start of `/ruver-fd`, **before** triage:

1. Discover the repo ([PRODUCT.md](PRODUCT.md)): forge, tracker, toolchain, topology
2. Scan the **user goal** for URLs/IDs
3. Load the **detected** tracker (Linear, GitHub Issues, Jira, …) if any
4. Any other URL → matching MCP

Persist under:

```
.ruver-feature-delivery/
  tracker-context.md      # if Linear
  figma-context.md       # if Figma
  sentry-context.md      # if Sentry
  notion-context.md      # if Notion
  mcp-sources.md         # index: what you tried, ok/fail, path
```

STATE: list `mcp_sources: [{name, status, path, refs}]`.

## Discovering MCP

1. Use MCP tools **already connected** in the project (`search_tool` / session catalog).
2. Typical server names (vary by setup):

| Source | Server (examples) | Detect |
|---|---|---|
| **Linear** | `linear-server` | `[A-Z][A-Z0-9]+-\d+`, `linear.app/.../issue/` |
| **Figma** | `figma`, `figma-dev-mode-mcp-server`, Figma MCP | `figma.com/file|design/...`, `figma.com/proto/` |
| **Sentry** | `sentry` | `sentry.io/...`, `SENTRY-...`, issue id in text |
| **Notion** | `notion`, `notionApi` | `notion.so/...`, `notion.site/...` |
| **GitHub** | if a gh MCP exists | `github.com/.../issues|pull/` |
| **Other** | whatever the project has | URL with a recognizable domain |

### MCP pre-check (required per source)

Before calling tools on a source:

1. Confirm the server is in the session catalog (`search_tool` / tools list).
2. If the server is **absent**, **timeout**, **auth required**, **handshake failed**:
   - `status: error`
   - **do not** invent
   - if the source is **critical** → `result=blocked` + error message (below)
3. If the server is ok but the tool call fails → same treatment.

### Critical vs optional sources

| Detected in goal/ticket | Critical? | If it fails |
|---|---|---|
| Tracker **URL** (Linear/Jira/GitHub issue) | **Yes** | STOP + error |
| Bare `ABC-123`, no URL | No | Try the connected tracker. Else local goal |
| Local goal, no ticket | No | Continue. No tracker MCP needed |
| Figma URL and the task is UI | **Yes** (only if a URL exists) | STOP + error |
| UI task **with no** Figma URL | Figma not required | Follow DS + recent code refs |
| Sentry URL and the task is bug/debug | **Yes** | STOP + error |
| Notion URL and it is the main spec/AC | **Yes** | STOP + error |
| Nice-to-have link / side attachment | No | `unavailable` + warning; may continue |

### Error message (English) — copy and stop (CANONICAL TEMPLATE — commands/adapters point here)

When a critical source fails, the orchestrator **prints and stops** (does not implement):

```text
## ERROR: MCP unreachable

I could not reach the MCP needed to continue.

| Field | Value |
|---|---|
| Source | Linear / Figma / Sentry / Notion / … |
| Expected server | linear-server / figma / sentry / … |
| Ref | ABC-123 / URL |
| Status | offline | auth_required | timeout | tool_error |
| Detail | <short technical message from the runtime> |

**What I did not do:** I did not invent content from that source and **did not** move on to implementation.

**How to unblock:**
1. Connect/authenticate the MCP in the project/session.
2. Run again: `/ruver-fd <same goal>`
```

Speak that block in the chat language (`ruver-memory`). Without this
message and without `result=blocked`, the run is **invalid**.

## Playbooks per source

### Linear (`linear-server`) — also [LINEAR.md](LINEAR.md)

```
get_issue(id, includeRelations: true)
list_comments(issueId) → paginate cursor to the end
get_issue on related/parent/children
extract_images if screenshots matter
```

Branch: [JOBS.md](../ruver-bus/JOBS.md) (`feature/<id-lowercase>`).

### Figma

Detect `fileKey` / `node-id` in the URL.

Typical order (project Figma MCP tools — **discover the schema with search_tool**):

1. Resolve file + node from the URL
2. `get_design_context` / `get_screenshot` / equivalent on the connected server
3. If skill `figma-design-to-code` / `figma-use` exists in the environment, follow its prerequisite
4. Summarize in `figma-context.md`: frames, copy, states, tokens, constraints

If the ticket **points at** Figma and MCP fails → STOP (do not invent layout).
If there is **no** Figma → UI follows [UI_DESIGN_SYSTEM.md](UI_DESIGN_SYSTEM.md): DS +
**recent same-type examples** in the repo (dialogs, forms, etc.).

### Sentry

Detect issue URL or id.

Typical tools (discover on the `sentry` server):

- get issue / latest event / stacktrace / tags / release
- breadcrumbs if relevant

Write `sentry-context.md`: title, culprit, stack, frequency, env, suspected root cause (hypothesis, not a fix).

Path `debug_fix` **must** consume this in diagnose.

### Notion

Detect page URL / id.

Typical tools:

- retrieve page / blocks children (paginate)
- search if you only have a title

Write markdown in `notion-context.md`.

### Generic ("etc")

For any other connected MCP (Slack, Jira, Confluence, …):

1. Detect URL/ID in the goal or Linear
2. `search_tool` by domain/product
3. Read-only fetch of the resource
4. File `.<source>-context.md` + entry in `mcp-sources.md`

## Execution order (node `mcp_context`)

```
1. Discover repo (PRODUCT.md) → STATE forge/tracker/pkg/cmds/scope/assignee/reviewers
2. Detect refs (goal + user)
3. For each needed source:
     a. pre-check MCP or CLI accessible?
     b. if critical and fail → English ERROR + result=blocked + STOP
     c. if ok → fetch → file
4. Tracker ok → branch checkout
5. Re-scan ticket body for more URLs → repeat 3
6. mcp-sources.md (ok | error | unavailable | skipped)
7. result: ok | partial | blocked
```

- `ok` = all critical sources ok
- `partial` = only optionals failed
- `blocked` = a critical source failed → **orchestrator does not call implement/ship**

## Downstream

| Node | Consumes |
|---|---|
| triage | tracker labels + Sentry? → bug path |
| grill / spec / tickets | tracker AC + Figma + Notion |
| diagnose | Sentry + tracker bug comments |
| implement | excerpts of `*-context.md` relevant to the ticket |
| reviewer | tracker/Figma/Notion AC |
| shipper | links in the PR/MR body |

## Anti-patterns

- Ignoring a Figma/Sentry link on the ticket
- Using Orca/CLI instead of MCP
- "I read the ticket title, that is enough"
- Inventing a Sentry stack or a Figma layout
- Blocking the graph on optional Notion that is not AC
