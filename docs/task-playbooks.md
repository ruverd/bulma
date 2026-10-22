# Task playbooks and proof

Bulma selects a task contract alongside the existing delivery path and risk.
The contract changes the evidence needed to finish. Graph nodes, retry caps,
QA ownership and merge permissions stay in their current owners.

In Codex, give `$bulma-feature-delivery` the goal and the result that must hold.
For example, ask it to refactor the formatter while preserving every output
byte. Claude Code and Grok use `/bulma-feature-delivery` for the same skill.

| Task | Added proof |
|---|---|
| Investigation | Sources and a cited answer, with no product writes or PR |
| Bug fix | Original repro, confirmed mechanism and fixed-path execution |
| Feature | Acceptance contract and observed behavior; alternatives only when unresolved |
| Maintenance | Bounded scope and relevant executed checks |
| Refactoring | Captured baseline and current output equivalence |
| Performance | Realistic baseline, comparable repeated measurements and regression proof |
| Skill change | Structural checks and targeted behavior evaluation when decisions change |

The coordinator reads one selected contract from the
[catalog](../skills/bulma-feature-delivery/playbooks.json). It keeps one checklist
in STATE. Optional skips retain their reason; required proof cannot skip.
Historical baselines survive resume. Changed contracts or evidence need explicit
reconciliation. See [the protocol](../skills/bulma-feature-delivery/PLAYBOOKS.md).

## Check a refactoring

From a Bulma clone, select the contract:

```bash
python3 skills/bulma-feature-delivery/scripts/playbook.py select --kind chore --playbook refactoring
```

Before editing the target, run its fixed characterization probe through
the `run` command of [runtime.py](../skills/bulma-bus/scripts/runtime.py). Keep receipts outside the target
checkout. After editing, capture again with the same command, fixtures and
environment fingerprint. Then run the equivalence command from the selected
contract. The result is exact equality of captured output, scoped to that probe.
It is not proof of behavior the probe never exercised.

The checklist check also needs the freshly recomputed environment fingerprint
for refactoring. Failed, empty, mutating, altered or stale captures cannot pass.
Old runtime receipts without a log hash must be recaptured. Reviews still
inspect whether the probe covers the promised contract and stayed fixed.

## Maintain project knowledge

Use [project verification recipes](../skills/bulma-host/VERIFICATION.md) when
startup, login or feature driving gets rediscovered on every task. Authoring and
maintenance are requested tasks, not extra gates on ordinary work. A recipe is
delivered only after launch, doctor, a real feature and cleanup were exercised.
External QA can consume the same recipe without Bulma running another QA.

Bulma's own [verification recipe](verification.md) covers repository invariants,
task proof and installer isolation. Agent behavior cases use the `playbooks` tag
in [the existing evaluation suite](../evals/README.md). Local deterministic tests
run in CI. Model evaluations run only when requested, with bounded spend.
