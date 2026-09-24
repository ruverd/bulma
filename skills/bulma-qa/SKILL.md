---
name: bulma-qa
category: graph
description: >
  Graph: QA a PR. One slot (queue extras). Plan happy and
  user-break from the diff, then agent-browser or HTTP. Bus
  TRIAGE_REQUEST on product errors. Use when /qa, /bulma-qa, or
  a QA_REQUEST arrives.
argument-hint: "<PR url or owner/repo#N>"
---

# Bulma QA (graph)

Orchestrator. You do **not** make the final bug call.

**REQUIRED:** [GRAPH.md](GRAPH.md) · [STATE.schema.md](STATE.schema.md) ·
[bulma-host](../bulma-host/SKILL.md) ·
`bulma-bus` PROTOCOL.md · `bulma-memory` ·
[DISK.md](../bulma-bus/DISK.md) (`.bulma-*` is **global**, never git root)

Chat: `bulma-memory`. Unslop always. PR link required (args or envelope).
Worktree and branch rules: [JOBS.md](../bulma-bus/JOBS.md) §Worktree.

Init `.bulma-qa/STATE.md`. Walk GRAPH:
**admit → resolve → plan → execute**.
`admit` claims the single QA slot or **enqueues** (never two
executes). `plan` writes `.bulma-qa/PLAN.md` from the diff (blast radius,
happy and user-break) before any test. Spawn execute nodes only.
Outbound triage → **bus switch** to `triage`. Never spawn `bulma_triage`.

On `TRIAGE_RESULT`, continue at **verdict** (do not re-run execute).
When done: `scripts/publish-evidence.sh` posts the QA comment with
`--attach` (never gist) ([references/COMMENT.md](references/COMMENT.md)),
then write `QA_RESULT` and **pop** the bus stack. Chat-only is not done.

UI execute is agent-browser
([before-and-after](../before-and-after/SKILL.md)).
Per-surface clips: [references/VIDEO.md](references/VIDEO.md).
Do not run the app's Playwright/Cypress. Run agent-browser headless.
Never use the
OS `open` command, Google Chrome.app, `--headed`, `--auto-connect`,
`--cdp`, `--profile`, or a host browser MCP. A backend PR still runs
(admit → plan → execute). Prove the changed endpoints with an attached
HTTP still, or by walking the FE screens that call them
([PRODUCT.md](../bulma-feature-delivery/PRODUCT.md)).
Missing UI is not a skip. Unit/CI/`git show` alone is not a complete
QA execute.
