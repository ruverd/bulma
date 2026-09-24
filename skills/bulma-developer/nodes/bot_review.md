# Node: bot_review

**Verb:** wait / route
**Capability:** read gh, `schedule_wake`, bus `LSTM_REQUEST`. No product patch.

Between **mergeable** (CI green and MERGEABLE) and **request_qa**.
Do not open QA from here.

## Detect

Run [PRODUCT.md](../../bulma-feature-delivery/PRODUCT.md) §9, or read
`review_bot` from STATE if already set. Write the field on developer STATE.

No bot → **request_qa**. Do not wait.

## Review on head SHA

Need a review from a detected bot login on the **current** head SHA
(`commit_id` equals `headRefOid`).

```bash
gh api "repos/$REPO/pulls/$PR/reviews" --paginate
gh pr view "$PR" --repo "$REPO" --json headRefOid,mergeable,state,url
```

CI not green or not MERGEABLE → **mergeable**.
PR CLOSED or MERGED → `cancel_wake`, stop.

No review on this SHA yet → **wait**.

## Wait

Same 5m `schedule_wake` as
[LOOP.md](../../bulma-code-review/LOOP.md) and
[bulma-goal LOOP.md](../../bulma-goal/references/LOOP.md).
[bulma-host](../../bulma-host/SKILL.md). Do not `gh pr checks --watch`.

If STATE already has `loop_id`, do not create a second loop.

```
schedule_wake
  interval: "5m"
  fire_immediately: false
  prompt: <exact text below>
```

Store the host wake id in `.bulma-developer/STATE.md` as `loop_id`.

### Prompt (paste verbatim, fill PR/repo)

```text
Continue bulma-developer bot_review. load_skill bulma-developer.

PR: <url>
Repo: <owner/repo>
State: $BULMA_ROOT/.bulma-developer/STATE.md

Re-enter nodes/bot_review.md on the live head SHA.
If required CI is not green or the PR is not MERGEABLE, go to mergeable.
If no bot review exists on this SHA, do nothing else and end the turn.
If a bot review exists, follow bot_review (threads / score / skip).
If the PR is CLOSED or MERGED, cancel_wake and stop.
Do not request QA until bot_review skip or pass.
Do not merge. Chat: `bulma-memory`. Unslop always, one short S/D/P block.
```

Interval **5m**. Min 60s.

## Threads

Unresolved bot threads (GraphQL `reviewThreads`, `isResolved=false`,
author is a detected bot) → bus `LSTM_REQUEST`
([PROTOCOL.md](../../bulma-bus/PROTOCOL.md)).
`from: developer`, `to: lstm`, `pr_url` required. Body: thread URLs
and comment ids. Do not spawn `bulma_lstm`. Do not patch here.
`bulma-lstm` already patches with TDD.

`cancel_wake` before the switch. On `LSTM_RESULT`, re-enter this node
on the new head SHA and wait for a bot review on that SHA.

A won't-fix reply that resolves the thread counts as resolved
(`isResolved=true`). Do not reopen it.

Thread fetch: [GITHUB.md](../../bulma-lstm/references/GITHUB.md).

## Score

If the bot review body on this SHA exposes `N/5`, pass only when
`N >= review_bot_min_score` (GRAPH default 5). No `N/5` in the body
means the score gate does not apply.

## Exit

Pass → **request_qa** when:

- zero unresolved bot threads, and
- the score gate holds

Then `cancel_wake`.

Score below min and zero unresolved threads: nothing to patch.
**escalate** with the score. Do not wait out the cap.

## Loops

`review_bot_loops: 3`. Each `LSTM_REQUEST` costs one
(`review_bot_loops_used`). Exhaust → **escalate** with the remaining
unresolved thread list and the score if it is below min.

## Output

```text
result: skip / pass / waiting / lstm / escalated
review_bot: <login or empty>
sha: <head>
unresolved: N
score: N/5 or none
loops_used: N
```
