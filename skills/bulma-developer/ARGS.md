# Args: ticket, goal, or resume

`$ARGUMENTS` (and the rest of the user message) must resolve to **one** of these. Do not ask which one if the text is enough.

## Parse (first, before admit)

Trim. Then, in order:

| Match | Mode |
|---|---|
| empty, and STATE exists with `status` not in `done` / `done_notes` | **resume** the current job |
| `resume` / `continue` (whole token, case-insensitive) | **resume** |
| Tracker issue URL, any vendor (detection: PRODUCT.md) | **ticket** |
| GitHub PR or GitLab MR URL, or envelope `QA_RESULT` FAIL+`PR_BUG` | **fix** (existing PR/MR) |
| issue id `[A-Z][A-Z0-9]+-\d+` | **ticket** (resolve tracker in PRODUCT.md; not a tracker gate) |
| free text with no resume, no STATE | **local goal** |
| empty, no STATE, no goal text | **stop** — ask for the ticket or the goal |

Examples:

```text
/bulma-developer ABC-123
/bulma-developer ABC-123: extra note
/bulma-developer https://linear.app/<workspace>/issue/ABC-123/...
/bulma-developer login button does nothing
/bulma-developer resume
/bulma-developer resume: the answer is B
```

`ABC-123: note` → ticket `ABC-123`, extra text is the note (and, if `waiting_user`, it is also the answer).

## Resume

Load, in order:

1. `$BULMA_ROOT/.bulma-developer/STATE.md`
2. `$BULMA_ROOT/.bulma-feature-delivery/STATE.md` (if present)
3. `$BULMA_ROOT/.bulma-feature-delivery/HANDOFF.md` (if present)
4. `$BULMA_ROOT/.bulma-bus/STACK.md` + `ENVELOPE.md`

**Reconcile** world vs STATE before skipping nodes. If fd STATE/HANDOFF
exist, replay that `## Invariants` block first. Then the developer checks.

| Check | Drift |
|---|---|
| `git rev-parse HEAD` vs `STATE.sha` | sha unknown; do not skip implement/review/tester on the old sha |
| `git branch --show-current` vs STATE branch | reconcile the checkout; do not invent a PR |
| PR `headRefOid` vs `STATE.sha` | follow the new head (mergeable / bot_review / QA) |
| `STATE.ci=green` and checks red | **ci_watch**, not done |
| UI After bound to an old sha | re-enter **evidence** |
| last `qa_verdict_log` row on another sha | that PASS does not count; QA again on HEAD |
| SPEC.md / TICKETS.md missing with status already past those nodes | re-enter spec/tickets |
| tracker `updatedAt` > STATE `updated_at` and AC changed | re-read AC; do not re-grill settled decisions unless an AC line contradicts a DECIDE row |

Skip a node only when its outputs exist **and** its invariants match.
Files matching STATE is not enough.

Then continue at `next_node` / current graph status. Do **not**:

- re-fetch the tracker as a blank start
- re-grill settled `## Decisions` (unless an AC line contradicts them)
- skip an open ASK; the current user message **is** the answer
- restart delivery if `fd_status=done` (go **mergeable** / **bot_review** / QA instead)

No STATE / no HANDOFF → tell the user in English that there is nothing to resume.

## After a waiting_user stop

The next invocation is resume, even if the user types the ticket id again. Attach their message as the ASK answer, then continue.
