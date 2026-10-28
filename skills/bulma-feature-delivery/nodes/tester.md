# Node: tester

**Verb:** verify
**Capability:** execute (test/typecheck); no product fix
**Skills:** bundled `principle-prove-it-works`. A skipped command is not a pass.

## Mission

Objective hard gate with **real commands**.

## Commands (from STATE, filled by [PRODUCT.md](../PRODUCT.md))

0. Floor guard, first and always:
   `python3 <this skill>/scripts/floor-guard.py --repo <worktree> --base <base_branch>`.
   It reads the diff from the merge base, untracked files included, and fails
   on a move that lowers the bar: new suppression, skipped or focused test,
   deleted test file, assertions removed from a kept test, empty catch, stub,
   silenced CI step, lowered coverage threshold. Exit 1 is a fail like a red
   test, routed back to implement. Exit 2 means it could not run: record
   `floor_guard: error` and treat the gate as fail, never as a pass.
   A deliberate exception carries `floor-guard: allow <reason>` on the line, or
   `--allow RULE:PATH` for a whole file. Copy every `ALLOWED` row into STATE
   `floor_allowed` so review sees each one and its reason.
1. `typecheck_cmd` if set
2. `test_cmd` on the **touched area** (full suite only if expected <3 min)
3. `lint_cmd` only if expected <3 min and it is part of usual local CI
4. `e2e_cmd` only if done criteria require it
5. every command under project memory `## Checks`
   ([bulma-memory](../../bulma-memory/SKILL.md)), from the repo root, through
   the same runtime evidence capture. They are the project's own pre-push guards.
   A non-zero exit is a fail like any other. A command that cannot run here
   (missing tool) is recorded as skipped with the reason, never as a pass

Use the discovered `pkg` (`bun` / `pnpm` / `go` / `cargo` / …). Never `npm` when the lockfile is something else.

"Cheap" = **expected <3 min**. A command expected **>10 min** (tool cap)
is **CI-only** — declare `ci_only` in STATE, never try it locally
(or listed in `AGENTS.md` / `$BULMA_CI_LOCAL_SKIP`).

## Execution prerequisites

Before a suite requiring a database, browser or service, run its existing bounded
preflight in the same execution environment. Record the missing capability as
`hard_gate: skipped`, with command and evidence path. Do not spend another worker
round on the same structural blocker until the environment changes. Transient
failures retain the existing retry cap. Do not provision shared infrastructure.

An exit code of zero is necessary but insufficient: verify the required suite was
selected and executed assertions. Early returns or all-skipped suites are unproven.
Use the project's existing integrity reporter; do not add an LLM judge. With an
external QA provider, read its verdict and criterion coverage for the matching SHA;
a green advisory status carrying BLOCKED is not QA PASS. Do not start a second QA.

## Output

`hard_gate: pass | fail | skipped` + `floor_guard: pass | fail | error` +
`floor_allowed` + commands + exit codes in STATE.
Capture each check through [runtime evidence](../../bulma-bus/PERFORMANCE.md),
passing the test runner as direct argv. Cite `exit_code` from its JSON receipt
and include the receipt path. Never use the exit code of a later `echo`, `tail`
or `tee` as the verdict. Full logs stay outside the checkout; summarize them
after capture. Suites >10 min belong to CI,
not this gate (scope to the touched area). Any red = fail; flakes are judged by the
orchestrator.

## Hard rules

- Never invent pass.
- Do not edit source to "make it pass".
- Never add a `floor-guard: allow` marker yourself. Only the coder adds one, with
  a reason review can check.
- skipped only if the toolchain is impossible → orchestrator escalates.

## Capture and reuse

Read the applicable selected playbook contract and complete its tester-owned
proof rows. Read the content of each proof against acceptance; file existence
alone is insufficient. Refactoring runs the equivalence helper on captured
before/after receipts. Performance checks counts, spread and limiter evidence.
Use the project verification recipe when discovered in STATE, following
[bulma-host VERIFICATION.md](../../bulma-host/VERIFICATION.md). Recipe execution
does not start a second QA or override the configured QA provider.

Use [runtime evidence](../../bulma-bus/PERFORMANCE.md) for these commands.
A successful `runtime.py check` permits reuse only for deterministic local tests
with a complete environment fingerprint. Otherwise execute. Keep command, exit
code and evidence path in STATE. Full logs stay on disk; inspect relevant errors.
