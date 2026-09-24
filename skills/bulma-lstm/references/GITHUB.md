# GitHub (LSTM)

One home for fetch / 👍 / reply / unslop / resolve / dismiss / re-request.

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
and dismiss messages.

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

## Dismiss CHANGES_REQUESTED

After 👍 + reply (and resolve if a fix landed), dismiss that review
so required-review is not left `CHANGES_REQUESTED`.

```bash
gh api -X PUT "repos/$REPO/pulls/$PR/reviews/$REVIEW_ID/dismissals" \
  -f message="$MSG" \
  -f event='DISMISS'
```

`$MSG` is unslopped and short. Example: `Addressed in the latest commits.`
Only `CHANGES_REQUESTED`. `COMMENTED` cannot be dismissed. 403: note
in the report. Do not fake success.

## Re-request (fix landed)

After dismiss.

```bash
gh api -X POST "repos/$REPO/pulls/$PR/requested_reviewers" \
  -f "reviewers[]=$LOGIN"
```
