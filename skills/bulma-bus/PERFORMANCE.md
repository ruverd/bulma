# Execution evidence and performance

Use `scripts/runtime.py` from this skill for tester commands and runtime
reproductions. It executes an argv without a shell, saves full output outside
the checkout and returns one JSON line. Example, from the installed bus folder:

```bash
python3 scripts/runtime.py run --repo "$WORKTREE" \
  --directory "$BULMA_ROOT/.bulma-bus/evidence" --trail \
  --environment "$ENV_FINGERPRINT" -- pnpm test --runInBand
```

`--trail` uses Trail when installed, otherwise captures to a plain file.
Trail's session ID and file path are in `output.log`; query that session through
`runtime_logs` in bulma-host. Capture is automatic; guided probe insertion is
only for a reproduction that existing logs cannot explain. Remove probes before
final validation. Never treat empty logs as a pass. Read the recorded exit code.

The environment fingerprint must identify toolchain versions, installed
dependencies, relevant configuration and external fixtures. Hash these values;
never store credentials. An unknown or changing external service means no reuse:
omit `--environment`. Ignored inputs such as generated files and node_modules
must be covered by this fingerprint or the result is not reusable.

Before reusing a successful check, run `check --repo ... --evidence ...
--environment ... -- <exact argv>`. It compares repository path, HEAD, tracked
changes, untracked files, submodule state, command and environment. Missing logs,
failed checks or a tree changed by the command invalidate evidence. Never reuse
TDD RED, flaky tests, remote CI status, security sign-off or live review context.
The check is an optimization for identical local validation, not an approval gate.

## Measurements

At each node exit, append a measurement using `measure --repo ... --directory
"$BULMA_ROOT/.bulma-bus/metrics" --input FILE`. Use a stable `sample_id` per
node attempt. Replaying that observation replaces it rather than double-counting.
The input has `run`, `sample_id`, `graph`, `node`, `kind` (`active` or `wait`) and
`duration_ms`. Optional `workers`, `retries`, `input_tokens`, `output_tokens`,
`cached_tokens` are nonnegative counts. Token fields require `usage_source`, a
host usage event identifier. Missing host usage stays null; never estimate it.
Record deltas per attempt, not cumulative session totals. Clock durations come
from execution timestamps, not a model estimate. Observation failure is a note,
never a reason to repeat product work or block delivery.

`report --directory ...` aggregates active time, waits and observed usage by node.
`usage_samples` exposes partial coverage. `bulma report` also includes these measurements alongside its existing
transition ledger; neither report claims missing host usage is zero.

Compare matched tasks with the same model, repository snapshot and risk: reviewer,
LSTM, small feature and elevated-risk feature. Record first-pass success, retries,
false positives and defects found by later human review alongside time and tokens.
Do not claim quality equivalence from a smaller prompt or a single green run.
