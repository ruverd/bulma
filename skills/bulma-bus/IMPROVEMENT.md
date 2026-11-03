# Offline process improvement

Use this opt-in path to investigate execution waste or compare recorded delivery
outcomes. It never changes delivery gates, calls a model, edits skills or publishes
anything. Keep records outside the checkout, under `$BULMA_ROOT/experiments/`.
Collect only explicitly selected evidence. Do not scan private session history.

Reuse [runtime measurements](PERFORMANCE.md) and existing run/job IDs. Confirmed
product defects still follow [verified prevention](FEEDBACK.md). Operational
friction is separate from defect and human-review telemetry.

## Record an assessment

From this skill's directory:

```bash
python3 scripts/improvement.py record --repo "$WORKTREE" \
  --directory "$BULMA_ROOT/experiments/process" --input /path/to/assessment.json
```

Example input, with a real content fingerprint and evidence path substituted:

```json
{
  "kind": "assessment", "run": "delivery-42", "task": "ticket-42",
  "variant": "baseline", "workflow": "<64-character SHA-256 of workflow inputs>",
  "configuration": "<pinned model/settings/environment identity>",
  "criterion": "test-command-discovery", "status": "fail", "method": "human",
  "cause": "project-command-rediscovered",
  "prevention": "Provide the existing test command in the project fixture",
  "counterexample": "Expected TDD RED and necessary diagnosis remain allowed",
  "evidence": ["/absolute/path/to/selected-execution.log"]
}
```

Classification is `pass`, `fail` or `unknown`; method is `human`, `deterministic`
or `model`. A fail requires a cause, concrete prevention, counterexample and
evidence. Record successful opportunities and unknowns too. One criterion per
run is one assessment, not one per tool call. Re-recording replaces that assessment
without increasing recurrence. Serialize writers through the coordinator.

Evidence files are hashed. Missing or changed assessment evidence is excluded;
affected outcomes stay in the report as unknown, with unknown cost and human time,
so their removal cannot inflate efficiency. Comparison refuses changed evidence. Records cannot be
reassigned to another task, workflow, configuration or repository. The identity
and evidence hashes detect accidental drift, not malicious input.

Only human or deterministic failures on at least two distinct tasks create a
candidate in the report. Repetitions of one task do not qualify. Model-only
classifications stay visible but never contribute to verified failure rates or
candidate recurrence. Calibrate a judge against independent labels before using
its suggestions. A candidate is a review lead, not a proven cause or adopted fix.

## Record a delivery outcome

Use the same command with `kind: outcome`. Required common fields are `run`,
`task`, `variant`, `workflow`, `configuration`; `trial` defaults to 1. Add:

- `status`: `accepted`, `rejected`, `blocked`, `cancelled` or `unknown`.
- `sha`: current artifact HEAD, plus `starting_sha` and `environment` fingerprint.
  `artifact_repo` optionally names a separate replay checkout.
- `scope`: `delivery` or `replay`. A replay oracle pass is not product delivery.
- `evidence`: acceptance evidence file paths. Accepted outcomes require evidence.
- Optional `first_pass`: boolean, unknown when absent. True requires accepted.
- Optional `metrics`: paths to existing runtime measurement JSON files for this
  run, including failed attempts and waits. Duplicate paths are rejected.
- Optional `cost_usd`, `cost_kind: api_billed` and `cost_source`: actual API cost
  for the entire run, including unsuccessful attempts. Host/list-price estimates
  do not belong here. Subscription cost without attribution stays unknown.
- Optional `human_ms` and `human_time_source`: measured steering duration,
  including corrections. Necessary product questions are not process failures.
- `task_fingerprint` is required for comparisons: SHA-256 content identity of
  task prompt and acceptance criteria. Replay supplies it automatically.

Accepted deliveries require a clean artifact checkout. Replay permits uncommitted
results and records their complete runtime tree identity; it never represents
those results as clean-head production acceptance.

