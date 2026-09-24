# Node: ci_watch

**Verb:** verify-remote
**Capability:** `gh` checks + dispatch a fix (orchestrator/coder); **never** merge
**When:** right after shipper opens/updates a PR (`open_pr: true`)

## Mission

Guarantee **CI/CD 100% green** on the PR. Until then the task is **not** delivered.

Follow [CI_DELIVERY.md](../CI_DELIVERY.md) + the spirit of `loop-on-ci` / `fix-ci`.

## Steps

1. Resolve the branch PR: `gh pr view --json number,url`.
2. `gh pr checks --json name,bucket,state,workflow,link` (or `glab ci status`).
3. Pending → **poll** with short calls (`gh pr checks --json ...`) about
   ~5 min apart. Never trust `--watch` inside one
   tool call (10 min cap); a dead watch is **not** a CI fail — re-check.
4. Fail → extract the error → dispatch a **fresh** `bulma-fd-coder` with the fix
   (this node does not edit product code) → push → goto 2 (≤ `ci_fix_loops`).
5. All green → STATE `ci.status: green`, allow `status: done`.
6. Fullstack: repeat for **each** PR.

## Output

```text
result: green | escalated | skipped_no_pr
pr_url: ...
checks_summary: ...
fix_loops_used: N
```

## Budget

After **each** fix loop: estimate remaining context; if low → write HANDOFF
**before** the next fix (SKILL.md mechanism). A CI loop on a 20+ min repo
can take hours — never leave the handoff until after the blow-up.

## Hard rules

- Done **only** with green (if there was a PR).
- Do not invent "CI should be ok".
- Do not merge.
- Speak real status to the user in English.
