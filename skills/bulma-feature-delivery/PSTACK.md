# Skill map

Spine (adapted) plus bundled primitives in `skills/`:

```
grill-with-docs → to-spec → to-tickets → implement(/tdd) → code-review
```

A clone of this repo is enough. Load primitives **by name** after
`install.sh` (they flatten next to the graphs).

Bugs: `diagnose` (then one implement ticket). Ungrillable feel:
prototype, then DECIDE.

## Bundled primitives (`skills/`)

Load the skill, then follow the **adapted** node.

| Skill | Node | Adaptation |
|---|---|---|
| `grill-with-docs` + `grill-me` | `grill` | Recommend + follow. ASK last resort. See [GRILL.md](GRILL.md). Vanilla "ask every branch and wait" is **off**. |
| `to-prd` | `spec` | Synthesize only. Write local `SPEC.md`. Do **not** publish a PRD to the tracker. |
| `to-issues` | `tickets` | Vertical slices into local `TICKETS.md`. Do **not** create tracker issues here. [BLOCKERS.md](BLOCKERS.md) is the only tracker-create path. |
| `tdd` + this graph's [TDD.md](TDD.md) | `implement` | Iron law wins. Do not skip RED because bundled `tdd` says the path is expensive. |
| `diagnose` | `diagnose` | Root cause. No product fix in this node. |
| `unslop` | all chat | Always. English. [VOICE.md](VOICE.md) |
| `how` | grill, diagnose | Subsystem you will touch, one pass. Not a swarm. |
| `why` | never default | Only when a last-resort design fork remains after `how` + tracker + neighbors. Not on implement, review, or lstm patch. |
| `blast-radius` | `blast` | Before quality/ship |
| `architect` | grill (new module) | Checkpoint only as last-resort ASK |
| `interrogate` | after spec, `full_feature` | Read-only, then DECIDE |
| `figure-it-out` | diagnose, no narrower playbook | Then one fix slice |
| `typescript-best-practices` / `no-comments` | review | `.ts` / `.tsx` |
| `technical-writing` | spec, PR body | |
| `thermo-nuclear-code-quality-review` | `quality` | Always `fix all`. Not optional. |
| `principle-fix-root-causes` | `diagnose` | Symptom guards are off. |
| `principle-sequence-verifiable-units` | `tickets` / `implement*` | One ticket, verify, then the next. |
| `principle-prove-it-works` | `tester` | Real commands. A skip is not a pass. |
| `principle-redesign-from-first-principles` | `no-comments` | Intent only. Does not widen the fence. |
| `show-me-your-work` | `grill` | Append `decisions.tsv`. TSV format only. |
| `receiving-code-review` | LSTM verify | Not this graph; `/lstm` |

`implement` does not reopen the plan. That is the point.

Sources and licences: `THIRD_PARTY.md` at the repo root. Not linked: a
skill has no path to the repo root once it is installed.
