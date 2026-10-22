# Bulma verification

## Launch and isolation

Bulma is a marketplace and CLI, with no application server to boot. Work from an
isolated Git worktree. Prerequisites are Git, Python 3, Node 22 or later, and Bash.
Install shellcheck to match CI lint. GitHub access is needed only for forge work.

Run `bash tests/repo.sh` from the clone. Ready means its checks finish with exit
zero, not that a process started. Installer tests create temporary homes and fake
host executables; never point those fixtures at the user's real home.

## Doctor

Run `git status --short`, `python3 --version`, `node --version` and
`bash --version`. Confirm the intended worktree and branch with
`git rev-parse --show-toplevel` and `git branch --show-current`. Read actual failed
check output before retrying; a missing tool is not a passing test.

## Feature map

| Feature | User entry and prerequisites | Actions | Observable pass condition | Evidence |
|---|---|---|---|---|
| Repository contracts | Clone with Python and Node | `bash tests/repo.sh` | Structure, routing and helper checks execute and pass | Captured stdout and exit code |
| Task proof | Python and Git | `python3 tests/lib/test_playbooks.py` | Required skips, missing baseline and stale evidence fail; valid equivalence passes | Test output |
| Runtime receipts | Python and Git | `python3 tests/lib/test_runtime.py` | Mutation, environment drift and changed log bytes invalidate reuse | Test output |
| Installation | Bash, Git and temporary-home fixtures | `bash tests/install.sh` | Managed copies and cleanup work inside temporary homes | Suite output |
| Agent decisions | Claude Code access and explicit evaluation budget | Run the `playbooks` tag per evals/README.md | Read graded responses and traces; report gaps and failures | External result JSON and report |

Use the `run` command of [runtime.py](../skills/bulma-bus/scripts/runtime.py) to keep evidence under
the run's `$BULMA_ROOT`. Model evaluation outputs likewise stay outside the clone.
Model availability or auth failure blocks that row only; it does not become PASS.

## Cleanup

Local Python suites remove their own temporary repositories and captures.
Installer tests remove their temporary homes. Stop only processes this run owns.
Keep the external run logs and evaluation receipts after cleanup. Confirm their
files still exist. Do not remove other worktrees or modify installed user skills
to recover a failed test.

## Last verified

The introducing PR records the exact revision, executed suites and evaluation
outcomes. These commands cover the shipped helpers and installer. They do not
establish cross-host behavioral equivalence or a productivity improvement.
