---
title: "Code review verdicts: APPROVE, REQUEST_CHANGES or DEFER only; dismissed CR is closed"
author: Ruver
date: 2026-11-06
id: l-0332910b
branch: fix/review-verdict-dismissed-cr
touches:
  - docs/commands/bulma-code-review.md
  - skills/bulma-code-review/GRAPH.md
  - skills/bulma-code-review/SKILL.md
  - skills/bulma-code-review/STATE.schema.md
  - skills/bulma-code-review/nodes/batches.md
  - skills/bulma-code-review/nodes/critic.md
  - skills/bulma-code-review/nodes/fetch.md
  - skills/bulma-code-review/nodes/gates.md
  - skills/bulma-code-review/nodes/pass_decision.md
  - skills/bulma-code-review/nodes/publish.md
---

## Decided
User rule (2026-11-06), supersedes the 2026-11-05 "everything else -> COMMENT" rule: bulma-code-review publishes only APPROVE, REQUEST_CHANGES or DEFER. A COMMENT review ("Reviewed, no blockers") is never a verdict; gate.py rejects event COMMENT. DEFER only for CI red/pending/unreadable (ci_red, ci_unknown), draft, merge conflict, or another reviewer's open (not dismissed) change request or unresolved thread (review_pending). A dismissed change request is closed (GitHub state DISMISSED) whoever dismissed it; it never blocks APPROVE. Another bot's approval on the head no longer downgrades APPROVE (bot quorum removed). Coverage incomplete, critic failed, unstable head: post nothing that run, report in chat.

## Tried and ruled out
Treating a dismissal as "never cleared" unless the original reviewer re-approved: teammates dismiss old human-sign-off change requests on purpose, so every such PR (api#2606, #2686, ui#3367, #3422, #3363) ended as COMMENT or DEFER review_context with zero findings and green CI.

## Watch out
gate.py exit codes now: 1 blocked, 4 DEFER review_pending, 5 DEFER ci_unknown; exit 3 is gone. The installed copy under ~/.bulma/workspaces/bulma-installed-main only changes after merge plus `bulma update`. needs_deep still reads older COMMENTED markers with coverage/uncertainty/critic_failed.
