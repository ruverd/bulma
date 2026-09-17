# Node: reply

**Verb:** ack

Commands: [GITHUB.md](../references/GITHUB.md). This node is the
progress trail on the PR. Chat does not count.

For **every** in-scope inline comment (fix **and** skip):

1. 👍 on the comment.
2. Load `unslop`, rewrite the reply, POST it on the thread.
3. 👍 on the parent review body.

Body-only review: 👍 on the review, then an unslopped COMMENT review
after it.

Enter this node only from GRAPH (**prove** pass, or verify skip-only).
Do not dismiss a should-fix run that never passed **prove**.

Then:

4. Resolve the conversation when a fix landed. Skip stays open after
   the skip reply unless that reply is enough to close it.
5. Dismiss `CHANGES_REQUESTED` on those reviews.
6. Re-request that reviewer when a fix landed.

Done only when every in-scope comment has 👍 + reply, every processed
`CHANGES_REQUESTED` review is dismissed (or 403 noted), comment ids
are in `processed_comment_ids`, and review ids are in
`processed_review_ids`.

A later re-review (new ids) needs its own pair. Do not repeat 👍/reply
on an id already in those lists.
