---
description: Address review comments and merge conflicts on an existing PR. Verify, patch, 👍 + unslopped reply on every comment, dismiss CHANGES_REQUESTED. Never merge.
argument-hint: "<PR | review | comment URL>"
---

# /ruver-lstm

Short alias: **`/lstm`**.

Follow **`../skills/ruver-lstm/SKILL.md`** in full.

Use arguments from the user request.

Same PR. Same branch. Draft stays draft. Always rebase conflicts.
Load `receiving-code-review` before any patch.
Patch via `ruver-fd-coder` + TDD. Grill only if the fix is complicated.
ASK last resort (same rule as `/ruver-developer`).
Every GitHub reply runs bundled `unslop` first. Never POST the
first draft. Every analyzed comment gets 👍 + a thread reply.
Then dismiss `CHANGES_REQUESTED`. Re-request if a fix landed.
