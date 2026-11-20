# CI + mergeability gates

Do not treat "CI is green" as enough. Both must be true:

```text
CI gate = passed
AND
mergeability = MERGEABLE
```

## Check

```bash
gh pr view "$PR" --repo "$REPO" \
  --json url,isDraft,mergeable,mergeStateStatus,statusCheckRollup,headRefOid,headRefName

gh pr checks "$PR" --repo "$REPO" --json name,bucket,state,workflow,link
```

Follow `bulma-feature-delivery` `CI_DELIVERY.md` for the poll/fix loop.
Never use `gh pr checks --watch` as the only wait (tool timeout < CI).

## CI green

No **required** check in fail / pending / cancelled-as-fail.
If GitHub does not expose required, treat every attached check as required.
For a stack child only, a verified `out_of_scope` receipt with matching
local tests satisfies the CI gate. See
[Stack child CI](../../bulma-feature-delivery/CI_DELIVERY.md#stack-child-ci).

## MERGEABLE

`mergeable == MERGEABLE` (or `mergeStateStatus == CLEAN`).

Not ready: `CONFLICTING`, `DIRTY`, `BLOCKED`, `UNKNOWN`, pending.

Conflicts on this branch → rebase onto origin/<base> when safe, push, re-check CI.
`--force-with-lease` on the task branch only. Never on main/master. Never `--force`.

## Review status

Open new delivery PRs ready for review. Existing PRs keep their draft flag,
including after QA. Use the verified head for bot review and, where applicable, QA after CI
and mergeability. Separate reviewer and repository approval
rules still apply. Bulma never merges.
