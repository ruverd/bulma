# Agent-browser for QA stills and video

Status: accepted

`/qa` used to pick Playwright, Cypress, or a host browser MCP from
the target repo. Evidence went to a gist because `gh gist` rejects
binaries. The PR body had no visual proof at open.

QA execute on UI is now agent-browser. The app's e2e suite stays in
CI. Stills (before/after, two worktrees) go on the GitHub PR body at
ship via `gh pr edit --attach`. The walk video goes on the QA comment
via `gh pr comment --attach`. Session cookies live under
`~/.ruver/agent-browser/`, shared across worktrees.

`format.mjs` from vercel-labs/before-and-after is PolyForm Shield. We
did not copy it. `format.sh` here is MIT and images-only.

GitLab and `--no-pr` skip the body block. UI without agent-browser is
BLOCKED, not a silent skip.

Backend PRs still execute. Evidence is an attached HTTP still (PNG
of the call) or the FE screens that call those endpoints. Missing
UI is not a skip.
