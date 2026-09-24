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
waits 5m and does **not** post. Red CI still DEFERS.

## Invariants — never break

1. **Subagents.** Multi-PR: one fresh subagent per PR; the orchestrator must
   **not** review diffs itself. Single-PR: at most one **high-risk critic**
   ([nodes/critic.md](nodes/critic.md)). That spawn is not a second GitHub
   artifact and does not fan out.
2. **Exactly one artifact per PR** — one review (inline comments in the same
   call) or one issue comment. Never both. Never two of either **on the same PR**.
3. **Never APPROVE** while any required check is failed, pending or unknown.
4. **Never invent a finding.** A finding with no concrete trigger is dropped in
   silence — not downgraded, not mentioned.
5. **Nits never block, and most stay silent.** A nit reaches the PR only inside the
   collapsed Nits block (§9), only with a concrete `path:line`, max 5 per run, and
   never changes the verdict. Always silent regardless: praise, generic refactor
   advice, speculative perf, pre-existing debt, anything the diff did not touch.
   "Could be cleaner" is silent except the one code-judo nit in Phase 8, which must
   name a layer, branch, or helper to delete.
6. **Voice.** GitHub text and chat follow **Voice** (just above §9). Teammate
   English on the PR. Chat: `bulma-memory`. Never caveman. Never a form.
7. **Fixed output template** (§9). Section order never changes; empty sections vanish.
8. **Phases run in order.** Do not start a phase before the previous one is done.
9. **Other reviewers' state is ignored.** An open CHANGES_REQUESTED from someone
   else is never a gate, never a DEFER reason, and never enters the body. Teams
   reply and push instead of dismissing, so that state is noise. Findings come from
   the code at the head SHA, not from review history. Never fetch their threads:
   a problem that still exists is found again by the axes; one that was fixed leaves
   nothing to deduplicate.
10. **My own open findings never expire silently.** A prior finding of mine is
    dropped only after it is re-verified against the head SHA (§4.2).
11. **Patch bind.** After Phase 10, every finding goes through
    `scripts/bind-findings.py`. A `path:line` that is not in this pass's patch
    (or a carry-forward allow-path) is dropped in silence. A finding with no
    `axis` is dropped the same way.
12. **High-risk critic.** When `scripts/classify-risk.py` prints `high`, spawn
    the critic before verdict. The critic walks contracts, integration/state,
    and security/data-loss on one spawn, without voting findings off. When
    the script prints `low`, skip the spawn.

## Caps

| Budget | Deep | Light |
|---|---|---|
| Full files read | 15 (highest churn first) | 4 (only to confirm a suspicion) + carry-forward re-reads (§4.2, ≤10, outside the cap) |
| Codegraph / caller queries | 8 | 3 |
| Findings published | 10 (blockers first) | 10 |
| Nits published | 5, collapsed block, never inline | 5 |
| Neighbour test files | only when new logic has no test in the diff | same |
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
| Chat summary shape | [references/CHAT.md](references/CHAT.md) |
| Failure modes | [references/FAILURES.md](references/FAILURES.md) |
| Graph and edges | [GRAPH.md](GRAPH.md) |
| STATE | [STATE.schema.md](STATE.schema.md) · [templates/STATE.md](templates/STATE.md) |

Correctness, Standards, and Self-verify are never skippable. A large diff is
not a reason.
