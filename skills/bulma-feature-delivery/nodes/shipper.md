# Node: shipper

**Verb:** package
**Capability:** git commit + push + ready PR; **never** merge
**Does not** mark final delivery alone — **ci_watch** closes done.

## Mission

After quality, review, tester and final evidence match the current tree: commit → push → ready-for-review PR.
Then the orchestrator runs **ci_watch** if a PR/MR exists.

## Sequence

1. Pre-checks: review pass, tester pass, quality ok, final evidence current —
   confirm recorded exit codes in the runtime receipts cited in STATE.
   Recheck the selected playbook with `scripts/playbook.py check`. Required
   task proof cannot be waived by an optional-step skip. Investigation never
   enters this node.
2. `git branch --show-current` must not be `main` or `master`. Fail the node if it is.
   Branch == tracker branch if set.
3. Forge from [PRODUCT.md](../PRODUCT.md). `github` → `gh`. `gitlab` → `glab`. `git` → push only, no PR (`done_local` unless the user insisted).
4. Idempotency: look up this exact head and base before publication. Update
   the existing open PR/MR in place and preserve its draft flag. A merged PR
   is a resume receipt, never a reason to push or publish again. A closed
   unmerged PR or a changed base needs reconciliation before publication.
5. Commit (cite ticket id if any). **No Co-Authored-By, no "Generated with", no trailers.**
6. `git fetch origin && git rebase origin/<base>`. If the tree or base changes,
   return to review, tester and final evidence before pushing. Preserve completed
   decisions; revalidate affected contracts against the new base.
   Then push (`-u`). `--force-with-lease` only after a rebase that rewrote
   commits, and only on the task branch. Never `--force`. Never on main/master.
   **Stack member:** use the assigned head, base, and position from STATE.
   Re-read origin and refuse publication if either the saved destination tip
   or the expected source tip drifted. Verify the candidate descends from
   the assigned start SHA. Record the candidate SHA in the worker's STATE
   before pushing so a retry can recover a push without a PR receipt.
   Keep its integrated history and push by
   fast-forward only. For the umbrella, package the validated existing head
   and skip the commit when the tree is clean. A base change goes back to
   combined validation or conflict handling before publish.
7. Ready-for-review PR/MR with the ticket link. Body from
   [../templates/PR_BODY.md](../templates/PR_BODY.md). Inline the
   evidence fragment (`$BULMA_ROOT/.bulma-feature-delivery/pr-body-evidence.md`).
   **UI + `forge=github`:** load
   [before-and-after](../../before-and-after/SKILL.md). Attach the
   evidence PNGs with `format.sh` + `gh pr edit --attach`. Do not gist.
   If the fragment has no PNGs yet, capture merge-base vs HEAD here.
   Capture failure does not block the PR. A repo `pr-description`
   skill may fill leftover fields. It is not the body.
   Keep the repo PR template and append missing **How to test** steps.
   Follow [PR run attribution](../../bulma-host/PR_ATTRIBUTION.md): append
   **Agent run** last only when at least one executing model is known. List
   known implementation/review/critic contributors by role; copy review identity
   from the verdict result for this PR's final tree, never from the shipper.
   Omit unknown or ambiguous identities, empty rows and public reasoning effort.
   If no models are known, omit the whole section. Each stacked child and
   fullstack sibling uses its own evidence. Preserve supported prior contributions
   and read back each saved description after creation or update.
8. **Reviewers + assignee** per PRODUCT.md §6 (re-read at PR open).
   ```bash
   ME=$(gh api user --jq .login)
   python3 <fd-skill>/scripts/delivery_pr.py --repo "$REPO" --head "$HEAD_BRANCH" \
     --base "$BASE_BRANCH" --title "$TITLE" --body-file "$BODY_FILE" \
     --assignee "${ASSIGNEE:-$ME}"
   ```
   For a stack member add `--position "$POSITION"` from STATE. The helper
   applies the same title position on a resumed open PR and verifies the
   result. Update the existing body/evidence using its URL and preserve the
   draft flag. With GitLab, use the same exact source and target checks,
   create with `glab mr create` without a draft flag or Draft title prefix,
   and read back draft status. Use `glab` for assignee and reviewers there.
   Request only `confirmed`. `proposed` / `missing`: still open the
   PR; orchestrator asks once (PRODUCT.md). One failed reviewer
   request must not block the rest. Never pass `git user.name` to
   `--assignee`.
9. STATE: PR/MR URL; `ci.status: pending`; `reviewers` /
   `reviewers_status` from PRODUCT.md §6.
10. **Hand off to ci_watch** when a PR/MR exists.
11. Chat summary (`bulma-memory`): PR open; waiting on CI green.
    If `reviewers_status` is `proposed` or `missing`, ask the one
    PRODUCT.md question in the same turn. Do not wait to start CI.

## Done

| Situation | graph `status` |
|---|---|
| PR + applicable CI gate passed | **`done`** (delivered) |
| PR + CI pending/red | `shipping` / `ci_watching` — **not** delivered |
| `--no-pr` + quality ok | `done_local` or done with note "no PR CI" |

## Hard rules

- Never merge. Never `--force`. `--force-with-lease` only on the task branch after a rebase that rewrote commits.
- Never "delivered" with failing checks.
- Fullstack: ship per repo + ci_watch on **each** PR.
- Every PR (create or update): reviewers/assignee per PRODUCT.md.
