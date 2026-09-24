# QA → Bug Triage Handoff

If QA finds a potential product error, **do not make the final bug
determination**. Hand the failure to **bulma_triage**.

The handoff **must always include the PR link**.

Send **one** `TRIAGE_REQUEST` after the plan finishes, containing
**every** `## F<n>` from `.bulma-qa/FINDINGS.md`. Do not drop
findings. Do not spawn a second triage run per finding.

## Required payload

* **PR link (required)**
* PR number, title, repository, branch, commit
* tracker issue, when available
* plan path (`.bulma-qa/PLAN.md`)
* each finding: step, surface, expected, actual, reproducible,
  evidence (agent-browser / video / screenshots / API / logs),
  whether the failing code is in this PR's diff
* `payload_path` if the body would be huge

Omit a field only when it does not exist. Never omit the PR link.

## Handoff text

```text
Potential bug(s) found during QA.

PR: https://github.com/<org>/<repo>/pull/<n>
PR number: <n>
PR title: <title>
Repository: <org/repo>
Feature: <feature>
Tracker: <ticket or none>
Branch: <head>
Commit: <sha>
Plan: .bulma-qa/PLAN.md
Findings file: .bulma-qa/FINDINGS.md

## F1
Plan step: S<n> — <title>
Surface: <route / endpoint>
In this PR diff: yes | no | unknown
Reproduction:
1. ...
Expected:
<...>
Actual:
<...>
Reproducible: yes | no | unknown
Evidence:
- agent-browser: <name + exit + excerpt>
- Video: <path or none>
- Screenshots: <paths or none>
- API: <or none>
- Logs: <or none>
Suspected root cause: <or unknown>

## F2
...

Please classify **each** finding. Open a tracker issue only for findings
that are real product bugs and **not** caused by this PR.
```

## After triage returns

Use `TRIAGE_RESULT.classification` for the **PR** verdict
(PR_BUG wins if any finding is PR_BUG). Per-finding tracker ids
go in the QA comment notes.

| Classification | QA verdict |
|---|---|
| `PR_BUG` | `FAIL` |
| `NEW_BUG` / `EXISTING_BUG` | Do **not** fail the PR. Report the tracker ids. QA = `PASS` with notes, unless an AC of *this* PR is also broken. |
| `NOT_A_BUG` | Continue / `PASS` if the rest of the surface holds |
| `BLOCKED` | `PENDING_TRIAGE` or `BLOCKED` — do not invent a bug |

`NEW_BUG` / `EXISTING_BUG` means the product is wrong but **this PR
is not the cause**. That is not a PR `FAIL`.
