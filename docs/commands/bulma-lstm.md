# `/bulma-lstm`

Alias: **`/lstm`**. The name is short for "looks shit to me", a joke on
LGTM. Graph engineer on the **author** side of a review: use it when a
reviewer left comments on your pull request.

Ingest a PR / review / comment URL. Patch should-fix on the **same
branch**. Rebase conflicts. 👍 + unslopped reply on every comment,
resolve fixed threads, dismiss fully addressed change requests with proof, and
request re-review after code changes unless the reviewer or PR is approved.
On Codex, invoke `$bulma-lstm` or select it through `/skills`.

Human sign-off or visual-proof requests trigger `bulma-qa` through the bus,
even without a code fix. QA walks every requested behavior, attaches UI clips
and stills or endpoint HTTP stills, and maps evidence to each request. It can
prepare isolated local database fixtures and QA auth users, including identity-provider
roles, grants and claims when needed. Setup is reversible and preserves the
authorization checks being tested. Missing proof keeps sign-off pending.
Automated QA supplies evidence; the human still decides approval.

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
  → group verified comments by root cause → patch groups (TDD)
  → prove (spec + quality + tester)
  → bulma-qa when human sign-off or visual proof was requested
  → 👍 + unslopped reply on every comment
  → COMMENT summary → resolve fixed threads → dismiss proved change requests
  → re-request after changes if not approved
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
   post a summary, resolve fixed threads and dismiss fully addressed
   `CHANGES_REQUESTED` with proof. Re-request only after code changes when the
   reviewer and PR are not approved. Pending requests are not repeated.

The graph engineer does not type the patch. The coder worker does.

Uses bundled `receiving-code-review` and `unslop` (`skills/receiving-code-review/`, `skills/unslop/`).

## Never

- New PR.
- Merge.
- Spawn `/bulma-developer` or `/bulma-reviewer`.
- Skip rebase when the branch is conflicting.
- Leave a comment without 👍 + reply.
- POST a GitHub reply that skipped `unslop`.
- Dismiss an approval or unresolved feedback.
- Re-request an approved reviewer or send requests without code changes.
- Reply on a should-fix run before **prove** passed.

## Related

[`/bulma-reviewer`](bulma-reviewer.md) · [`/bulma-developer`](bulma-developer.md)
