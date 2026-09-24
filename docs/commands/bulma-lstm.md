# `/bulma-lstm`

Alias: **`/lstm`**. The name is short for "looks shit to me", a joke on
LGTM. Graph engineer on the **author** side of a review: use it when a
reviewer left comments on your pull request.

Ingest a PR / review / comment URL. Patch should-fix on the **same
branch**. Rebase conflicts. 👍 + unslopped reply on every comment,
resolve threads, dismiss `CHANGES_REQUESTED`, re-request.

Never opens a new PR. Draft stays draft.

Skill: [`../../skills/bulma-lstm`](../../skills/bulma-lstm).

## When

- `/lstm https://github.com/org/repo/pull/99`
- `/lstm <review or comment URL>`
- `/lstm resume`
- Envelope: `LSTM_REQUEST`
- GitHub `CHANGES_REQUESTED` on a PR you own

## Graph

```
URL | resume | LSTM_REQUEST
  → admit
  → resolve comments
  → rebase if DIRTY / CONFLICTING
  → verify (claim_true + fix_ok_here, bind HEAD)
  → patch should-fix (bulma-fd-coder, TDD)
  → prove (spec + quality + tester)
  → 👍 + unslopped reply on every comment
  → resolve threads + dismiss CHANGES_REQUESTED + re-request
```

## What the main thread does

1. Resolve the PR and the comment ids.
2. Always rebase if GitHub says dirty/conflicting.
3. Verify each thread on HEAD: `claim_true`, `fix_ok_here`, then
   fix / skip / unclear. Skip cites a path or test.
4. Complicated should-fix → grill first. Else `bulma-fd-coder` (TDD).
5. **prove**: fd reviewer (`spec_verdict` = this comment,
   `quality_verdict` = TDD/DS) + tester. Fail → patch, do not dismiss.
6. 👍 + unslopped reply on **every** comment (fix and skip). Then
   resolve, dismiss `CHANGES_REQUESTED`, re-request if a fix landed.

The graph engineer does not type the patch. The coder worker does.

Uses bundled `receiving-code-review` and `unslop` (`skills/receiving-code-review/`, `skills/unslop/`).

## Never

- New PR.
- Merge.
- Spawn `/bulma-developer` or `/bulma-reviewer`.
- Skip rebase when the branch is conflicting.
- Leave a comment without 👍 + reply.
- POST a GitHub reply that skipped `unslop`.
- Leave `CHANGES_REQUESTED` on a processed review.
- Dismiss or reply on a should-fix run before **prove** passed.

## Related

[`/bulma-reviewer`](bulma-reviewer.md) · [`/bulma-developer`](bulma-developer.md)
