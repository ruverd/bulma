# Decision policy

Default to autonomous implementation decisions. Acquire missing user intent when
it changes the accepted outcome. Chat follows `bulma-memory`; forge text is English.

## Decide or ask

**DECIDE** from explicit acceptance criteria, relevant project rules and existing
patterns. Prefer the smaller reversible change. A recommendation is useful, but
the model's confidence is not evidence of the user's intent.

**ASK** when all three hold:

1. A missing fact or preference changes the accepted behavior, scope or a costly
   commitment. Name the concrete difference between plausible outcomes.
2. The answer is absent from the supplied context and relevant available sources.
   Read those sources once. Do not search code or prototype to infer a preference
   only the user can supply.
3. The likely cost of choosing wrong exceeds the interruption. Consider rework,
   reversibility and product impact, not just whether the topic sounds important.

Do not assign invented probabilities or numerical confidence thresholds. A cheap
prototype is useful when it can resolve feasibility or make a choice reviewable;
it is not a prerequisite to asking about missing intent.

Examples:

- Existing helper versus a new helper with the same behavior: DECIDE reuse.
- Delete a record versus retain its history, with no retention requirement: ASK
  before choosing the accepted behavior, even if one option seems technically best.
- Ticket explicitly requires retained history: DECIDE implementation from that
  constraint. Do not ask the user to repeat it.

Never invent product acceptance criteria. If a required fact is unavailable and
the user cannot supply it, report the blocker rather than guessing.

## Interaction

Ask the smallest set that unlocks work. Bundle up to three independent questions
in one message; ask dependent questions after their prerequisite answer. Include
the behavior each answer changes and a recommendation when useful.

Set `waiting_user` for work that depends on the answer. Continue independent,
already authorized work when possible; do not perform the dependent action until
answered. On resume, preserve settled decisions and ask only about remaining gaps.

Do not ask for:

- Facts already present in the repo, tracker or current conversation.
- Routing, seam or file choices settled by the graph or project rules.
- Approval to close discovery or synthesize a spec within the authorized scope.
- Rubber-stamping an implementation choice with no unresolved user intent.

An explicit request for a design interview enables deeper exploration. Load
bundled `grill-with-docs` only for that request. It does not widen
delivery scope or require another interview after the answers are recorded.

## Discovery and implementation

Use [GRILL.md](GRILL.md) for bounded discovery. `ASK last resort` in this graph
means the criteria above, not exhaustive searching before every question.
Use `how` or `architect` only for a named gap their output can resolve.

Implement does not restart discovery. On `NEEDS_CONTEXT`, resolve from the
contract and repo; ASK under this policy only if a consequential gap remains.
TDD requiring a redesign follows the same policy. Do not skip required TDD.
Missing contracts follow [BLOCKERS.md](BLOCKERS.md).
Stay inside the authorized goal. Reuse existing abstractions and visual patterns;
do not widen architecture or invent an endpoint to resolve a gap. UI decisions
also follow [UI_DESIGN_SYSTEM.md](UI_DESIGN_SYSTEM.md).

## Record once

Keep decision rationale in STATE `## Decisions` using the existing template:
choice, who decided, evidence or user answer, and material residual risk.
Confidence metadata does not establish intent. Record consequential decisions, not every routine
implementation detail. Spec and tickets reference that rationale and carry only
the constraints needed to execute. Do not also maintain `decisions.tsv` unless
the user requests an audit trail.

## Escalate

Exhausted loops or an unavailable critical dependency: set `status: escalated`,
stop dependent dispatch and report the blocker, evidence and resume point.
Tracker and PR notes remain English. Slice review/test loop exhaustion blocks
that ticket; never skip to the next ticket or ship it.
