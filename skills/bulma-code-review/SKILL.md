---
name: bulma-code-review
category: engine
description: >
  Adaptive PR review via gh: one PR on the main thread, one fresh subagent per
  extra PR, one verdict artifact each (REQUEST_CHANGES / APPROVE / DEFER). Use
  when /bulma-code-review with PR URLs, numbers, or the current branch.
---

# Bulma Code Review

Sequential phases per PR. Depth adapts to review history.
**Multi-PR:** one subagent per PR (see §0).
**CI fork:** [GRAPH.md](GRAPH.md) · [LOOP.md](LOOP.md). Pending required CI
allows pinned code review, then waits with retained analysis and does **not** post. Red CI still DEFERS.

## Invariants — never break

1. **Subagents.** Multi-PR: one fresh subagent per PR; the orchestrator must
   **not** review diffs itself. Single-PR: at most one **high-risk critic**
   ([nodes/critic.md](nodes/critic.md)). That spawn is not a second GitHub
   artifact and does not fan out.
2. **Exactly one artifact per PR** — one review (inline comments in the same
   call) or one issue comment. Never both. Never two of either **on the same PR**.
   Dismissing my own stale approval and resolving my own fixed threads are
   state changes, not artifacts.
3. **Never APPROVE** while any required check is failed, pending or unknown.
   `out_of_scope` is not unknown: the repo's own workflows never build or test
   PRs into this base ([PREFLIGHT.md](references/PREFLIGHT.md) §CI out of scope).
4. **Never invent a finding.** A finding with no concrete trigger is dropped in
   silence — not downgraded, not mentioned.
5. **Nits never block, and most stay silent.** A nit reaches the PR only inside the
   collapsed Nits block (§9), only with a concrete `path:line`, max 5 per run, and
   never changes the verdict. Always silent regardless: praise, generic refactor
   advice, speculative perf, pre-existing debt the diff neither changed nor broke.
   A break this diff causes in an unchanged file (a caller, a test) is not
   pre-existing; it is a finding with `cause_path`/`cause_line` (§5 Phase 10).
   "Could be cleaner" is silent except the one code-judo nit in Phase 8, which must
   name a layer, branch, or helper to delete.
6. **Voice.** GitHub text and chat follow **Voice** (just above §9). Teammate
   English on the PR. Chat: `bulma-memory`. Never caveman. Never a form.
7. **Fixed output template** (§9). Section order never changes; empty sections vanish.
   Every verdict body includes the executing reviewer's model in the `Model`
   row. Resolve identity through `bulma-host`; use `unknown` if unavailable.
8. **Phases run in order.** Do not start a phase before the previous one is done.
9. **Read the room before approving.** Follow [PREFLIGHT.md](references/PREFLIGHT.md)
   before pass selection and again before publishing. Open change requests,
   unresolved threads, unanswered questions and AI QA `FAIL` block approval.
   A thread whose author approved this head does not. QA `FAIL` needs human
   approval. QA `BLOCKED` (could not run) never gates.
   Never dismiss another reviewer's review; ask its reviewer to re-review.
   Missing evidence fails closed. `--force` cannot bypass these approval gates.
10. **My own open findings never expire silently.** A prior finding of mine is
    dropped only after it is re-verified against the head SHA (§4.2).
11. **Patch bind.** After Phase 10, every finding goes through
    `scripts/bind-findings.py`. A `path:line` that is not in this pass's patch
    (or a carry-forward allow-path) cannot be inline. A defect this diff
    causes elsewhere carries `cause_path`/`cause_line` and lands in the
    script's `body` bucket. Exit 3 means a blocker or major sits outside the
    inline set: it still blocks APPROVE. Binding failure is not evidence that a
    High disappeared. A finding with no `axis` must be completed before
    publishing.
12. **High-risk critic.** When `scripts/classify-risk.py` prints `high`, spawn
    the critic before verdict. The critic walks contracts, integration/state,
    and security/data-loss on one spawn, without voting findings off. When
    the script prints `low`, skip the spawn. High risk with no completed
    critic is **DEFER** `reason=critic_failed`, marker `critic=failed`.
13. **Approve the reviewed head only.** Pin the full reviewed SHA, re-review
    any new commits, and verify CI execution on that SHA. Skipped or missing
    build/test jobs are not green, unless `ci-scope.py` proves the base is out
    of scope. Recheck before promotion and retry too.
14. **Own Critical/High means no approval.** Reconcile body, inline comments,
    carried findings and critic output with the verdict before POST.
15. **Sensitive paths are named, not deferred.** Workflows, Terraform, auth,
    billing/seats and secrets go in the Human sign-off row when
    `classify-risk.py --human-signoff` lists them. That list does not DEFER
    and does not block APPROVE. Use the full PR file list, including renames,
    even during light review.
16. **Preserve the checkout.** Review through pinned source reads. Never edit,
    stage, switch, stash, reset, clean, rebase or move existing branches in the
    user's checkout. Fetch commits and run checks in an isolated review
    checkout. Inspect changed scripts and configuration before executing them.
    Follow [EVIDENCE.md](references/EVIDENCE.md) for test and rollout proof.
