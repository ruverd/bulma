# Review evidence

Use the sections referenced by preflight and the Tests and Contract phases.
Keep existing file/query caps, severity rules and the single-artifact contract.
These checks run on the current reviewer, without another agent or an external
skill installation. Store notes and command output under
`$BULMA_ROOT/.bulma-code-review/`.

## Isolated execution

Read source with `git show <sha>:<path>` or forge blob APIs at the pinned SHA.
If commits must be fetched or checks executed, use an isolated checkout via
[bulma-host](../../bulma-host/SKILL.md). Preserve existing clones, dirty files,
staged changes and branch refs. Do not stash user work to make review possible.

Before running a check, inspect changes to its script, hooks, build definition
and configuration. Use repository-supported commands. A worktree isolates
files, not databases or remote services; use disposable test resources and do
not run deploys or destructive operations as review checks.

Record command, working directory, full source SHA, exit code and output path.
Separate source inspection, local execution and CI evidence. If a command
cannot run, record the reason and continue source review. Apply existing
coverage and blocker-uncertainty gates; missing local execution alone is not
a fabricated defect and never turns unknown CI green.

## Tests that distinguish the defect

For changed runtime behavior, identify the concrete success, failure and
boundary scenarios that matter, including retry or partial writes when
applicable. Map them to assertions using the narrowest established test seam.
An existing integration test can supply the proof; a missing colocated test
file is not itself a finding. Missing-test findings name the changed behavior,
uncovered scenario and observable consequence.

Follow the assertion to the production symbol. A test that recreates the
implementation or mocks away the failing boundary does not verify that path.
Compare mocks with the real provider contract, including error and empty
responses. Confirm the relevant test is selected by a CI job or explicitly
report local-only coverage.

For a bug fix, check whether its regression test would fail with the defect
present and pass with the correction. When an existing isolated comparison
mechanism makes this practical, run both. The failing run must reach the
intended assertion; a setup, import or dependency failure proves nothing about
the defect. Never revert code in the user's checkout to create this comparison.
If execution is unavailable, inspect the assertion path and state that the
differential check was not run. Do not claim a runtime reproduction from a
source trace.

Run the floor guard in the isolated review checkout:
`python3 ../bulma-feature-delivery/scripts/floor-guard.py --repo <checkout> --base <pr base>`
(path from this skill's directory). Each `VIOLATION` row is a **major**,
`axis: tests`, unless the PR body or the linked ticket justifies it. Each
`ALLOWED` row names its reason: check that the reason holds, or it is a
major too. Exit 2 means the guard did not run; say so and do not count it as clean.

When the diff removes assertions, weakens fixtures or adds skips, identify
which behavior stops being checked. A known-flake note is a lead, not proof.
Compare the same command and environment at base and head before calling a
failure pre-existing. Without that comparison, report the cause as unverified.

## Paired changes and rollout

Run when a changed API, event, schema, migration, flag or required config value
depends on another deployment. Start with linked PRs and repository-declared
counterparts; do not guess repositories or scan unrelated PRs.

Record the counterpart revision and contract inspected. Check the intermediate
deployment states: new consumer with old provider, and old consumer with new
provider. Identify the safe merge/deploy order, flag/default behavior and the
rollback path after writes or migrations. A paired PR being merged does not
prove its code is deployed. Keep source compatibility separate from observed
environment availability.

If linked or directly related open PRs change the same route, schema or
registration, check their overlap for a concrete conflict. Missing deploy prose
alone is not a blocker. A reachable contract break is an `axis: contract`
finding with the failing version combination and causal changed hunk. An
unavailable counterpart that leaves a blocker-level question follows the
existing uncertainty gate. Record checked revisions, order and remaining gaps
in Coverage; never claim one PR's checks validate its counterpart.