Do not infer acceptance from graph completion, a judge grade or green CI alone.
One run covers a task/trial's attempts. Repetitions are separate runs with the
same task and different trial numbers. Keep blocked/cancelled outcomes; never
record an interrupted run as an inexpensive accepted task.

## Report or compare

```bash
python3 scripts/improvement.py report --repo "$WORKTREE" \
  --directory "$BULMA_ROOT/experiments/process"
python3 scripts/improvement.py compare --repo "$WORKTREE" \
  --directory "$BULMA_ROOT/experiments/process" --baseline baseline --candidate candidate
```

Reports group exact workflow/configuration identities and separate replay from
delivery. Cost per accepted run includes costs of rejected and blocked runs, and
is null unless every included run has known cost. Human time follows the same
coverage rule. First-pass coverage is explicit. Runtime duration sums are observed
work/waits, not elapsed time when work overlaps. Missing metric files reduce
coverage; zero observed duration does not establish zero work.

Comparison pairs task/trial IDs, checks starting SHA, environment, scope and task
fingerprint, lists unmatched trials, retains failures and exposes paired
regressions. Each variant must have one workflow/configuration identity. It never
promotes a candidate or claims statistical significance. Apply the matched-task,
held-out and quality rules in [EXPERIMENTS.md](EXPERIMENTS.md).

## Replay repository snapshots

`scripts/replay.py --manifest /path/to/suite.json --output /fresh/external/path`
executes the configured commands. A coding-agent command can incur model cost;
review its configuration and budget first. CI uses deterministic fixture commands.
The existing contributor improvement pilot remains useful for small coder
fixtures; this runner adds full repository snapshots and explicit host commands.

```json
{
  "repo": "/path/to/product", "environment": "<fixed toolchain/fixture hash>",
  "repetitions": 3, "seed": 42, "timeout_seconds": 180,
  "tasks": [{
    "id": "historical-task", "ref": "<starting commit>",
    "prompt": "<original request, without later answers>",
    "verify": ["/path/to/independent-verifier", "{repo}"]
  }],
  "variants": [{
    "name": "baseline", "configuration": {"model": "<pinned model>"},
    "policy_files": {"coder.md": "/path/to/reviewed-coder.md"},
    "command": ["/path/to/host-adapter", "{repo}", "{prompt}", "{policy}", "{config}"]
  }]
}
```

Add a candidate variant. `policy_files` are frozen per trial and hashed with the
command and configuration. Commands are argv arrays; placeholders are replaced
without shell interpolation. Repository refs resolve before execution. Every
trial exports tracked files into a new Git repository with one starting commit
and no remotes or future objects. Original worktree/index stay untouched. Dirty
uncommitted input is intentionally excluded. Submodules require explicit fixtures.
The manifest fingerprints the replay, capture and reporting scripts; comparisons
reject different runner fingerprints. Keep configuration free of credentials and
use the host's existing authentication.

The runner provides Git-history separation, **not OS or network isolation**.
A local process can still access the original checkout, external verifier,
other trial directories and remote services. Use trusted commands for local
smoke tests. For independent agent benchmarks, the host adapter must restrict
filesystem/network access, hide graders and other trials, substitute external
services and prevent PR/message side effects. Pin external verifier and adapter
versions as part of the environment; a path alone does not freeze their code.

Worker exit 0 allows independent verification; verifier exit 0 records a replay
acceptance. Host adapters must translate provider errors into nonzero exits,
including errors embedded in otherwise successful CLI responses. Exit 75 means
quota/budget exhaustion. It stops scheduling, as do timeout 124 and interruption
130. A snapshot/setup error also stops. `plan.json` preserves attempted and
not-started cells; outcomes retain attempted failures. Partial experiments cannot
establish a gain. Output directories are never overwritten. Usage, money and human
time remain unknown until supplied from reliable sources; runtime durations and
logs use the existing capture helper.
Runner exit 0 means the scheduled campaign finished, not that its trials passed.
Read the recorded outcomes and comparison before drawing a conclusion.
