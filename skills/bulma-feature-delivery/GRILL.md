# Bounded discovery

The `grill` node resolves implementation gaps. It is not a mandatory interview.
Policy: [DECISION_POLICY.md](DECISION_POLICY.md). Load bundled
`grill-with-docs` only when the user requests a deeper design interview.
Formats: [CONTEXT-FORMAT.md](../grill-with-docs/CONTEXT-FORMAT.md),
[ADR-FORMAT.md](../grill-with-docs/ADR-FORMAT.md).

ASK for unavailable information that changes the accepted outcome when the cost
of choosing wrong exceeds the interruption. Confidence alone does not settle intent.

## Goal

Resolve decisions required to implement the acceptance criteria. Start with one
bounded discovery pass on the touched subsystem. Do not interview through an
open-ended design tree or explore alternatives with no implementation consequence.

## Loop

1. Reuse supplied acceptance criteria, existing patterns, contracts and recorded
   decisions. Read missing relevant sources once. If these already settle the
   change, record only material gaps and continue; do not generate a design tree.
2. Run `scripts/plan-shape.py --risk <risk> --files <estimated behavioral files>
   --units <vertical slices>` with `--cross-contract`, `--structural` and
   `--uncertain` when those facts apply. Unknown facts mean `--uncertain`.
3. Select the design and test plan. DECIDE reversible details from repo patterns.
   Record consequential rationale once in STATE. The spec node writes the
   executable contract; do not draft a second plan here.
4. Continue discovery only for a named unresolved decision that changes behavior,
   a contract, testability or a hard-to-reverse choice. Record that decision and
   the evidence sought before another lookup. No new round for wording or polish.
5. ASK under DECISION_POLICY when missing information changes the outcome.
   Batch independent questions, sequence dependent ones. Set `waiting_user` for
   dependent work. Do not exhaust lookups for a preference only the user knows.
6. Decisions needed for implementation resolved → **spec**. Budget exhaustion is
   not resolution: escalate or ASK under policy if a blocking decision remains.

Most runs never hit step 5.

Load bundled `how` only for a named subsystem gap. Do not spawn an explorer
swarm. Routine delivery does not load interview skills.

Use `architect` when a new module has an unresolved boundary or contract; creating
a module alone does not require another planning pass.

## ASK format (rare)

Speak in the chat language (`bulma-memory`):

Use this shape per missing decision. Up to three independent questions may share
one message; dependent questions wait for the prerequisite answer.

```
Q: <missing information and the behavior it changes>

A. ...
B. ...

Recommendation: A, because <fact>.
I am asking because: <cost of the wrong outcome and why sources cannot settle it>.
```

## Docs (grill-with-docs)

Read, in order, whatever exists:

1. `CONTEXT.md` (only if already in the repo)
2. `CLAUDE.md` / `AGENTS.md`
3. nearest `src/**/CLAUDE.md`
4. `docs/en-US/` or `docs/adr/` if the area has them

Use code and docs for current behavior; explicit ticket AC defines requested
behavior within project constraints. Consequential conflicts follow the decision
policy. Do not infer desired behavior from code alone.

Do **not** create a new `CONTEXT.md` or ADR in the git repo unless that tree already exists. Domain terms go in STATE `## Decisions`. If `CONTEXT.md` / `docs/adr/` already exist, update them lazily (domain language only).

ADR when hard to reverse + surprising later + real trade-off. Write it on DECIDE. Do not ASK for permission to write an ADR.

## UI

DS of the repo. Figma if the ticket has it. No Figma → copy 2–5 recent same-type screens. Record those paths. Do not invent visual.

## Ungrillable

For uncertain feel or layout, prototype when it will supply useful evidence.
DECIDE reversible details from existing screens. ASK when an unresolved product
preference changes acceptance; a prototype is not required before asking.

## Done

Implementation decisions resolved → spec. Short chat-language rollup of decisions.
STATE holds consequential rationale. Do not duplicate it into a TSV by default.

## Compact contract

For `plan_mode=compact`, keep one canonical `TICKETS.md` containing a short design
preamble and one `## Ticket 1:` section in the standard ticket format. Include
acceptance, reuse paths, contracts/risks, decisions, RED/GREEN and files. Set
`spec_path` and `tickets_path` to this same file. Spec synthesizes it; tickets
validates it without rewriting. Detailed mode retains separate SPEC and TICKETS.
All downstream readers use STATE paths, including dispatch, plan critic and resume.
Expand to detailed if discovery or implementation exposes another independent
slice, unknown contract or elevated risk. Existing resumes keep their format.
