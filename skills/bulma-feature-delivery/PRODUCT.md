# Product — discover this repo, then follow it

Graphs never name a company. Run this at `mcp_context`. Write STATE.
Later nodes **read STATE**. They do not re-guess unless files appeared.
Ship re-reads §6 (assignee / reviewers).

If two options fit, pick what the **neighbor file already does**. Log DECIDE.
ASK only when the ticket cannot be done without a fact you cannot discover.

Read first, when present: `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`.
Those win over heuristics.

## 1. Forge (where PRs live)

| Probe | `forge` | PR CLI |
|---|---|---|
| `gh repo view` works | `github` | `gh` |
| `glab repo view` works | `gitlab` | `glab` |
| git remote only | `git` | none. Push if a remote exists. No PR unless the user has a CLI |

`--no-pr` or `forge=git` → ship is commit (+ push). Not a GitHub PR.

## 2. Tracker (where the ticket lives)

From the **goal**, not from this plugin:

| In the goal | `tracker` | How to read |
|---|---|---|
| `linear.app/...` | `linear` | Linear MCP. Critical. [LINEAR.md](LINEAR.md) |
| `github.com/.../issues/N` | `github_issues` | `gh issue view` |
| `github.com/.../pull/N` | (PR, not a ticket) | fix path |
| GitLab issue / MR URL | `gitlab` | `glab` |
| Jira / `atlassian.net` | `jira` | Jira MCP if connected |
| Notion/Figma/Sentry URL | that source | its MCP. Critical only if it is the spec or the bug |
| Bare `ABC-123` | try Linear MCP if connected, else `gh issue view`, else **local goal** with that token in the text | Bare id is **not** a Linear hard gate |
| Free text, no URL | `none` | local goal. No tracker MCP required |

Do not STOP because Linear is missing on a local goal.
STOP when the user pasted a tracker URL and that source cannot be read.

Branch: [JOBS.md](../bulma-bus/JOBS.md) §Worktree. Tracker id → always
`feature/<id-lowercase>` (`DEV-4525` → `feature/dev-4525`). Not
`gitBranchName`. Not `{login}/<id>`. No id → `feature/<slug>`.

## 3. Toolchain

Lockfile / manifest wins:

| File | `pkg` |
|---|---|
| `bun.lock` / `bun.lockb` | `bun` |
| `pnpm-lock.yaml` | `pnpm` |
| `yarn.lock` | `yarn` |
| `package-lock.json` | `npm` |
| `go.mod` | `go` |
| `Cargo.toml` | `cargo` |
| `pyproject.toml` / `poetry.lock` / `requirements.txt` | `uv` / `poetry` / `pip` (whichever file exists) |
| `Gemfile` | `bundle` |
| `Package.swift` | `swift` |
| `mix.exs` | `mix` |
| `*.csproj` / `*.sln` | `dotnet` |
| `Makefile` / `justfile` | those recipes, on top of the language |

Commands. Prefer `AGENTS.md`, then `package.json` scripts, then language defaults.
Write `typecheck_cmd`, `test_cmd`, `lint_cmd`, `e2e_cmd` (empty if none).

Examples of names to look for, not to invent: `typecheck`, `tsc`, `test`,
`test:unit`, `lint`, `test:e2e`, `cargo test`, `go test ./...`, `pytest`.

Never run `npm` when the lockfile is bun/pnpm/yarn.

## 4. Topology

| Signals in **this** git root | `scope` |
|---|---|
| UI (react/vue/svelte/next/nuxt/vite/angular, SwiftUI, Compose, `app/`, `pages/`, `src/App`, `*.tsx` routes) and no API | `frontend_only` |
| API (express/nest/elysia/gin/axum/rails/django/fastapi/spring, OpenAPI, controllers, `src/modules`) and no UI | `backend_only` |
| Both in this git root (`apps/web` + `apps/api`, `frontend/` + `backend/`, …) | `mono` |
| Ticket needs UI **and** API, this root is one side | `fullstack` if a sibling resolves; else stay here |
| Infra/docs/skills only | `frontend_only` is wrong. `path: light_change`. No browser QA |

`mono` is one checkout. Not two worktrees.

Sibling, only for `fullstack`:

1. `$BULMA_FRONTEND` / `$BULMA_BACKEND`
2. `AGENTS.md` `## Product (bulma)` keys `frontend` / `backend`
3. `orca project list --json` only if `orca status --json` works
4. Else stay. Do not invent a sibling

