# Node: quality (thermo-nuclear)

**Verb:** harden
**Capability:** read-write (fix code quality); **no** merge, **no** PR yet
**Skill:** `thermo-nuclear-code-quality-review` + agent `thermo-nuclear-code-quality-review`

## Mission

Before **any** final commit / push / PR: run the **thermo-nuclear code quality**
audit on the branch diff and **apply every fix** (`fix all`).
Only then does the shipper package.

## When

After **blast** (or after **evidence** on `light_change`).
Before **shipper**. Thermo `fix all` is still required before any PR.

## Steps

1. Load the branch diff and the touched files (orchestrator or this node):
   - `git diff <base_branch>...HEAD` (and unstaged if not committed yet)
   - contents of the touched files
2. Invoke the thermo-nuclear review with the bundled skill
   `thermo-nuclear-code-quality-review` (`skills/thermo-nuclear-code-quality-review/`). Always.
   Do not skip.
3. Required mode: **`fix all`**
   - Do not only list findings.
   - Apply **every** quality fix in the code (code judo, decomposition, anti-spaghetti, etc.).
   - Preserve behavior and **TDD** (if you touch logic, keep tests green; adjust tests if needed without weakening them).
4. Re-run the cheap hard gate (typecheck + unit of the area) after the fixes.
5. Record each finding you fixed with
   `../bulma-bus/scripts/observe.py --source fd --reviewer bulma-fd-quality`
   (path from this skill's directory; fields in
   [INSIGHTS.md](../../bulma-bus/INSIGHTS.md)). A failed write is a chat
   note, never a reason to block.
6. Update STATE:
   - `## Quality (thermo-nuclear)`
   - findings → fixed / remaining
   - if a residual structural **blocker** has no safe fix → `result=blocked` (do not open a PR)

## Output

```text
result: ok | blocked
findings_fixed: N
findings_remaining: [...]
hard_gate_after: pass | fail
summary: ...
```

## Hard rules

- **Forbidden** commit/push/PR in this node (shipper does that **after**).
- **Forbidden** skipping with "lgtm without running".
- **Forbidden** merge.
- Do not invent features; structural quality on the diff only.
- If `fix all` breaks tests and cannot recover in 1 cycle → blocked / back to coder (orchestrator).
- Chat (`bulma-memory`) if you need to explain residual issues.

## Orchestrator note

Mental equivalent of what the user would run:

```text
/thermo-nuclear-code-quality-review fix all
```

Then: commit → push → draft PR (shipper).
