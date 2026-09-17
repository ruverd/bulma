# 4. Fetch — patches first, file bodies later

```bash
gh pr checks "$PR" --repo "$REPO"        # only for the failing/pending check names
```

Do not Read product files until Phase 1 has written `AC.md`.

## 4.0 Patches and file list

Write both under `$RUVER_ROOT/.ruver-code-review/`:

- `PATCH.diff` — the unified diff this pass will bind against
- `FILES.txt` — one changed path per line

**Deep** — full PR diff:

```bash
gh pr diff "$PR" --repo "$REPO"
```

**Light** — incremental diff only:

```bash
gh api "repos/$REPO/compare/$OLD_SHA...$HEAD_SHA" \
  --jq '.files[] | {filename, status, additions, deletions, patch}'
```

Join the compare patches into `PATCH.diff` (same paths as `FILES.txt`).
`404` or missing SHA (force-push, rebase) → fall back to the full `gh pr diff`,
note `stale_base` in the chat summary, and treat the pass as light anyway.

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

## 4.3 Product-file Read — after Phase 1

**Deep** — `Read` each changed file in full, highest churn first, up to the cap.

**Light** — do not Read whole files except §4.2 and up to 4 files to confirm a
suspicion.
