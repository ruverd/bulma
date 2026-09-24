---
description: Adaptive PR review via gh. One PR on main thread; 2+ PRs → one fresh subagent each. Pending CI waits 5m (no comment); defers on CI red, draft, conflict. Deep then light. One artifact per PR.
argument-hint: "[PR ...] [--deep|--light] [--force] [--dry-run]"
---

# /bulma-code-review

Follow **`../skills/bulma-code-review/SKILL.md`** in full.

Use arguments from the user request.

```
/bulma-code-review 123
/bulma-code-review https://github.com/org/repo/pull/12 https://github.com/org/repo/pull/15
/bulma-code-review 12 15 18 --dry-run
```
