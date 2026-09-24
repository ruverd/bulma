# Bulma: Jev picks the worker tier, code keeps quality gates

Status: accepted

Every worker inherits the session model (`model: inherit` in `agents/`,
`session_model: inherit` in every adapter). `IMPLEMENTATION.md` already
hints "mechanical coder: mid/fast", but nothing applies it, so a slice that
changes a button color costs the same as a tenant migration.

Decision: under `/bulma`, a tenth hook, `dispatch.tier`, asks Jev
`light | standard | heavy` per `spawn_worker` unit (each TICKETS.md slice,
each CI fix, each lstm patch), all slices in one call after `tickets`.
Code, not Jev, clamps the answer: `heavy` is the session model; gates
(reviewer, quality, plan-critic, debugger, triage, grill) never go below
it; `light` is refused on elevated risk or a `classify-risk.py` high path;
a fail escalates one tier inside the existing loop caps. The host mapping
(`tiers` in `$BULMA_HOME/bulma.json`) is the only place a model name
appears, so graph files stay host-free.

Measurement decides whether it pays: `DISPATCH.tsv` logs first pass,
loops, escalation, later reversals (CI, QA `PR_BUG`, lstm should-fix on the
unit's files) and worker tokens with retries. The hook starts under
`shadow` by default, and `dispatch report` prints a promotion gate. Criteria
text is versioned; `dispatch review` groups reversed units so each criteria
edit is a reviewed diff, not an automatic change.

Why not reuse the review gates as the safety net alone: they catch wrong
work, not weaker work. A cheaper coder can pass with weak tests or clumsy
code, and repeated fails end in `escalate`. The clamp rules and the
reversal signal cover what the gates miss.

Contract: `skills/bulma/DISPATCH.md`.
