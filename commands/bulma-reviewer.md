---
description: Review a PR/branch. Diagnose CI. Classify root cause. Never merge.
argument-hint: "<PR url | owner/repo#N | branch>"
---

# /bulma-reviewer

Short alias: **`/reviewer`**.

Follow **`../skills/bulma-reviewer/SKILL.md`** in full.

Use arguments from the user request.

Start with `/bulma-code-review`. Draft DEFER is expected and unchanged.
CI comes from GitHub Actions runs plus `statusCheckRollup.state`. If those
cannot be read, the review continues and CI is `unverified`.
Codex invokes `$bulma-reviewer`; Cursor and Claude invoke `/bulma-reviewer`.
