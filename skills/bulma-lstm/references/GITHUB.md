# GitHub (LSTM)

One home for fetch / 👍 / reply / unslop / resolve / re-request.

## Fetch

```bash
gh pr view "$PR" --repo "$REPO" --json number,url,isDraft,state,mergeable,mergeStateStatus,headRefOid,baseRefName,headRefName,reviewDecision,statusCheckRollup

gh api "repos/$REPO/pulls/$PR/reviews" --paginate
gh api "repos/$REPO/pulls/$PR/comments" --paginate
gh api "repos/$REPO/issues/$PR/comments" --paginate
```

URL fragments: `#pullrequestreview-<id>` · `#discussion_r<id>` ·
`#issuecomment-<id>`.

## Per comment (hard)

Every inline comment this run analyzes gets **both**, including skip:

1. 👍 on the comment
2. A thread reply on that comment

The parent review body gets 👍. Body-only review (no inline): 👍 on
the review plus a top-level COMMENT review **after** that review.
Nested reply on `pullrequestreview-*` 404s.

Never put 👍 in the reply text. Chat is not a substitute.
The reply node is not done while any in-scope comment lacks 👍 or a
reply.

## Unslop then POST

Load bundled `unslop`. Rewrite the body. Then POST. Never POST the
first draft. English. Same rule for skip reasons, COMMENT reviews,
and re-review requests.

## Reactions

```bash
gh api -X POST "repos/$REPO/pulls/comments/$COMMENT_ID/reactions" \
  -f content='+1'

gh api -X POST "repos/$REPO/pulls/$PR/reviews/$REVIEW_ID/reactions" \
  -f content='+1'
```

## Reply

Inline thread:

```bash
gh api "repos/$REPO/pulls/$PR/comments/$COMMENT_ID/replies" \
  -f body="$BODY"
```

Body-only COMMENT review:

```bash
gh api "repos/$REPO/pulls/$PR/reviews" \
  -f event='COMMENT' \
  -f body="$BODY"
```

## Resolve thread (fix landed)

Need the GraphQL thread id:

```bash
gh api graphql -f query='
query($o:String!,$n:String!,$p:Int!) {
  repository(owner:$o, name:$n) {
    pullRequest(number:$p) {
      reviewThreads(first: 100) {
        nodes { id isResolved
          comments(first: 20) { nodes { databaseId } } }
      }
    }
  }
}' -F o=OWNER -F n=REPO -F p=$PR
```

```bash
gh api graphql -f query='
mutation($id:ID!) {
  resolveReviewThread(input: {threadId: $id}) {
    thread { isResolved }
  }
}' -F id="$THREAD_ID"
```

## Plan the remaining review actions

Build `review-actions.json` under the LSTM state directory from fresh fully
paginated reviews, the live head, requested reviewers and prove output:

```json
{
  "pr_state": "OPEN",
  "head": "full head SHA",
  "proof_sha": "same full head SHA",
  "proof_pass": true,
  "code_changed": true,
  "review_decision": "CHANGES_REQUESTED",
  "original_reviewers": ["reviewer-login"],
  "requested_reviewers": [],
  "addressed_review_ids": [123],
  "reviews": []
}
```

`reviews` is the flattened REST list, including id, state, user.login and
submitted_at. `code_changed` compares the run's starting code/tree with its
pushed final tree, not merely two commit SHAs. `addressed_review_ids` includes
only reviews whose complete body and inline findings have final proof. A scoped
comment URL does not establish that its parent review is fully addressed.

```bash
python3 scripts/review-actions.py "$BULMA_ROOT/.bulma-lstm/review-actions.json"
```

This prints a plan, not an authorization to use stale evidence. Re-fetch HEAD
and each target review before a mutation; head drift returns to verify/prove.
Permission denial stays pending. Never change branch protection to make it work.

## Dismiss a fully addressed change request

After replies, summary and resolved fixed conversations, dismiss each planned
active CHANGES_REQUESTED review with a message citing fix SHA and proof:

```bash
gh api -X PUT "repos/$REPO/pulls/$PR/reviews/$REVIEW_ID/dismissals"   -f message="$DISMISS_REASON"
```

Store confirmed DISMISSED review IDs. Never dismiss APPROVED reviews or unresolved
feedback. A dismissal is administrative cleanup, not the original reviewer's
approval. The review engine still requires that reviewer to clear their concern.

## Re-request after changes, unless approved

Refresh reviews and `reviewDecision` after dismissal. Recompute the action plan.
Only request when code changed, prove passed, neither the original reviewer's
latest decisive state nor overall reviewDecision is APPROVED, and no request is
already pending. On resume also check the reviewer+SHA request ledger.

```bash
gh api -X POST "repos/$REPO/pulls/$PR/requested_reviewers"   -f "reviewers[]=$LOGIN"
```

Record failures and leave them pending; do not repeatedly notify or claim success.
Do not send a new request for a skip-only run or for an approved reviewer.

## Summary idempotency

Use `<!-- bulma-lstm: sha=<full SHA> comments=<hash of sorted analyzed IDs> -->`
in the COMMENT summary. Search existing review bodies and issue comments before
POST on resume or uncertain network failure. Reuse the existing summary URL.
Do not use this marker to skip missing per-comment replies or resolutions.
