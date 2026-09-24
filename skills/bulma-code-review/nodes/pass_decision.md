# 2. State → pass decision

```bash
gh pr view "$PR" --repo "$REPO" --json number,title,body,state,isDraft,mergeStateStatus,headRefOid,baseRefName,headRefName,statusCheckRollup,additions,deletions,changedFiles

gh api "repos/$REPO/pulls/$PR/reviews" --paginate \
  --jq "[.[] | select(.user.login==\"$ME\") | {kind:\"review\", state, commit_id, at:.submitted_at, body}]"

gh api "repos/$REPO/issues/$PR/comments" --paginate \
  --jq "[.[] | select(.user.login==\"$ME\" and (.body|test(\"bulma-review:\"))) | {kind:\"comment\", state:\"DEFERRED\", at:.created_at, body}]"
```

Take the artifact with the latest timestamp. Parse its marker:

```
<!-- bulma-review: v=1 pass=deep|light|none sha=<sha> blockers=<n> majors=<n> reason=<slug>
     open=<path>:<line>:<slug>|<path>:<line>:<slug> risk=low|high critic=skip|ran -->
```

`pass=none` means the run stopped at a §3 gate and **read no code**. Any decision
below that leads to APPROVE must check for a `pass=deep|light` marker first.

`open=` lists every **blocker and major** published by that run, max 10, `-` when
none. Nits never enter the ledger — they are said once and never carried. It is the
carry-forward ledger (§4.2): a light pass must re-verify each entry, because the
incremental diff alone cannot prove a prior finding was addressed. Slugs are short
kebab-case labels of the finding title.

A review without a marker (older tooling, manual review) still counts: use its
`commit_id` as `sha` and its `state` as the verdict.

| Last artifact | Decision |
|---|---|
| none | **deep** |
| `sha == headRefOid`, state APPROVED or CHANGES_REQUESTED | **skip** — post nothing, report in chat |
| `sha == headRefOid`, DEFERRED `pass=deep\|light`, `reason=ci*`, CI now green, `blockers=0 majors=0` | **promote** — §8.1, no diff re-read |
| `sha == headRefOid`, DEFERRED `pass=none` `reason=ci_pending`, CI still pending | **wait_ci** — [LOOP.md](../LOOP.md). No new comment. |
| `sha == headRefOid`, DEFERRED `pass=none` (gate), the gated condition is gone | **deep** — nothing was reviewed yet |
| `sha == headRefOid`, DEFERRED, the gated condition still holds (not `ci_pending`) | **skip** — report the same reason in chat, post nothing |
| `sha == headRefOid`, DEFERRED with `reason=uncertainty` | **skip** — needs a human answer or a new commit |
| `sha != headRefOid`, prior marker `pass=none` | **deep** on the full diff — no prior pass to be incremental against |
| `sha != headRefOid`, prior marker `pass=deep\|light` | **light** on `sha..headRefOid` |

A second DEFER for a reason already posted on the same SHA is a duplicate artifact:
skip and report in chat instead. `ci_pending` is never posted; that path is wait_ci.

Skip output is chat-only: state the reason and the SHA. Do not touch the PR.
