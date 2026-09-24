# `/bulma-qa`

Alias: **`/qa`**. Graph engineer for **product QA**. One
QA execute slot. Plan happy and user-break from the diff
before any click.
Comment with per-surface clips (a concatenated reel) or HTTP
stills on API. UI stills go on the PR body
([before-and-after](../../skills/before-and-after/SKILL.md)).

Skill: [`../../skills/bulma-qa`](../../skills/bulma-qa).

## When

- `/qa https://github.com/org/repo/pull/99`
- `/qa owner/repo#99`
- Envelope: `QA_REQUEST` from [developer](bulma-developer.md)

## Graph

```
PR from args or QA_REQUEST
  → admit          one slot; else enqueue
  → plan           blast radius + happy + user-break, before any click
  → execute        agent-browser clips or HTTP; then exploratory
  → triage?        product suspicion → bus → /bulma-triage
  → verdict        comment + evidence + QA_RESULT
```

## What “done” means

A PR comment on the **head SHA** with evidence (UI video and/or
HTTP still). Chat-only is not done. Unit tests or `git show` are
not a complete execute.

UI: agent-browser only. The app's Playwright/Cypress suite stays in CI.
A backend PR still runs. Prove the changed endpoints with an HTTP
still, or by walking the FE screens that call them. Missing UI is
not a skip.

## Slot

Never two executes. If another PR holds `qa_active`, this one
**enqueues** ([bulma-bus JOBS](../../skills/bulma-bus/JOBS.md)).

The graph engineer does **not** classify bugs. Suspicion →
[`/bulma-triage`](bulma-triage.md). After `TRIAGE_RESULT`, continue at
**verdict** (do not re-run execute).

## Never

- Spawn `bulma_triage` as a child.
- Skip the PR comment.
- `gh gist create` on `.webm` (use `scripts/publish-evidence.sh`).
- PASS without evidence (FE video, or HTTP still / FE screens on API).
- PASS on a happy-only walk. User-break steps are required.
- Fall back to Playwright or a host browser MCP.

## Related

[`/bulma-triage`](bulma-triage.md) · [`/bulma-developer`](bulma-developer.md) ·
[`/bulma-goal`](bulma-goal.md)
