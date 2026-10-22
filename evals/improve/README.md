# Evidence-driven improvement pilot

This opt-in tool connects a lookback signal to a frozen prompt amendment, a
paired execution pilot and a review packet. It never edits installed skills,
opens a PR or promotes a candidate. It tests coder instruction amendments only;
it does not optimize tools, orchestration, review policy or a whole delivery graph.

`prepare` and `report` are local operations. `probe` calls authenticated Claude
Code through the existing factory runner and incurs model cost. No paid probe
runs in CI. Use trusted fixtures: their executable graders run locally.

## Prepare one hypothesis

Run from a development checkout. Keep artifacts outside every git checkout.
First export a signal using the existing lookback:

```bash
python3 skills/bulma/scripts/lookback.py --since 120 --power shadow --json \
  > "$HOME/.bulma/experiments/lookback.json"
```

Create the experiments directory first if needed. Inspect source observations
and examples before selecting a cluster. Regex clusters can contain unrelated
matches; recurrence does not prove a cause. The tool requires at least five
distinct PRs for a proposed global lesson, following the lookback threshold.
An individual confirmed defect can still justify a project regression test.

Write one reviewed, bounded instruction amendment to an external text file.
State the expected outcome as a falsifiable hypothesis. Prefer an executable
project check when the defect has a precise predicate. Do not generate a global
rule from keywords alone.

Freeze an experiment before probing. Supply an exact model ID, not an alias.
For example, after reviewing a sibling-path hypothesis:

```bash
python3 evals/improve/run.py prepare \
  --lookback "$HOME/.bulma/experiments/lookback.json" \
  --cluster 'sibling-path parity' \
  --candidate /path/to/reviewed-amendment.txt \
  --hypothesis 'Tracing sibling writes reduces missed validation paths without regressions.' \
  --model "$PINNED_MODEL" --runs 3 --budget-per-run 0.25 \
  --development sibling-validation postgres-unavailable reuse-money duplicate-override \
  --heldout tenant-access concurrent-delivery pagination-bound advisory-status \
  --out "$HOME/.bulma/experiments/sibling-001"
```

These eight public fixtures are a smoke pilot, not historical task replays.
The held-out subset is withheld from model executions during development, but
is public to the proposal author. Do not tune on its results or repeatedly reuse
it as unseen evidence. Real promotion requires fresh, independent real-task cases.
The tool does not maintain a global registry of previously inspected cases.

The proposal freezes the hypothesis, split, model, repetitions, timeout, per-call
budget, minimum cost-per-correct saving, instructions, lookback and fixtures.
Hashes detect accidental drift; they are not signatures or an adversarial trust
boundary. A changed runner or frozen input requires a new proposal. Preserve
failed and rejected proposals as evidence instead of overwriting them.

## Probe and inspect

```bash
python3 evals/improve/run.py probe \
  --proposal "$HOME/.bulma/experiments/sibling-001" --phase development --dry-run
python3 evals/improve/run.py probe \
  --proposal "$HOME/.bulma/experiments/sibling-001" --phase development
python3 evals/improve/run.py report \
  --proposal "$HOME/.bulma/experiments/sibling-001"
```

The dry run prints calls and requested budget ceiling without invoking a model.
The example requests 24 development calls and 24 held-out calls, up to $12 in
CLI budgets across both phases. Billing can exceed a CLI ceiling on a final
in-flight request. Proposal authoring, preparation and human review are separate,
unmeasured costs. Unknown usage is never converted to zero. Host cost may be reported at list
prices rather than actual subscription billing. Prompt-cache warmth can affect
small comparisons; inspect cache usage and repeat balanced trials before claiming savings.

Only a development `pilot_pass` unlocks held-out execution:

```bash
python3 evals/improve/run.py probe \
  --proposal "$HOME/.bulma/experiments/sibling-001" --phase heldout
python3 evals/improve/run.py report \
  --proposal "$HOME/.bulma/experiments/sibling-001"
```

Baseline and candidate run in fresh workspaces with the same frozen task,
model, timeout and budget. Arm order alternates. Graders remain outside the
model workspace. The candidate appends its amendment to the frozen baseline.
A phase cannot be overwritten or retried in place, including interrupted runs.

## Interpret the report

- `reject`: a paired trial succeeds under baseline and fails under candidate.
  A host failure, budget stop or denied tool also cannot count as candidate success.
- `pilot_pass`: no paired regression and either a paired correctness improvement
  or the predeclared cost-per-correct saving, 10% by default.
- `inconclusive`: no demonstrated improvement, pending or incomplete evidence.
  Unknown cost cannot establish savings; a correctness gain may still pass a pilot.
- `review_candidate`: both phases pass. This is a candidate for human inspection,
  not approval to modify production or evidence of statistical equivalence.

`report.json` records paired outcomes, active execution seconds, observed probe
cost and limitations. `review.md` points reviewers to the amendment and raw
factory artifacts. Review source claims, delivered code, scope and failure logs;
then validate on real tasks with risk-appropriate repetition before proposing a
production PR. The general protocol is
[workflow experiments](../../skills/bulma-bus/EXPERIMENTS.md).
