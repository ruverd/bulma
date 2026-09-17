# `/ruver-qa`

Alias: **`/qa`**. Graph engineer for **product QA**. One
QA execute slot. Plan happy and user-break from the diff
before any click.
Comment with per-surface clips (a concatenated reel). UI stills
go on the PR body
([before-and-after](../../skills/before-and-after/SKILL.md)).

Skill: [`../../skills/ruver-qa`](../../skills/ruver-qa).

## When

- `/qa https://github.com/org/repo/pull/99`
- `/qa owner/repo#99`
- Envelope: `QA_REQUEST` from [developer](ruver-developer.md)

## Graph

```
PR from args or QA_REQUEST
  → admit          one slot; else enqueue
  → plan           blast radius + happy + user-break, before any click
  → execute        agent-browser clips or HTTP; then exploratory
  → triage?        product suspicion → bus → /ruver-triage
  → verdict        comment + video + QA_RESULT
```

## What “done” means

A PR comment on the **head SHA** with evidence (video and/or HTTP).
Chat-only is not done. Unit tests or `git show` are not a complete execute.

UI: agent-browser only. The app's Playwright/Cypress suite stays in CI.
Backend-only PRs with no UI sibling: HTTP the changed endpoints.
With a sibling UI: hit that screen when a caller exists.

## Slot

Never two executes. If another PR holds `qa_active`, this one
**enqueues** ([ruver-bus JOBS](../../skills/ruver-bus/JOBS.md)).

The graph engineer does **not** classify bugs. Suspicion →
[`/ruver-triage`](ruver-triage.md). After `TRIAGE_RESULT`, continue at
**verdict** (do not re-run execute).

## Never

- Spawn `ruver_triage` as a child.
- Skip the PR comment.
- `gh gist create` on `.webm` (use `scripts/publish-evidence.sh`).
- PASS without evidence (FE video, or HTTP record on API-only).
- PASS on a happy-only walk. User-break steps are required.
- Fall back to Playwright or a host browser MCP.

## Related

[`/ruver-triage`](ruver-triage.md) · [`/ruver-developer`](ruver-developer.md) ·
[`/ruver-goal`](ruver-goal.md)