ASK only if the ticket cannot ship without the other side.

## 5. QA tool

| What exists | `qa_tool` |
|---|---|
| UI (routes, screens, widgets, layout) | `agent-browser`. Stills + video. [before-and-after](../before-and-after/SKILL.md) |
| API, no UI, no sibling | `http`. Curl the changed endpoints. Attach an HTTP still (PNG). No invented screen |
| API + resolved frontend | FE route if a caller exists (`agent-browser`), else `http` |
| Infra/docs, no screen | `none`. No browser QA |

The app's Playwright/Cypress suite is CI (`e2e_cmd`). QA does not run
it. Missing `agent-browser` on a UI PR is BLOCKED, not a host-MCP
fallback. Missing UI on an API PR is not a skip.

One execute slot. Never two browser runs. UI PASS needs an
agent-browser `.webm`. HTTP still (PNG of the call) is enough on
`qa_tool=http`. FE screens of callers are enough when resolved.

## 6. Assignee and reviewers

Resolve **at PR open** (ship). mcp_context may prefill STATE. Shipper
re-reads this section. Do not invent handles. Never request `$ME` or a
bot.

**Assignee:** `AGENTS.md` if listed, else forge user (`gh api user --jq .login`
or `glab api user`). Never `git config user.name`.

**Reviewers:**

| Order | Source | `reviewers_status` |
|---|---|---|
| 1 | `AGENTS.md` listed reviewers | `confirmed` |
| 2 | `CODEOWNERS` file with owners for the changed paths | `confirmed` |
| 3 | `$BULMA_ROOT/memory.md` `## Product` reviewers (`bulma-memory`) | `confirmed` |
| 4 | Merged-PR history (below) | `proposed` |
| 5 | Still empty | `missing` |

No `CODEOWNERS` file (`CODEOWNERS`, `.github/CODEOWNERS`,
`docs/CODEOWNERS`), or none matching: skip row 2.

Shipper requests only `confirmed` (`gh pr edit --add-reviewer` /
`glab mr update --reviewer`, one failure must not block the rest).
Open the draft PR anyway if `proposed` or `missing`. Do not block CI.

Orchestrator, after ship, asks **one** question (chat language from
`bulma-memory`). Next user message writes project `## Product`
(that is confirmation) and adds the reviewers to the open PR. If
they do not answer this turn, append the question to project
`## Open`. After confirmation, DECIDE from memory. This ASK is
last-resort: wrong humans on the PR is hard to reverse, and the list
is uncertain until then.

### History probe (GitHub)

One call. Last 20 merged PRs. Count `APPROVED` + `CHANGES_REQUESTED`
per human login. Drop the PR author, `$ME`, and bots (`[bot]`,
dependabot, renovate, copilot, codecov). Top 3 → `proposed`.

```bash
gh api graphql -F owner=OWNER -F name=REPO -f query='
query($owner:String!,$name:String!) {
  repository(owner:$owner, name:$name) {
    pullRequests(states: MERGED, last: 20,
                 orderBy: {field: UPDATED_AT, direction: DESC}) {
      nodes {
        author { login }
        reviews(last: 20) { nodes { state author { login } } }
      }
    }
  }
}'
```

GitLab: same idea on merged MRs (`glab api`). Same filters.

Tracker **NEW_BUG** assignee: the session user on that tracker
(email match). Never a hardcoded person.

## 7. CI

Poll required checks ~5 min. `gh pr checks` or `glab ci status`.
No assumed duration.
Skip locally when the command is expected **>10 min**, or listed in
`AGENTS.md` / `$BULMA_CI_LOCAL_SKIP`.

## 8. Orca

Optional. Never a gate. Default: `git worktree` + host `spawn_worker`
([bulma-host](../bulma-host/SKILL.md)).

## 9. Review bot

Same last-20-merged-PR probe as §6. On each review author also read
`__typename` (GraphQL) or `user.type` (REST / GitLab).

A review bot is a review author whose login ends with `[bot]`, or whose
GitHub user type is `Bot`. Do not name a vendor as *the* bot. Do not
hardcode a product. Detect from this history.

Write `review_bot`: the distinct bot logins that authored those reviews,
or empty. Empty means skip. Developer `bot_review` re-reads this section
and writes the field on developer STATE.

GitLab: same idea on merged MRs (`glab api`). Same filters.
