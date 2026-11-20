# Node: ci_watch

**Verb:** verify-remote
**Capability:** `gh` checks + dispatch a fix (orchestrator/coder); **never** merge
**When:** right after shipper opens/updates a PR (`open_pr: true`)

## Mission

Verify required CI on the PR. A stack child may instead satisfy the gate
through [verified scope and local proof](../CI_DELIVERY.md#stack-child-ci).
The umbrella requires hosted CI.

Follow [CI_DELIVERY.md](../CI_DELIVERY.md) + the spirit of `loop-on-ci` / `fix-ci`.

## Steps

1. Resolve the branch PR: `gh pr view --json number,url`.
2. `gh pr checks --json name,bucket,state,workflow,link` (or `glab ci status`).
3. For a stack child, check for proven build/test execution before accepting
   an all-green rollup. If missing, validate the exact head/base pair through
   the stack-child CI procedure. Only `out_of_scope` with matching local proof
   satisfies that path. Expected checks without execution and unknown scope
   stay open.
4. Pending → **poll** with short calls (`gh pr checks --json ...`) about
   ~5 min apart. Never trust `--watch` inside one
   tool call (10 min cap); a dead watch is **not** a CI fail — re-check.
5. Fail → extract the error → dispatch a **fresh** `bulma-fd-coder` with the fix
   (this node does not edit product code) → push → goto 2 (≤ `ci_fix_loops`).
6. All green → for each applicable feature failure test, verify execution
   on the current PR head using the relevant CI job log or test report.
   Record the test name and run link in CI evidence. If discovery or workflow
   scope excluded the test, route the gap through the fix loop. If execution
   cannot be verified, report it as unverified and escalate. Set STATE
   `ci.status: green` and allow `status: done` after these checks pass.
7. Fullstack: repeat for **each** PR.

## Output

```text
result: green | out_of_scope | escalated | skipped_no_pr
pr_url: ...
checks_summary: ...
fix_loops_used: N
```

## Budget

After **each** fix loop: estimate remaining context; if low → write HANDOFF
**before** the next fix (SKILL.md mechanism). A CI loop on a 20+ min repo
can take hours — never leave the handoff until after the blow-up.

## Hard rules

- Done with an open PR requires the applicable CI gate to pass.
- Do not invent "CI should be ok".
- Do not merge.
- Speak real status to the user in English.
