# Developer → bulma_qa

Request QA only after implementation, tests, draft PR, CI green,
MERGEABLE, and bot_review skip or pass.

## Payload

```text
QA requested after delivery.

PR: https://github.com/<org>/<repo>/pull/<n>
Repo: <org/repo>
Branch: <head>
SHA: <sha>
Job: <dev-<ticket>>
Tracker: <ticket or none>
Environment: <local / preview / notes>

Ticket requires:
<ACs>

Implemented:
<what changed>

Expected behavior:
<...>

Edge cases:
<...>

Setup:
<auth, flags, seed data>

Please validate the behavior. Build `.bulma-qa/PLAN.md` from the
diff (happy and user-break walks) before running anything. Do not
assume green CI means the feature is correct.
```

PR link is required.

## After QA returns

| QA | Action |
|---|---|
| `PASS` | `gh pr ready`. Report to user. PR is Ready, **unmerged**. |
| `FAIL` after triage `PR_BUG` | Fix on the same branch → CI → MERGEABLE → bot_review → QA again |
| `PASS` with `NEW_BUG` / `EXISTING_BUG` | Do not pad this PR. Cite the tracker ids. |
| `NOT_A_BUG` | Treat as pass unless an AC of this PR is still broken |
| `BLOCKED` / `PENDING_TRIAGE` | Wait or escalate. Do not invent product behavior. |

Product ambiguity → escalate to the user. Do not invent behavior.
