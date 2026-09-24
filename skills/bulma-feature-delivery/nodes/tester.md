# Node: tester

**Verb:** verify
**Capability:** execute (test/typecheck); no product fix
**Skills:** bundled `principle-prove-it-works`. A skipped command is not a pass.

## Mission

Objective hard gate with **real commands**.

## Commands (from STATE, filled by [PRODUCT.md](../PRODUCT.md))

1. `typecheck_cmd` if set
2. `test_cmd` on the **touched area** (full suite only if expected <3 min)
3. `lint_cmd` only if expected <3 min and it is part of usual local CI
4. `e2e_cmd` only if done criteria require it

Use the discovered `pkg` (`bun` / `pnpm` / `go` / `cargo` / …). Never `npm` when the lockfile is something else.

"Cheap" = **expected <3 min**. A command expected **>10 min** (tool cap)
is **CI-only** — declare `ci_only` in STATE, never try it locally
(or listed in `AGENTS.md` / `$BULMA_CI_LOCAL_SKIP`).

## Output

`hard_gate: pass | fail | skipped` + commands + exit codes in STATE.
Exit codes via wrapper (`<cmd>; echo "<cmd> exit=$?" >> .bulma-feature-delivery/gates.log`)
and **cited** from the file — never retyped from memory. Suites >10 min belong to CI,
not this gate (scope to the touched area). Any red = fail; flakes are judged by the
orchestrator.

## Hard rules

- Never invent pass.
- Do not edit source to "make it pass".
- skipped only if the toolchain is impossible → orchestrator escalates.
