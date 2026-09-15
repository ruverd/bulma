---
name: ruver-qa
category: graph
description: >
  Graph: QA a PR. One slot (queue extras). Plan happy and
  user-break from the diff, then agent-browser or HTTP. Bus
  TRIAGE_REQUEST on product errors. Use when /qa, /ruver-qa, or
  a QA_REQUEST arrives.
argument-hint: "<PR url or owner/repo#N>"
---

# Ruver QA (graph)

Orchestrator. You do **not** make the final bug call.

**REQUIRED:** [GRAPH.md](GRAPH.md) · [STATE.schema.md](STATE.schema.md) ·
[ruver-host](../ruver-host/SKILL.md) ·
`ruver-bus` PROTOCOL.md · `ruver-memory` ·
[DISK.md](../ruver-bus/DISK.md) (`.ruver-*` is **global**, never git root)

Chat: `ruver-memory`. Unslop always. PR link required (args or envelope).
Worktree and branch rules: [JOBS.md](../ruver-bus/JOBS.md) §Worktree.

Init `.ruver-qa/STATE.md`. Walk GRAPH:
**admit → resolve → plan → execute**.
`admit` claims the single QA slot or **enqueues** (never two
executes). `plan` writes `.ruver-qa/PLAN.md` from the diff (happy and
user-break) before any test. Spawn execute nodes only.
Outbound triage → **bus switch** to `triage`. Never spawn `ruver_triage`.

On `TRIAGE_RESULT`, continue at **verdict** (do not re-run execute).
When done: `scripts/publish-evidence.sh` posts the QA comment with
`--attach` (never gist) ([references/COMMENT.md](references/COMMENT.md)),
then write `QA_RESULT` and **pop** the bus stack. Chat-only is not done.

UI execute is agent-browser
([before-and-after](../before-and-after/SKILL.md)). Do not run the
app's Playwright/Cypress. Run agent-browser headless. Never use the
OS `open` command, Google Chrome.app, `--headed`, `--auto-connect`,
`--cdp`, `--profile`, or a host browser MCP. Backend-only PRs: HTTP the changed
endpoints unless a frontend sibling is resolved
([PRODUCT.md](../ruver-feature-delivery/PRODUCT.md)).
Unit/CI/`git show` alone is not a complete QA execute.
