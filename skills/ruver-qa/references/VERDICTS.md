# QA verdicts

Exactly one:

| Verdict | When |
|---|---|
| `PASS` | Surface holds, including walked user-break steps. Every Must AC was observed in the running app (app-level). Unproven Must is not PASS. A happy-only walk is not PASS. A login-wall / Check-your-email .webm is not PASS (re-record or BLOCKED). Or triage said `NOT_A_BUG` and nothing else failed. Or triage said `NEW_BUG` / `EXISTING_BUG` (unrelated) and this PR's ACs still hold. |
| `PENDING_TRIAGE` | Potential product error handed off; triage not back yet. |
| `FAIL` | Triage returned `PR_BUG`, **or** the failure is unambiguous. |
| `BLOCKED` | Cannot run QA (no PR link, no env, no auth, cannot start the app). |

## Unambiguous FAIL (triage optional)

All must be true:

1. Reproduced at least twice on the tested SHA
2. Violates an AC or stated expected behavior of **this PR**
3. Failure lives in code the PR changed (or a test the PR added)
4. Not explained by env, auth, fixture, or flaky timing
5. Evidence (steps + actual/expected + artifact) is attached

If any item is missing → append a finding and hand off. Do not FAIL.

Findings collected while walking the plan always go to triage
(one `TRIAGE_REQUEST` after the last step) unless the run is
`BLOCKED` (cannot execute) or this unambiguous FAIL already
applies to an AC of **this** PR.

## PR comments

**Required** after a final `PASS` / `FAIL` / `BLOCKED`.

Follow [COMMENT.md](COMMENT.md): one `gh pr comment --attach` with
the QA header and the walk video (per-surface reel).

Chat report is not enough. Never comment `PENDING_TRIAGE`.
A run without that comment is not finished.
