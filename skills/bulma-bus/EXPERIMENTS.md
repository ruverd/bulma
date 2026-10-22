# Workflow experiments

Use this protocol when evaluating a workflow change. It is not a delivery gate.
Keep experiment state outside the checkout under `$BULMA_ROOT/experiments/`.
Use [PERFORMANCE.md](PERFORMANCE.md) for observed usage and execution evidence.

## Compare policies

Start with 30–50 real tasks, stratified by bug, clear feature and feature with
missing user intent. Include low, normal and elevated risk. Use only tasks with
known starting snapshots and independently checkable acceptance criteria.

Freeze three variants before the pilot:

- Baseline: the exact workflow revision before the proposed change.
- Selective: bounded discovery, compact contracts where eligible, questions under
  the decision policy, no default interview helpers or duplicate decision log.
- Interview: the selective variant with a deeper design interview on ambiguous
  tasks. Other execution and verification rules stay identical.

The baseline/selective comparison measures the combined workflow change. The
selective/interview comparison isolates interview depth on ambiguous tasks.
Use further single-change comparisons before attributing gains to an individual
helper, log or gate.

Use the same model version, settings, tools, starting snapshot and resource caps
for each matched task. Run at least three trials per task and variant, in isolated
worktrees and environments. Randomize run order. Reset memory and external state
between variants; never let one see another's solution or user answers.

For retrospective tasks, give a respondent the original intent and let it answer
only what was asked. Label simulated respondents separately from real users;
never give the executor hidden acceptance tests. Include a small real-user check
before treating simulated interaction savings as measured human savings.

Split development and held-out tasks before tuning. Freeze the policy again
before running held-out evaluation. Never optimize against held-out answers.

## Measure outcomes and cost

Score behavior against acceptance criteria, regression checks and independent
human review blinded to variant. CI success alone does not establish intent fit.
Record for each task, variant and trial:

- First-pass acceptance, final acceptance, defects and their severity.
- Rework attempts, scope violations and unnecessary questions.
- Active duration, human wait duration and total wall-clock duration.
- Observed input/output/cached tokens, model calls and actual API cost if available.
- Question rounds and measured respondent time. Missing observations stay unknown.
- Stage-level defects caught, false positives and time spent, including later
  human findings that an earlier gate missed.

Set identical total caps and report capped or failed runs. Count all proposal,
probe, composition, reflection and discarded executions in an optimization cost.
Report experiment cost separately from ordinary delivery cost.

## Promote or reject

Set an acceptable quality regression margin and target cost/latency reduction
before running. Compare paired results by task and risk; report variation and
uncertainty intervals, not only pooled averages. The pilot finds signals; it
cannot establish safety equivalence for rare defects.

Reject changes that introduce critical scope or intent failures. Investigate
other regressions before promotion. Keep changes only when measured savings meet
the predeclared target and quality evidence meets the agreed margin. An
inconclusive result remains inconclusive. Do not remove verification gates based
on prompt size or one green run.

For a Harness²-style iteration, propose one bounded policy edit, probe matched
tasks, inspect behavioral differences and retain only supported lessons. Version
the policy and keep a rollback point. Do not recursively edit the live delivery
workflow or accumulate untested lessons in always-loaded memory.
