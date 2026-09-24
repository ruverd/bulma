# 9. Publish — one artifact, fixed template

### Review (APPROVE / REQUEST_CHANGES)

One atomic call. Findings with `in_diff: true` become inline comments; every other
finding goes in the body.

```bash
PAYLOAD=$(mktemp /tmp/bulma-review-XXXX.json)   # session scratchpad if one is set
# {"commit_id","event":"APPROVE|REQUEST_CHANGES","body":"...","comments":[{"path","line","side":"RIGHT","body"}]}
gh api "repos/$REPO/pulls/$PR/reviews" -X POST --input "$PAYLOAD"
```

`422` means an invalid position and kills the whole review atomically. Retry
**once** with `comments: []` and all findings in the body, then record
`inline_failed` in the chat summary. No further retries.

### Body template — identical for all verdicts, only the header changes

Section order is fixed. The words inside are Voice, not labels pasted as the comment.

```markdown
## ✅ Approved: <repo>#<pr>

Adds the company seat picker. I did not find a merge blocker.

| | |
|---|---|
| Pass | deep, 1st review |
| CI | green |
| Coverage | 12 of 12 changed files |
| Findings | 1 blocker · 2 majors |
| Acceptance | 1 done · 1 missing |

### 🛑 Blockers
1. `src/x.ts:42`. **Retry keeps the old count.** If the user retries after a failure, `attempts` still has the old number and the cap never fires. Reset it before the new run.

### ⚠️ Majors
1. `src/y.ts:10`. Empty list has no test. Add one that asserts the empty state.
2. `src/a.ts:42`. Seat cap is not checked again before the write. Validate there. _(still open from 9b2f1ac)_

### ❓ Open
- I cannot tell if api-v2 returns 409 on a duplicate submit. If it does not, this path double-writes.

<details><summary>Nits (skip these if you want)</summary>

- `src/y.test.ts:14`. The test name should start with `should`.
</details>

<details><summary>Coverage</summary>

| File | Checked |
|---|---|
| `src/x.ts` | logic, contract, tests |
</details>

<details><summary>Acceptance</summary>

| Criterion | Status |
|---|---|
| User can retry after a failure | done |
| Seat cap is enforced on the write | missing |
</details>

<details><summary>Skipped axes</summary>

- Perf. No render, query or effect change in the diff.
</details>

<!-- bulma-review: v=1 pass=deep sha=abc1234 blockers=1 majors=2 reason=-
     open=src/x.ts:42:unreset-retry-count|src/y.ts:10:missing-empty-list-test|src/a.ts:42:seat-cap-not-rechecked
     risk=low critic=skip -->
```

The marker is written on **every** artifact, including gate DEFERs (`pass=none`,
`open=-`). Without it the next run loses the ledger and re-reviews from scratch.

Headers: `## ✅ Approved: <repo>#<pr>`, `## ❌ Changes requested: <repo>#<pr>`,
`## ⏸️ Deferred: <repo>#<pr>`. Sections with no content are omitted. Omit
Acceptance when `AC.md` is `none`. Inline findings still appear in the body
list so the summary stands alone. Do not print `axis` labels on the PR; the
Acceptance table is the spec report, and a standards finding already quotes
the rule.

### Inline comment — one shape only

Two to four sentences. First line is the severity and the break. Then when it
happens and what to change. No `Trigger:` / `Fix:` labels on the PR.

```markdown
🛑 **Blocker.** `send` gets null.

On first render `user.email` is still undefined, and this calls `send` anyway. Guard before the call.
```

`⚠️ **Major.**` for majors. No praise. No questions. No list of other ways to
fix it.

### DEFER — issue comment, never a review

```bash
BODY=$(mktemp /tmp/bulma-defer-XXXX.md)
gh api "repos/$REPO/issues/$PR/comments" -F body=@"$BODY"
```

Same template. The line under the header is a sentence, not a status code:
"CI is still red on lint and typecheck, so I did not read the diff."
Under `### ❓ Open`, name the reason: failing checks with log links (max 8),
the draft or conflict, the files you could not cover, or the open question.
Never call `gh pr review` on a DEFER.

### Post-verify

```bash
gh api "repos/$REPO/pulls/$PR/reviews" --jq '.[-1] | {user: .user.login, state, commit_id}'
```

DEFER: print the comment URL instead. `--dry-run`: print the payload, post nothing,
and label the chat summary `DRY-RUN`.
