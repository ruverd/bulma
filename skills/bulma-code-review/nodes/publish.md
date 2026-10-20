# 9. Publish — one artifact, fixed template

Run [PREFLIGHT.md](../references/PREFLIGHT.md) immediately before POST, including
promotion and any retry. A changed head returns to review; refresh room and
CI evidence too. Use the same checked SHA in `commit_id`, STATE and the marker.
Never approve while body or inline comments raise a Critical/High.
Pending CI returns to **wait_ci** without POST, even with findings or `--force`.
A retained analysis is never approval authorization; preflight and gate.py still run.

### Review (APPROVE / REQUEST_CHANGES)

One atomic call. Findings with `in_diff: true` become inline comments; every other
finding goes in the body.

Never call the reviews endpoint on its own. The gate and the POST are one
command, so an APPROVE the gate rejects is never sent:

```bash
PAYLOAD=$(mktemp /tmp/bulma-review-XXXX.json)   # session scratchpad if one is set
# {"commit_id","event":"APPROVE|REQUEST_CHANGES|COMMENT","body":"...","comments":[{"path","line","side":"RIGHT","body"}]}
python3 scripts/gate.py --dir "$REVIEW_DIR" --payload "$PAYLOAD" --me "$ME" \
  --head "$HEAD_SHA" --signoff "$REVIEW_DIR/signoff.json" \
  --ledger "$REVIEW_DIR/bound.json" $BOT_LOGINS \
  && gh api "repos/$REPO/pulls/$PR/reviews" -X POST --input "$PAYLOAD"
```

`$BOT_LOGINS` is `--bot-login <login>` for each review bot named in
`bulma-memory` (accounts that run an AI reviewer under a user login). GitHub
`Bot` users and `$ME` always count as bots.

| Gate exit | Next |
|---|---|
| 0 | posted; post-verify below |
| 1 | nothing posted. Each `BLOCKED` line is a reason: DEFER with them under Open, dismiss my standing approval, record STATE `gate=blocked` |
| 3 | nothing posted. Only bot approvals stand on this head. Rewrite the payload as `event: COMMENT`, header `## 💬 Reviewed, no blockers: <repo>#<pr>`, first line "Another bot already approved this head, so this needs a human approval, not a second bot one.", marker `reason=bot_quorum`; re-run the gate and POST |

REQUEST_CHANGES and COMMENT payloads pass through the gate too; it checks
their template rows, marker and `commit_id`.

`422` means an invalid position and kills the whole review atomically. Retry
**once** with `comments: []` and all findings in the body, then record
`inline_failed` in the chat summary. No further retries.
Re-run preflight and the gate before that retry and preserve severity/verdict. Do not retry
an ambiguous network failure until checking whether the review was created.

### Body template — identical for all verdicts, only the header changes

Section order is fixed. The words inside are Voice, not labels pasted as the comment.

Every APPROVE and REQUEST_CHANGES body must include the `Model` row below,
filled from this pass's `reviewer_model`. Keep it in DEFER bodies, dry-run
payloads, and the `422` retry too. It identifies the reviewer responsible for
the verdict, not the orchestrator or critic. Use `unknown` when the host exposes
no identity; never omit the row or invent a model name or version. Escape any
Markdown table delimiters or line breaks in the value before rendering it.

```markdown
## ❌ Changes requested: <repo>#<pr>

The seat picker has an unchecked seat cap and a retry-state defect.

| | |
|---|---|
| Model | <reviewer_model> |
| Reviewed head | <full reviewed_sha> |
| Pass | deep, 1st review |
| CI | green on <sha>, <run links>; or CI did not run |
| Review context | clear, or linked open concerns |
| Human sign-off | not required, or needs human sign-off: <paths> |
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

<!-- bulma-review: v=1 pass=deep sha=<full reviewed_sha> blockers=1 majors=2 reason=-
     open=src/x.ts:42:unreset-retry-count|src/y.ts:10:missing-empty-list-test|src/a.ts:42:seat-cap-not-rechecked
     risk=low critic=skip preflight=1 -->
```

The marker is written on **every** artifact, including gate DEFERs (`pass=none`,
`open=-`). Without it the next run loses the ledger and re-reviews from scratch.

Headers: `## ✅ Approved: <repo>#<pr>`, `## ❌ Changes requested: <repo>#<pr>`,
`## ⏸️ Deferred: <repo>#<pr>`, `## 💬 Reviewed, no blockers: <repo>#<pr>` (bot
quorum). The table rows `Model`, `Reviewed head`, `CI`, `Review context`,
`Human sign-off` and `Coverage` are required on every review body, compact or
not; `gate.py` rejects a body without them. Findings in the bind `body` bucket
name both where the break surfaces and the changed hunk that causes it. Sections with no content are omitted. Omit
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

Same template. Before posting, dismiss my standing approval on this PR
([PREFLIGHT.md](../references/PREFLIGHT.md) §Retire my stale approval); the
DEFER comment alone does not withdraw it. The marker carries the reason
(`reason=coverage`, `reason=critic_failed`, ...) so the next pass knows a flip
to APPROVE needs a deep pass. The line under the header is a sentence, not a status code:
"CI is still red on lint and typecheck, so I did not read the diff."
Under `### ❓ Open`, name the reason: failing checks with log links (max 8),
the draft or conflict, the files you could not cover, or the open question.
Never call `gh pr review` on a DEFER.

### Post-verify

```bash
gh api "repos/$REPO/pulls/$PR/reviews/$REVIEW_ID" --jq '{user: .user.login, state, commit_id}'
gh pr view "$PR" --repo "$REPO" --json headRefOid --jq .headRefOid
```

`REVIEW_ID` comes from the POST response, never from the last review in a list.
Compare `commit_id` and the live head with `reviewed_sha`. A concurrent push
makes this review stale; dismiss it, report it and require review of the new head.

DEFER: print the comment URL instead. `--dry-run`: print the payload, post nothing,
and label the chat summary `DRY-RUN`.