17. **The gate script decides, not memory.** Every review POST runs as
    `scripts/gate.py ... && gh api .../reviews` ([nodes/publish.md](nodes/publish.md)).
    Exit 1 → DEFER with its reasons. Exit 3 → the same body as a `COMMENT`
    review: another bot already approved this head, and two bot approvals must
    not satisfy a two-approval rule. Never post an APPROVE the gate did not pass.
18. **My approval never outlives its evidence.** When the head moves past my
    approval, or I DEFER, request changes or see a new concern on a PR I
    approved, dismiss my own approval first ([PREFLIGHT.md](references/PREFLIGHT.md)
    §Retire my stale approval). Branch protection may not do it.
19. **A flip needs a full look.** APPROVE after my own REQUEST_CHANGES, or
    after my DEFER for `coverage`, `uncertainty` or `critic_failed`, needs a
    **deep** pass on the full PR diff. A delta-only light pass or an empty
    commit cannot clear it.
20. **Converge, do not loop.** One finding per defect class, with its other
    `instances`. A published finding is carried, never re-posted as new. A
    rebase that keeps the same change re-verifies the ledger only. From my
    third REQUEST_CHANGES on a PR, new majors in lines unchanged since my first
    pass do not block, and the body asks the author to rethink the area
    ([nodes/pass_decision.md](nodes/pass_decision.md) §Convergence). Proven
    blockers always block.
21. **Project knowledge stays in the project.** Repo rules come from the
    repo's own files, including `REVIEW.md`. Domain facts come from the
    `## Gotchas` section of project memory ([bulma-memory](../bulma-memory/SKILL.md)).
    This skill carries no product, company or vendor knowledge.

## Caps

| Budget | Deep | Light |
|---|---|---|
| Full files read | 15 (highest churn first) | 4 (only to confirm a suspicion) + carry-forward re-reads (§4.2, ≤10, outside the cap) |
| Codegraph / caller queries | 8 | 3 |
| Findings published | 10 (blockers first) | 10 |
| Nits published | 5, collapsed block, never inline | 5 |
| Neighbour test files | inspect changed exports' tests and API contract mocks, within existing file/query caps | same |
| Critic (risk=high only) | 1 spawn, 4 Reads, 2 new blockers | same |

Large PR (`additions + deletions > 2500` or `changedFiles > 25`): keep the caps,
review hotspots first (auth, permissions, data writes, migrations, public API,
money, PII), and declare uncovered files in the Coverage block.

---

## Where the rest lives

SKILL.md carries the invariants and the caps. Each step is its own file so a
pass loads only what it needs.

| Step | File |
|---|---|
| 0. Multi-PR fan-out (orchestrator only) | [nodes/fanout.md](nodes/fanout.md) |
| 1. Resolve the PR | [nodes/resolve.md](nodes/resolve.md) |
| 2. State to pass decision (deep or light) | [nodes/pass_decision.md](nodes/pass_decision.md) |
| 3. Gates, before reading any diff | [nodes/gates.md](nodes/gates.md) |
| 4. Patches, risk, then Reads after spec | [nodes/fetch.md](nodes/fetch.md) |
| 5. Spec checklist, then axes, then bind | [nodes/review.md](nodes/review.md) |
| 6. High-risk critic (no-op when low) | [nodes/critic.md](nodes/critic.md) |
| 7-8. Severity, coverage, verdict | [nodes/verdict.md](nodes/verdict.md) |
| 9. Publish, one artifact per PR | [nodes/publish.md](nodes/publish.md) |
| CI wait | [nodes/wait_ci.md](nodes/wait_ci.md) · [LOOP.md](LOOP.md) |

| Reference | File |
|---|---|
| Voice and wording | [references/VOICE.md](references/VOICE.md) |
| Isolated checks, regression and rollout evidence | [references/EVIDENCE.md](references/EVIDENCE.md) |
| Chat summary shape | [references/CHAT.md](references/CHAT.md) |
| Failure modes | [references/FAILURES.md](references/FAILURES.md) |
| Graph and edges | [GRAPH.md](GRAPH.md) |
| STATE | [STATE.schema.md](STATE.schema.md) · [templates/STATE.md](templates/STATE.md) |

Correctness, Standards, and Self-verify are never skippable. A large diff is
not a reason.

## Loaded by another reviewer

A caller that borrows this engine's phases ([nodes/review.md](nodes/review.md),
[references/EVIDENCE.md](references/EVIDENCE.md), [nodes/verdict.md](nodes/verdict.md))
instead of running the whole skill still owns the approval gates. Hand over,
with those files:

- [references/PREFLIGHT.md](references/PREFLIGHT.md), including §Sensitive changes
- the `classify-risk.py --human-signoff` JSON for the full PR file list and patch
- `scripts/gate.py` and `scripts/bind-findings.py`

The caller runs the gate before its own APPROVE. A nonempty sign-off list means
the caller cannot approve either. A caller that cannot run the gate does not
approve; it posts its findings as a `COMMENT` or DEFERs.
