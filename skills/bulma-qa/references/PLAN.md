# QA test plan (from the PR diff)

Write `.bulma-qa/PLAN.md` **before** any browser or HTTP step.
Do not execute until the inventory and numbered steps exist.

Source of truth for *how* to plan. Execute walks that file.

## Inputs

```bash
gh pr view "$PR" --json number,title,url,body,files,headRefOid,headRefName
gh pr diff "$PR" --name-only
```

Also: tracker ACs when a ticket id exists; envelope `QA_REQUEST` ACs.

Never invent ACs. If the tracker is down, plan from PR body + diff only.

## Inventory

Classify every changed path (skip lockfiles, generated graphql
types unless the query/mutation itself changed):

| Path kind (match the diff, not a baked tree) | Kind | Surface to exercise |
|---|---|---|
| Pages / routes / screens (`app/`, `pages/`, `src/App`, views) | screen | That route |
| Shared components | widget | Screens that import it |
| Design system / `ui` | visual | Desktop, and mobile only if layout/CSS/media/DS changed |
| API client / hooks / services | REST | HTTP path + UI that calls it (if UI exists) |
| GraphQL operations | GraphQL | Operation name + UI that uses it |
| hooks / contexts / state | state | Every screen that reads that state |
| API routes / handlers / controllers / services | endpoint | HTTP method/path. FE screen **only if** a frontend exists in-repo or `$BULMA_FRONTEND` resolves ([PRODUCT.md](../../bulma-feature-delivery/PRODUCT.md)) |
| `tests/`, `*.spec.ts` | skip | App CI owns the spec. Do not add an execute step for it |
| auth, router, middleware, flags | cross-cut | The user-visible routes those files gate |

One row per distinct **surface** (route or endpoint). Group
files that only exist to serve the same screen.

## Blast radius

Map each changed file or symbol to the **user flows** that call it.
Grep, or CodeGraph when the repo has it. Do not add GitNexus as a
required tool.

| Changed | d=1 callers / screens | User flow to walk | Risk |
|---|---|---|---|
| | | | |

d=1 will break (direct callers). d=2 likely. d=3 maybe. Zero
callers is **UNKNOWN**, not skip. UNKNOWN goes under Coverage gaps
(why the walk could not resolve callers) **or** an extra step that
hits a suspected host screen. Do not drop the row.

Risk: LOW fewer than 5 d=1 callers, MEDIUM 5-15, HIGH more than 15
or many flows, CRITICAL on auth / billing / tenant. UNKNOWN stays
UNKNOWN until a search shows the symbol is unused.

Every user flow in this table must appear as a plan step. Happy +
user-break still apply on process surfaces.

## Steps

Each step is **one walk**: the intended use, or one user-break on
the same surface. Do not pack several attempts into a `variants` list.

```markdown
### S<n> — <short title>
- files: <paths from this PR>
- kind: screen | endpoint | state | visual
- route: </path or n/a>
- endpoint: <METHOD /path or GQL op or n/a>
- acs: <AC ids / quotes this step covers, or n/a>
- intent: happy | user-break
- how:
  1. ...
- pass_if: <observable>
```

Rules:

- If any step is an authenticated screen, S1 (or an explicit setup
  step) is **log in** via session restore, then the repo helper if
  restore missed. Later steps assume a session. Login is setup, not
  a user-break.
- Happy path of every AC the PR claims (`intent: happy`).
- **User-break on every process this PR changes.** `kind: screen`,
  `state`, `endpoint`, and the host screen of a widget. `kind: visual`
  with no operable control: stills only (empty/overflow on a host
  screen if one exists). Derive from *this* flow, not a menu. On the
  snapshot and the diff, ask:
  1. **Wrong use.** Controls this change exposes or now depends on:
     empty, invalid, too long, wrong type, submit twice, confirm then
     cancel. One step per distinct mistake class, not one per input.
  2. **Interrupted transition.** Submit, next, back, close, navigate:
     refresh, browser back, leave and return, open a later step by URL.
  3. **Around the gate.** Auth, role, flag, or validation this PR
     added or relies on: signed out, wrong role, flag-off, skip the
     client check and hit the endpoint.
- Do not skip a user-break because the PR did not add an error state.
  Users still make those mistakes on fields this change now depends on.
- Skip a user-break only when the repo has no fixture for it (no
  second role, no OTP helper). Write that under Coverage gaps with
  why. "Unlikely" is not a reason.
- Other screens that **read the same state**, after happy *and* after
  a user-break that wrote data.
- Desktop + mobile only when layout/CSS/media/DS changed.
- Do not name or run an e2e spec. `qa_tool` is `agent-browser` or `http`.
- Targeted REST/GQL checks when the PR changes a service/endpoint
  even if a screen step exists (the walk can miss the contract).
  Endpoint user-breaks: missing required field, unauthenticated if
  gated, duplicate POST on a mutation.
- **Backend-only PR, no frontend sibling:** still run. HTTP the
  changed endpoints (happy + user-break) and render each call to an
  HTTP still. Do not invent a screen.
  Missing UI is not a skip. `git show` / unit/CI alone is still not a
  complete plan.
- **Backend-only PR with a resolved frontend:** map the handler to
  the UI that calls it and exercise that route (happy + user-break).
  Those screens are the proof. If no caller exists, HTTP still as
  above.
- A plan that is only `intent: happy` (plus login) is not a plan.
  Rewrite before execute.

User-break `pass_if`: the product refuses or recovers in a way the
user can see. Silent success, crash, blank screen, lost data, or a
5xx is a finding, not a pass.

## Gate before execute

PLAN.md must have: inventory table, blast radius table, ≥1
`intent: happy` step, ≥1 `intent: user-break` step per process
surface (or a Coverage-gaps line that names the missing fixture),
`intent` and `pass_if` on every step. Empty plan → stop and ask
(no route and no endpoint). A backend diff with handlers is a plan.
Missing UI is not a skip. Happy-only plan → rewrite, do not execute.
Blast radius with an UNKNOWN row and no Coverage-gaps line and no
extra step → rewrite, do not execute.

Chat (`bulma-memory`): list the steps in one short block, then execute.
Do not wait for approval unless the user asked to review the plan.
