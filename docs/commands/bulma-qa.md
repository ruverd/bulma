# `/bulma-qa`

Alias: **`/qa`**. Graph engineer for **product QA**. One
QA execute slot. Plan happy and user-break from the diff
before any click.
Comment with per-surface clips (a concatenated reel) or HTTP
stills on API. UI stills go on the PR body
([before-and-after](../../skills/before-and-after/SKILL.md)).

Skill: [`../../skills/bulma-qa`](../../skills/bulma-qa).

Browser work belongs to [agent-browser](https://agent-browser.dev/) and its
bundled Chrome for Testing. Uploads belong to `gh --attach`. This graph owns
the plan, the walk, the verdict, and the comment between them.

## Requires

- `agent-browser`, with its Chrome for Testing downloaded. `bulma setup`
  installs both and fails until they work. To install it yourself:
  `npm install -g agent-browser && agent-browser install`
  ([other methods](https://agent-browser.dev/installation)).
- GitHub CLI 2.99 or newer, for `gh pr comment --attach`.

Check the browser with `agent-browser doctor --offline --quick`. A UI PR
with a failing doctor is `BLOCKED`. QA never falls back to another browser.

## Why agent-browser only

agent-browser runs headless in its own Chrome for Testing, with its own
cookies under `~/.bulma/agent-browser/`. It never opens a window, never
touches your Google Chrome profile, and records clips the QA comment can
attach. A browser MCP server, a browser extension, or another plugin's
browser skill drives your real Chrome instead. So QA uses none of them,
even when the host offers them.

`ensure-session.sh` pins agent-browser to Bulma's own headless config through
`AGENT_BROWSER_CONFIG`. A `~/.agent-browser/config.json` or a repo's
`agent-browser.json` cannot turn on `headed`, a Chrome profile, or attach to
a running Chrome during QA.

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

## Scope

Does not run the app's Playwright or Cypress suite (that stays in CI), does
not install browsers at QA time, and does not use any browser other than
agent-browser.

## Related

[`/bulma-triage`](bulma-triage.md) · [`/bulma-developer`](bulma-developer.md) ·
[`/bulma-goal`](bulma-goal.md)
