# Node: shipper

**Verb:** package
**Capability:** git commit + push + draft PR; **never** merge
**Does not** mark final delivery alone — **ci_watch** closes done.

## Mission

After quality ok: commit → push → draft PR.
Then the orchestrator runs **ci_watch** if a PR/MR exists.

## Sequence

1. Pre-checks: review pass, tester pass, quality fix-all + hard_gate_after pass —
   confirm exit codes in `.bulma-feature-delivery/gates.log` if it exists.
2. `git branch --show-current` must not be `main` or `master`. Fail the node if it is.
   Branch == tracker branch if set.
3. Forge from [PRODUCT.md](../PRODUCT.md). `github` → `gh`. `gitlab` → `glab`. `git` → push only, no PR (`done_local` unless the user insisted).
4. Idempotency: list PRs/MRs on this head. Exists → update, do not recreate.
5. Commit (cite ticket id if any). **No Co-Authored-By, no "Generated with", no trailers.**
6. `git fetch origin && git rebase origin/<base>`. Re-run the hard gate.
   Then push (`-u`). `--force-with-lease` only after a rebase that rewrote
   commits, and only on the task branch. Never `--force`. Never on main/master.
7. Draft PR/MR with the ticket link. Body from
   [../templates/PR_BODY.md](../templates/PR_BODY.md). Inline the
   evidence fragment (`$BULMA_ROOT/.bulma-feature-delivery/pr-body-evidence.md`).
   **UI + `forge=github`:** load
   [before-and-after](../../before-and-after/SKILL.md). Attach the
   evidence PNGs with `format.sh` + `gh pr edit --attach`. Do not gist.
   If the fragment has no PNGs yet, capture merge-base vs HEAD here.
   Capture failure does not block the PR. A repo `pr-description`
   skill may fill leftover fields. It is not the body.
8. **Reviewers + assignee** per PRODUCT.md §6 (re-read at PR open).
   ```bash
   ME=$(gh api user --jq .login)   # or glab equivalent
   gh pr create --draft --title "..." --body "..." \
     --assignee "${ASSIGNEE:-$ME}"
   # only if reviewers_status=confirmed:
   # gh pr edit "$PR" --add-reviewer "$LOGIN"   # one login per call
   ```
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
| PR + CI green | **`done`** (delivered) |
| PR + CI pending/red | `shipping` / `ci_watching` — **not** delivered |
| `--no-pr` + quality ok | `done_local` or done with note "no PR CI" |

## Hard rules

- Never merge. Never `--force`. `--force-with-lease` only on the task branch after a rebase that rewrote commits.
- Never "delivered" with failing checks.
- Fullstack: ship per repo + ci_watch on **each** PR.
- Every PR (create or update): reviewers/assignee per PRODUCT.md.
