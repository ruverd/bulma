# CI/CD green = delivered

**Graph done:** PRs open and the applicable CI gate has passed. For ordinary
delivery and the umbrella, required checks must be green. Stack children
can use the documented proof below when CI is scoped away from their base.

Source of truth: **`gh pr checks`** on GitHub, **`glab ci status`** on GitLab
(not only `gh run list`). `forge=git` → no PR CI; `done_local`.
Wake: `schedule_wake` in [bulma-host](../bulma-host/SKILL.md). Follow
`nodes/ci_watch.md` + STATE `ci_fix_loops`.

## Sequence after quality

```
quality ok
 → commit + push
 → open ready-for-review PR or update existing PR
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

## Stack child CI

Use the normal hosted gate when the repository runs build or test checks
for the actual PR base. When a child lacks those checks, use the same
[workflow scope validator as code review](../bulma-code-review/references/PREFLIGHT.md#ci-out-of-scope-for-the-base).
Read workflows from the verified base commit. The candidate head cannot
change its own scope decision.

For a candidate out-of-scope result, run the relevant tester checks on the
clean, committed PR head in its recorded worktree. Its history includes
the pinned destination commit. Check the selected suites ran assertions
and capture receipts through [runtime evidence](../bulma-bus/PERFORMANCE.md).
Write the head SHA, base SHA, and receipt paths as
`{"head":"…","base":"…","receipts":["/path/to/result.json"]}` under the
worker state. Supply that proof to the script:

```bash
python3 <fd-skill>/scripts/stack-ci.py --checkout "$WORKTREE" --repo "$REPO" \
  --pr "$PR" --head-sha "$HEAD_SHA" --base "$BASE_BRANCH" --base-sha "$BASE_SHA" \
  --default "$DEFAULT_BRANCH" --proof "$PROOF_FILE"
```

Use the `out_of_scope` result only for the exact pair on its receipt. The
script checks live refs, reported checks, classic branch protection and
applicable rulesets, and verifies local receipts with `runtime.py check`.
Failed, pending, unreadable, or missing required checks need the ordinary
CI gate. If a required workflow rule applies, verify it through that gate.
An `in_scope` result with missing expected checks or an `unknown` result
does not pass. Re-run on head, base or test environment changes.

Store `ci.status: out_of_scope` separately from `green`. Report
**CI out of scope for this base**, with the local tests that ran.
The umbrella always needs hosted CI and, on the Developer route, integrated
QA. Preserve existing external QA-provider and required check policies.

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
  status: pending | watching | fixing | green | out_of_scope | escalated | skipped_no_pr
  pr_url: ...
  last_checks: summary
  fix_loops_used: 0
```

Graph `status: done` requires `ci.status: green` or a verified stack-child
`out_of_scope` result when there was a PR.

If this run sits **inside** the `bulma-developer` graph, `done` here
**does not** finish delivery: the developer orchestrator continues to
`mergeable` → `request_qa`. QA (comment + evidence on the PR) belongs to
`bulma-qa`, not this graph. `/bulma-fd` alone **does not** call QA.

## User summary

Call it **delivered** only when you have:

- PR URL
- CI outcome (green checks, or scope and local proof for a stack child)
- branch + SHA

Speak that summary in the chat language (`bulma-memory`). Fullstack: FE green + BE green. Forge notes stay English.
