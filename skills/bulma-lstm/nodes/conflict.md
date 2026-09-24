# Node: conflict

**Verb:** rebase

Always. User rule: merge conflicts are never left sitting.

Same branch. No new PR. If the PR is draft, it stays draft.

```bash
git fetch origin
git rebase "origin/$BASE"
# resolve, commit
git push --force-with-lease
```

`--force-with-lease` only. Never `--no-verify`.
See [JOBS.md](../../bulma-bus/JOBS.md) §Worktree.

Already rebasing in an Orca/worktree for this PR → do not start a
second rebase. Note it and continue to **verify**.

Rebase fails (needs a human on binary/generated files) →
`HUMAN INTERVENTION REQUIRED`, escalate, still run **verify** on
what can be read so comments are not ignored.
