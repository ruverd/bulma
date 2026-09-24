# Dispatch tier

Which model a worker runs on. Without `/bulma` every worker inherits the
session model (`session_model` in [bulma-host](../bulma-host/SKILL.md)). Under
the overlay, `dispatch.tier` lets simple units run cheaper and measures
whether quality held. Graph files never name a model; the mapping lives in
`$BULMA_HOME/bulma.json`.

## Unit

One `spawn_worker` call. Kinds: `slice` (one ticket from fd `TICKETS.md`),
`ci_fix` (coder dispatched by `ci_watch`), `lstm_patch` (should-fix patch).
A re-fix of the same slice is the same unit one tier up, not a new unit.

## Tiers

`light | standard | heavy`. `heavy` is the session model, always. A tier
never goes above it.

| role | tier |
|---|---|
| coder (every unit kind) | `dispatch plan` (Jev + rules) |
| tester, shipper | `light` by rule (`dispatch role tester`) |
| reviewer, quality, plan-critic, debugger, triage, grill | `heavy`, always |

Gates never get a weaker model. Under `shadow` every role prints `heavy`.

## Rules (in code)

1. `shadow`, Jev undecided, or Jev down -> `heavy`.
2. `light` with `risk=elevated`, or any file that
   `../bulma-code-review/scripts/classify-risk.py` calls high -> `standard`.
3. Review, test or CI fail -> `dispatch result <unit> fail --stage <s>`
   prints the next tier (light -> standard -> heavy). The re-dispatch uses
   it. Loop caps stay as they are: escalation spends a loop, never adds one.
4. Never ASK the user for a tier.
5. The orchestrator passes only the printed `spawn=` args: no model,
   effort or worker type of its own choosing on any worker spawn.

## Commands

```text
bulma.py dispatch plan --tickets TICKETS.md --risk <risk> --path <path> --host <host> --context repo=... --context pr=...
bulma.py dispatch plan --unit-text FILE --unit-kind ci_fix --files a.ts,b.ts --risk <risk> --host <host>
bulma.py dispatch role tester --host <host>
bulma.py dispatch result <unit> pass|fail [--stage review|test|ci] [--tokens N]
bulma.py dispatch reverse <unit> | --file PATH [--pr N] --source ci|qa|lstm|user
bulma.py dispatch report
bulma.py dispatch review
bulma.py dispatch map <host> [light|standard key=value ... | inherit]
```

`plan` prints one line per unit:
`ticket 2 tier=light spawn=model=haiku unit=u-… · J: dispatch.tier tier=light .91 ok [id]`.
Pass the `spawn=` args to the host's spawn call (`inherit` means none). Keep
the `unit=` id: every `result` and `reverse` names it.

A host with no mapping for a tier runs `inherit`, so nothing changes until
the user maps it.

## Hosts

What each host can apply per worker call lives in
[bulma-host](../bulma-host/SKILL.md) §Worker tier. `dispatch map` rejects
keys the host cannot take.

`agent=<name>` means spawn that worker definition instead of the default
one. Use it for what a host cannot take per call: on Claude Code, a copy of
`bulma-fd-coder` with `effort: low`. Keep such definitions in the user's
host config, not in this repo, so no model name lands in git.

Starting points (tune from `dispatch report`, not from this table):

```text
bulma.py dispatch map claude light model=haiku
bulma.py dispatch map claude standard model=sonnet
bulma.py dispatch map codex light model=gpt-6-luna effort=low
bulma.py dispatch map codex standard effort=medium
bulma.py dispatch map cursor light model=fast
```

Claude Code ignores per-call models when `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1`
is set, and swaps any model outside the org `availableModels` list; both
make `light` run on something else, which `dispatch report` then shows as
no saving.

## Measurement

`.bulma-core/DISPATCH.tsv`, one row per unit: `tier_jev`, `tier_run`,
`clamp`, `first_pass`, `loops_used`, `escalated_to`, `worker_tokens`,
`outcome`, `criteria_version`, and the state file path. The Jev answer also
lands in `DECISIONS.tsv` as usual.

Quality signals, strongest first:

1. **reversed**: the unit escalated (rule 3) or a later signal hit its files
   (`dispatch reverse`: CI red after push, QA `PR_BUG`, lstm should-fix).
   When Jev's answer lowered the tier, the `DECISIONS.tsv` row is marked
   `reversed` too.
2. **first pass**: review and tests passed on the first dispatch.
3. **loops per unit**.

Cost: `worker_tokens` summed per tier, retries included. Pass `--tokens`
when the host reports worker usage; leave it out otherwise.

## Promotion gate

Promote with `bulma.py power set cautious --hook dispatch.tier`
(`/bulma power cautious dispatch.tier`); demote with `shadow`.

`dispatch report` ends with one `gate:` line:

- **shadow**: keep collecting until 30 units Jev would have lowered. Then
  `ready for cautious` when the units Jev called `light` passed first time
  at least as often as the units it called `heavy` (all ran heavy, so this
  checks the label, not the cheaper model).
- **live** (`cautious` or above): after 30 `light` units, `demote to shadow`
  when more than 10% were reversed, else `holds`.

Override with `"dispatch_gate": {"units": 30, "reversed": 0.10}` in
`bulma.json`. `/bulma tune dispatch.tier.tier <act_at>` moves the threshold;
`/bulma report` agree% is not meaningful here, because the graph answer is
always `heavy`.

## Improving the criteria

The pattern is the `tier` criteria text in `decisions.json` plus `act_at`.

1. `dispatch review` groups reversed units by kind, UI and Jev label, with
   the state file of each.
2. Propose one criteria edit that would have kept those units out of the
   lower tier (for example "a UI slice that adds a new variant is not
   light"). The user approves; bump `criteria_version`.
3. `dispatch report` splits rows by version. A version whose reversed %
   is higher than the one before it goes back.

No automatic criteria edits: every change is a reviewed diff.
