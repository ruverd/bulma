# 0. Multi-PR fan-out (orchestrator only)

Run this section **once** at the start of the invocation, before any §1–§11 work
that reads a diff.

### 0.1 Parse arguments → PR list

Accept one or more of: PR URL, `owner/repo#N`, bare number (current repo), or empty
(current branch → one PR). Flags (`--deep`, `--light`, `--dry-run`, `--force`) apply
to every PR in the batch.

Normalize into an ordered list of `{REPO, PR}` pairs. Deduplicate by `repo#number`.
If empty after resolve, stop (same as single unresolvable PR).

### 0.2 Branch

| Count | Action |
|---|---|
| **1** | Stay on the **main thread**. Run §1–§11 for that PR. No subagent. |
| **2+** | **Orchestrator mode** — do **not** fetch diffs, run axes, or post reviews on the main thread. Follow §0.3–§0.5. |

### 0.3 Spawn — one fresh subagent per PR

For each PR in the list, spawn a **separate** subagent (parallel when the host allows):

- **Fresh context** — no shared review state between children.
- **Prompt must include:** this skill path / name (`bulma-code-review`), the single
  target (`REPO` + `PR` or full URL), the same flags as the parent, and an explicit
  constraint: **review this one PR only; do not fan out again; do not spawn further
  multi-PR subagents**. Spawn payload:
  [bulma-host](../../bulma-host/SKILL.md) `spawn_worker`. Do not paste
  GRAPH.md or the parent tool catalog. Pass a path to the diff, not the
  diff inline.
- Each child runs the full skill as a **single-PR** invocation (§1 → §11), including
  gates, publish, and its own chat-style return summary.

Do not batch multiple PRs into one subagent. Do not review "a bit of each" on the
main thread while children run.

### 0.4 Wait and aggregate

Wait for all children (or until the host reports permanent failure). Collect from
each: `repo#pr`, pass, verdict (`APPROVED` / `CHANGES_REQUESTED` / `DEFERRED` /
`SKIPPED` / error), head sha7, findings counts, posted yes/no.

Main-thread chat output is an **aggregate table only** — one row per PR — plus any
spawn failures. Do not re-run the review on the main thread. Do not merge findings
across PRs into one GitHub artifact.

```
# Multi-PR review — N PRs

| PR | Pass | Verdict | Findings | Posted |
|---|---|---|---|---|
| owner/repo#12 | deep | CHANGES_REQUESTED | 1b · 2m | yes |
| owner/repo#15 | light | APPROVED | 0 | yes |
| owner/repo#18 | — | ERROR | — | no — spawn failed |
```

### 0.5 Child failure

| Situation | Action |
|---|---|
| one child fails / times out | mark that row ERROR; still wait for siblings; do not abort the batch |
| all children fail | report all errors; post nothing extra from the orchestrator |
| user cancels mid-batch | stop spawning new children; report completed rows |

Nested multi-PR inside a child is **forbidden**. If a child receives 2+ PRs by
mistake, it must refuse and return ERROR for that spawn.

---
