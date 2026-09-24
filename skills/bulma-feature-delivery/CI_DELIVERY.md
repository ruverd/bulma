# CI/CD green = delivered

**Graph done:** PR(s) open **and** **all** CI/CD checks green. Until then the
task is **not** delivered (`status` ≠ `done`).

Source of truth: **`gh pr checks`** on GitHub, **`glab ci status`** on GitLab
(not only `gh run list`). `forge=git` → no PR CI; `done_local`.
Wake: `schedule_wake` in [bulma-host](../bulma-host/SKILL.md). Follow
`nodes/ci_watch.md` + STATE `ci_fix_loops`.

## Sequence after quality

```
quality ok
 → commit + push
 → create/update draft PR
      reviewers/assignee: PRODUCT.md
 → ci_watch (required if open_pr)
      pending → poll checks (short calls, ~5 min apart)
      fail → diagnose + fix (coder subagent) + push → re-check
      green → status=done
```

PR packaging (shipper): reviewers and assignee per [PRODUCT.md](PRODUCT.md).

With **`--no-pr`**: local delivery = tester + quality ok; PR CI does not apply.
If the user still says "deliver it", prefer opening a PR and waiting for green CI.

Fullstack: **each** PR (FE and BE) must be green. Delivered only when **both** are green.

## Commands

```bash
gh pr view --json number,url,headRefName,statusCheckRollup
gh pr checks --json name,bucket,state,workflow,link
# poll: repeat the call above until green/fail (~5 min apart).
# NEVER depend on `gh pr checks --watch` finishing in one tool call.
# A dead watch is not a CI fail.

# GHA logs if the link is Actions
gh run view <run-id> --log-failed
```

Green = no **required** check in `fail` / `pending` / failed `cancelled`. Prefer:

- every `state` success (or a neutral skip if the repo treats skip as ok)
- `bucket` / required: if `gh` exposes required, require those; otherwise
  **every** check attached to the PR

## Fix loop

1. Extract the **first** actionable failure.
2. Coder / fix-ci subagent: smallest diff.
3. Commit + push (no force).
4. Re-run full `gh pr checks`.
5. Repeat until green or the cap:

```yaml
ci_fix_loops: 5   # default; lower on repos whose CI exceeds 15 min
```

If loops blow / infinite flake / failure on main that is unrelated:

- merge latest `main` when that is the case
- or `status: escalated` + a chat-language summary (PR URL, red checks, logs)

**Forbidden:** declare done with CI red/pending.
**Forbidden:** skip git hooks to fake a green commit.

## STATE

```yaml
ci:
  status: pending | watching | fixing | green | escalated | skipped_no_pr
  pr_url: ...
  last_checks: summary
  fix_loops_used: 0
```

Graph `status: done` **only** if `ci.status: green` (when there was a PR).

If this run sits **inside** the `bulma-developer` graph, `done` here
**does not** finish delivery: the developer orchestrator continues to
`mergeable` → `request_qa`. QA (comment + evidence on the PR) belongs to
`bulma-qa`, not this graph. `/bulma-fd` alone **does not** call QA.

## User summary

Call it **delivered** only when you have:

- PR URL
- CI green (check list or "all green")
- branch + SHA

Speak that summary in the chat language (`bulma-memory`). Fullstack: FE green + BE green. Forge notes stay English.
