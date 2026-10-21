# 4. Fetch — patches first, file bodies later

```bash
gh pr checks "$PR" --repo "$REPO"        # only for the failing/pending check names
```

Do not Read product files until Phase 1 has written `AC.md`.

## 4.0 Patches and file list

Write both under `$BULMA_ROOT/.bulma-code-review/`:

- `PATCH.diff` — the unified diff this pass will bind against
- `FILES.txt` — one changed path per line

**Deep** — full PR diff:

```bash
gh pr diff "$PR" --repo "$REPO"
```

Save the full PR path list as `PR_FILES.txt` for the human-signoff gate in
[PREFLIGHT.md](../references/PREFLIGHT.md). Use paginated
`gh api "repos/$REPO/pulls/$PR/files?per_page=100" --paginate`, including
`previous_filename` for renames. Incomplete file evidence blocks approval.

**Light** — incremental diff only, between exact commits:

```bash
git diff "$OLD_SHA..$HEAD_SHA"
```

Fetch the exact commits into the review checkout first. Save the unified diff
as `PATCH.diff` and its changed paths as `FILES.txt`. Missing old SHA or a
force-push/rebase → full PR diff and **deep** pass, noting `stale_base` in chat,
unless [pass_decision.md](pass_decision.md) §Rebase only proved the same content.
A prior REQUEST_CHANGES or DEFER `coverage|uncertainty|critic_failed` of mine
also forces the full PR diff and a deep pass
([pass_decision.md](pass_decision.md)).
Read source from `HEAD_SHA`, never from a moving branch or unrelated checkout.
Verify the PR head before and after fetching its diff; retry if it moved.

## 4.1 Risk

```bash
python3 scripts/classify-risk.py --files-from FILES.txt --patch PATCH.diff \
  --changed-files "$CHANGED_FILES" --churn "$((ADDITIONS + DELETIONS))"
```

`$CHANGED_FILES`, `$ADDITIONS`, `$DELETIONS` come from the §2 `gh pr view`
payload. `scripts/` sits next to this skill's `SKILL.md`. Print `high` or
`low`. Write that value to STATE `risk`. High does not raise caps. It only
enables [critic.md](critic.md).

Do not guess risk. Do not skip the script.

## 4.2 Carry-forward — light pass only, after Phase 1

Every entry in the prior marker's `open=` list must be resolved before this run
can publish. Reads here are **outside** the light file cap, bounded by the
10-entry list. Each re-read path is a `--allow-path` for bind-findings.py.

| Entry | Action |
|---|---|
| its file appears in the incremental diff | re-verify against the new code |
| its file is untouched | `Read` that file at the head SHA and re-verify |
| still reproduces | re-publish it, same severity, suffixed `carried from <sha7>` |
| no longer reproduces | drop it in silence |
| its file was deleted, or the code it pointed at is gone | drop it in silence |

An author reply, a comment, or a pushed commit is **not** evidence that a carried
finding was fixed. Only the code at the head SHA is. A run that cannot re-verify
an entry (file unreadable, cap exhausted) treats it as unresolved and keeps it.

A reply that disputes the finding is different from a reply that claims a fix.
When the author says why it is not a bug ("the caller already filters nulls",
"intentional, see the spec"), test that reason as the finding's `refutation`
against the head SHA. It holds → drop the entry and resolve my thread. It does
not hold → carry the entry and answer the reason in one sentence with the
`path:line` that disproves it. Never carry an entry without engaging the reason.

## 4.3 Product-file Read — after Phase 1

**Deep** — `Read` each changed file in full, highest churn first, up to the cap.

**Light** — do not Read whole files except §4.2 and up to 4 files to confirm a
suspicion.
