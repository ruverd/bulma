# Token economy (bulma-fd)

Goal: **less repeated context**, **short prompts**, **artifacts on disk**
instead of pasting megabytes into chat. Quality does not drop. Budget stays
for the end (CI green / handoff).

## Principles

| Do | Avoid |
|---|---|
| STATE + files under `.bulma-feature-delivery/` as memory | Re-pasting the whole tracker-context into every subagent |
| Whitelist per node (this ticket + refs) | "Read the whole monorepo" |
| Paths + 20–40 line excerpts | Dumping whole files into the prompt |
| Fresh subagent **with a minimal prompt** ([bulma-host](../bulma-host/SKILL.md) `spawn_worker`) | GRAPH.md, `why`, parent MCP/tool catalog, session history |
| 1 parallel tool call when independent | Re-read loops on the same file |
| User chat: short English (status + next step) | Narrating every tool call |
| Incremental commits | Loading a 50-file diff into the orchestrator |

## By phase

### mcp_context
- Fetch MCP → **write to a file**; in chat only: ids, counts, `mcp_gate`.
- Do not reprint the full description in the orchestrator.

### triage / grill / spec
- Read the **summary** of tracker-context (AC bullets), not the raw 10k tokens again if it is already on disk.
- Grill is the expensive model. Spec/tickets are synthesis, not a second interview.
- Coder prompt = this ticket + decisions + whitelist. Not the grill transcript.
- `plan_critic` is a table. Spawn only when `risk=elevated`. Skip on debug_fix, light_change, and `risk=low`.

### implement (subagents)
Coder prompt **at most ~1–2 screens**:

```
ticket N: <text>
done criteria: <bullets>
UI refs: path1, path2
contract: path or 15 lines
TDD: red→green
Do NOT read all of SPEC/TICKETS if the ticket text is already in the prompt
```

- Reviewer: path to `git diff` + files_touched + done criteria. Not the diff inline.
- One ticket per subagent. Do not "resume" with a monster transcript.
- Do not load `how` / `why` in the coder ([PSTACK.md](PSTACK.md)).
- Discovery: host `code_graph_explore` when `.codegraph/` or `.tokensave/` exists. No extra explorer worker.

### quality / CI
- Logs: only the **tail** of the failure (`gh run view --log-failed`, filtered).
- Do not paste a full typecheck if the error is five lines.
- **Declared exception:** the quality node MAY load the touched files in full.
  It is the only node with that license (structural audit needs the whole file).
  Branch diff only, never "the monorepo".

### fullstack / Orca
- Worker spec: compact HANDOFF + paths to context files **in the worktree**, not a paste.

## User-facing compression

Unslop. [VOICE.md](VOICE.md). Preferred format (spoken in English):

```text
S: phase + branch + mcp_gate
D: what changed (1–3 bullets)
P: next step / blocker / PR+CI
Walk: ✓mcp ✓triage ●grill ○spec ○tickets …
```

Walk marks: [VOICE.md](VOICE.md). One line. Do not paste GRAPH.md.

No preamble "I will now…".

## Orchestrator: anti-waste

1. **Do not** re-run MCP if `mcp_gate: passed` and context files exist (resume), unless [HANDOFF.md](HANDOFF.md) invariants drifted.
2. **Do not** re-triage if path/scope/risk is already in STATE (unless the goal changed or invariants drifted).
3. Before a limit handoff: **stop expanding scope**; close the current phase + write HANDOFF.
4. Prefer host `code_graph_explore` (required when an index exists) over `read` of 1k+ line files.

## Do not cut

- TDD evidence (paths + command + pass/fail)
- MCP gate errors
- Contract in the blocker comment
- CI check names + links when red
