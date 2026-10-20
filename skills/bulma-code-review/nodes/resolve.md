# 1. Resolve

Argument: **one** PR URL, **one** PR number, or empty (PR of the current branch).
If the invocation already listed 2+ PRs, the orchestrator (§0) handled fan-out —
this section only ever sees a single target (main thread or one child).

```bash
gh auth status                       # stop and print output if unauthenticated
gh repo view --json nameWithOwner --jq .nameWithOwner   # → REPO when arg is a number
ME=$(gh api user --jq .login)
```

Load `bulma-memory` before the first chat sentence.

Before gates, resolve `reviewer_model` using
[bulma-host](../../bulma-host/SKILL.md) §Review model identity and record it in
this pass's STATE. Refresh it for each pass, including a resumed CI wait.
Each worker resolves its own value; never reuse a prior pass's model identity.

Flags: `--deep` force deep, `--light` force light, `--dry-run` run everything and
print to chat but post nothing, `--force` review despite non-green CI. `--deep` and
`--light` override §2 only; nothing but `--force` relaxes a §3 gate, and it relaxes
the failure/unknown CI inspection rows alone. Pending CI permits inspection by
default, but publication still waits.

Stop if the repo or PR cannot be resolved. Never guess a repo.
