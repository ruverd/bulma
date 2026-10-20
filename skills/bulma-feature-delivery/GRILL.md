# Grill (Matt Pocock, last-resort ASK)

Source: bundled `grill-with-docs` + `grill-me` (`skills/grill-with-docs/`, `skills/grill-me/`).
This file is the adapted loop. Policy: [DECISION_POLICY.md](DECISION_POLICY.md).
Formats: [CONTEXT-FORMAT.md](../grill-with-docs/CONTEXT-FORMAT.md),
[ADR-FORMAT.md](../grill-with-docs/ADR-FORMAT.md).

ASK is last resort: very important **and** high uncertainty, after lookup.

## Goal

Resolve decisions required to implement the acceptance criteria. Start with one
bounded discovery pass on the touched subsystem. Do not interview through an
open-ended design tree or explore alternatives with no implementation consequence.

## Loop

1. List acceptance criteria, existing patterns, contracts, risks and unresolved
   implementation decisions. Read each relevant source once.
2. Run `scripts/plan-shape.py --risk <risk> --files <estimated behavioral files>
   --units <vertical slices>` with `--cross-contract`, `--structural` and
   `--uncertain` when those facts apply. Unknown facts mean `--uncertain`.
3. Write the selected design and test plan. DECIDE reversible details from repo
   patterns. Record evidence in STATE decisions.
4. Continue discovery only for a named unresolved decision that changes behavior,
   a contract, testability or a hard-to-reverse choice. Record that decision and
   the evidence sought before another lookup. No new round for wording or polish.
5. ASK only under DECISION_POLICY when that decision remains important and highly
   uncertain. Stop at `waiting_user`; otherwise resolve it and continue.
6. Decisions needed for implementation resolved → **spec**. Budget exhaustion is
   not resolution: escalate or ASK under policy if a blocking decision remains.

Most runs never hit step 5.

Load bundled `how` for the subsystem you will touch, not the whole
monorepo. One pass. Do not spawn a how-explorer swarm. Do not load
`why` unless a last-resort design fork remains after that lookup.
Do **not** run vanilla grill-with-docs interview-and-wait.

New module: run `architect`. Take the synthesized sketch (DECIDE). Checkpoint only as last-resort policy.

## ASK format (rare)

Speak in the chat language (`bulma-memory`):

```
Q: <only the tie lookup did not break>

A. ...
B. ...

Recommendation: A, because <fact>.
I am asking because: important + high uncertainty after <paths / tracker>.
```

## Docs (grill-with-docs)

Read, in order, whatever exists:

1. `CONTEXT.md` (only if already in the repo)
2. `CLAUDE.md` / `AGENTS.md`
3. nearest `src/**/CLAUDE.md`
4. `docs/en-US/` or `docs/adr/` if the area has them

Code vs ticket wording: the code + docs win unless the ticket AC explicitly overrides. DECIDE. ASK only if both readings are still plausible **and** the fork is very important.

Do **not** create a new `CONTEXT.md` or ADR in the git repo unless that tree already exists. Domain terms go in STATE `## Decisions`. If `CONTEXT.md` / `docs/adr/` already exist, update them lazily (domain language only).

ADR when hard to reverse + surprising later + real trade-off. Write it on DECIDE. Do not ASK for permission to write an ADR.

## UI

DS of the repo. Figma if the ticket has it. No Figma → copy 2–5 recent same-type screens. Record those paths. Do not invent visual.

## Ungrillable

Feel, layout, "one page or three": prototype, then DECIDE the smaller option that matches existing screens. ASK only if the prototype still leaves a last-resort fork.

## Done

Implementation decisions resolved → spec. Short chat-language rollup of decisions.
Append rows to `decisions.tsv` (bundled `show-me-your-work` TSV format).

## Compact contract

For `plan_mode=compact`, keep one canonical `TICKETS.md` containing a short design
preamble and one `## Ticket 1:` section in the standard ticket format. Include
acceptance, reuse paths, contracts/risks, decisions, RED/GREEN and files. Set
`spec_path` and `tickets_path` to this same file. Spec synthesizes it; tickets
validates it without rewriting. Detailed mode retains separate SPEC and TICKETS.
All downstream readers use STATE paths, including dispatch, plan critic and resume.
Expand to detailed if discovery or implementation exposes another independent
slice, unknown contract or elevated risk. Existing resumes keep their format.
