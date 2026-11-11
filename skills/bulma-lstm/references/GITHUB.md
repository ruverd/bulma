# GitHub (LSTM)

One home for fetch / 👍 / reply / kevin / resolve / re-request.

## Fetch

```bash
gh pr view "$PR" --repo "$REPO" --json number,url,isDraft,state,mergeable,mergeStateStatus,headRefOid,baseRefName,headRefName,reviewDecision,statusCheckRollup

gh api "repos/$REPO/pulls/$PR/reviews" --paginate --slurp
gh api "repos/$REPO/pulls/$PR/comments" --paginate --slurp
gh api "repos/$REPO/issues/$PR/comments" --paginate --slurp
gh api "repos/$REPO/pulls/$PR/requested_reviewers" --jq '.users | map(.login)'
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

## Kevin then POST

Load bundled `kevin`. Rewrite the body. Then POST. Never POST the
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

Flatten the REST pages into one review list, including `id`, `state`, `user.login`
and `submitted_at`. Use REST `id` / GraphQL `databaseId` for the review ID.
Join inline findings via `pull_request_review_id`. For a scoped run, fetch the
whole review body and the paginated review comments at
`repos/$REPO/pulls/$PR/reviews/$REVIEW_ID/comments` before deciding coverage.
Keep issue comments separate unless they document an outstanding request
from that review. PR-level `reviewDecision` is for re-request policy and
reporting. It does not identify which review is eligible for dismissal.

Populate `proof_sha`, `code_changed` and `addressed_review_ids` from the
recorded prove output. Set `proof_pass` true only when spec, quality and
tester all passed at `proof_sha`. Use the live PR for `head`, `pr_state`
and `review_decision`. Keep `original_reviewers` for re-requests and use
`requested_reviewers` for live pending user requests.

Run these commands from the LSTM skill directory or use the installed skill's
absolute script path. Set `ACTION_STATE` to the path of `review-actions.json`.

```bash
python3 scripts/review-actions.py "$ACTION_STATE"
```

## Dismiss a fully addressed change request

After replies, summary and resolved fixed conversations, execute each ID
from the plan's `dismiss` list. Set `DISMISS_REASON` to a message citing the
fix SHA, proof and summary URL.

```bash
python3 scripts/review-actions.py "$ACTION_STATE" --dismiss "$REVIEW_ID" \
  --repo "$REPO" --pr "$PR" --message "$DISMISS_REASON"
```

The command refreshes the paginated reviews and live head before any PUT to
`/dismissals`. It checks the exact ID and `DISMISSED` state in the response and
reads the same review back. Store only confirmed IDs. On resume or ambiguous
failure, read back the exact ID before retrying. Record nonzero exit status
and stderr in pending actions. Return to verify/prove on head drift. Leave
permission denials pending and report them without changing branch protection.
Other reviewers can still keep the PR in `CHANGES_REQUESTED`.

## Re-request after changes, unless approved

Refresh reviews and `reviewDecision` after dismissal. Recompute the action plan.
Only request when code changed, prove passed, neither the original reviewer's
latest decisive state nor overall reviewDecision is APPROVED, and no request is
already pending. Recheck the live PR head before each request. On resume also
check the reviewer+SHA request ledger.

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
