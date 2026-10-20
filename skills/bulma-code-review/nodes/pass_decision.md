# 2. State → pass decision

```bash
gh pr view "$PR" --repo "$REPO" --json number,title,body,state,isDraft,mergeStateStatus,headRefOid,baseRefName,baseRefOid,headRefName,reviewDecision,latestReviews,statusCheckRollup,additions,deletions,changedFiles
```

Run [PREFLIGHT.md](../references/PREFLIGHT.md), then derive our prior artifacts
from its cached reviews/comments. Filter by `$ME` only for this ledger, never
for room evidence. Take our artifact with the latest timestamp. Parse its marker:

```
<!-- bulma-review: v=1 pass=deep|light|none sha=<sha> blockers=<n> majors=<n> reason=<slug>
     open=<path>:<line>:<slug>|<path>:<line>:<slug> risk=low|high critic=skip|ran|failed preflight=1 -->
```

`reason=` carries the DEFER reason (`coverage`, `uncertainty`, `critic_failed`,
`ci_red`, ...) on every DEFER, and `bot_quorum` on a COMMENT review.

`pass=none` means the run stopped at a §3 gate and **read no code**. Any decision
below that leads to APPROVE must check for a `pass=deep|light` marker first.

`open=` lists every **blocker and major** published by that run, max 10, `-` when
none. Nits never enter the ledger — they are said once and never carried. It is the
carry-forward ledger (§4.2): a light pass must re-verify each entry, because the
incremental diff alone cannot prove a prior finding was addressed. Slugs are short
kebab-case labels of the finding title.

A review without a marker (older tooling, manual review) still counts: use its
`commit_id` as `sha` and its `state` as the verdict.
Missing `preflight=1` or retained one-hop evidence cannot qualify for skip or
promotion. Run a fresh deep pass under the new rules, preserving prior findings.
`preflight=1` identifies this protocol; it does not mean the gates passed.

| Last artifact | Decision |
|---|---|
| none | **deep** |
| `sha == headRefOid`, state APPROVED or CHANGES_REQUESTED | **skip** — post nothing, report in chat |
| `sha == headRefOid`, DEFERRED `pass=deep\|light`, `reason=ci*`, CI now green, `blockers=0 majors=0` | **promote** — §8.1, no diff re-read |
| `sha == headRefOid`, DEFERRED `pass=none` `reason=ci_pending`, CI still pending | **wait_ci** — [LOOP.md](../LOOP.md). No new comment. |
| `sha == headRefOid`, DEFERRED `pass=none` (gate), the gated condition is gone | **deep** — nothing was reviewed yet |
| `sha == headRefOid`, DEFERRED, the gated condition still holds (not `ci_pending`) | **skip** — report the same reason in chat, post nothing |
| `sha == headRefOid`, DEFERRED with `reason=uncertainty` | **skip** — needs a human answer or a new commit |
| `sha == headRefOid`, COMMENTED `reason=bot_quorum`, approvals on the head unchanged | **skip** |
| `sha != headRefOid`, prior marker `pass=none` | **deep** on the full diff — no prior pass to be incremental against |
| any `sha`, my latest decisive artifact is REQUEST_CHANGES, or a DEFER with `reason=coverage\|uncertainty\|critic_failed`, with no deep pass of mine after it | **deep** on the full PR diff, carry-forward still applies |
| `sha != headRefOid`, prior marker `pass=deep\|light` | **light** on `sha..headRefOid` |

A second DEFER for a reason already posted on the same SHA is a duplicate artifact:
skip and report in chat instead. `ci_pending` is never posted; that path is wait_ci.

A light pass only reads the delta, so it can only keep an approval-shaped
verdict that was already APPROVE. Whatever the earlier deep pass missed is
never looked at again unless the flip back to APPROVE reruns Phases 5–6 on the
full diff. `gate.py` enforces this from the markers.

If my approval stands on an older SHA, dismiss it now, before review
([PREFLIGHT.md](../references/PREFLIGHT.md) §Retire my stale approval). It no
longer describes the head.

Skip output is chat-only: state the reason and the SHA. Do not touch the PR.
If fresh room evidence blocks a previous approval, do not silently skip: DEFER
with the concern URLs. Reevaluate `review_context`, `review_context_unknown`,
`human_signoff`, and `head_changed` deferrals on every run. Promotion always
re-runs the full preflight, including sensitive paths and CI evidence.

## Retained analysis from pending CI

Before selecting a new pass, refresh preflight and `CONTEXT.json` in `review_dir`.
This context contains the current tracker acceptance criteria and content hashes
of every repository rule file used by the review. Refresh those sources, not a
copy of the old context. Missing tracker/rule evidence invalidates reuse.
Run `scripts/snapshot.py check --dir "$REVIEW_DIR" --context "$REVIEW_DIR/CONTEXT.json"`.
Success reuses only completed code analysis, including carried findings and
coverage. Resume at verdict with live CI and room evidence. If prior own
REQUEST_CHANGES or coverage/uncertainty/critic_failed requires deep, the retained
pass must be deep too. A changed head, base, PR text, context, policy or artifact
invalidates the cache. Apply the normal deep/light rules above. Never turn an
unfinished review into a completed analysis just to save work.
