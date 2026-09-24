# Developer STATE

**Path:** `.bulma-developer/STATE.md`

## status

```
init | delivering | fixing | mergeable | qa_requested | applying_qa | waiting_user | done | done_notes | escalated | handed_off
```

## Fields

| Field | Use |
|---|---|
| `mode` | delivery \| fix |
| `goal` | user text; enough to start without a tracker |
| `fd_status` | mirror of fd graph if delivery |
| `pr_url` | draft PR |
| `sha` | head |
| `ci` | pending \| green \| red |
| `mergeable` | MERGEABLE \| … |
| `review_bot` | PRODUCT.md §9 login(s), empty means skip |
| `review_bot_loops` / `review_bot_loops_used` | remaining + used on bot threads. Default 3 |
| `loop_id` | host `schedule_wake` id while waiting for a bot review on head SHA |
| `qa_verdict` | after QA_RESULT (`PASS`/`FAIL`/`BLOCKED`) |
| `triage_class` | rollup from QA notes when present |
| `qa_fix_loops` / `qa_fix_loops_used` | remaining + used on the QA lap. Mirrors fd `ci_fix_loops` |
| `qa_verdict_log` | body table, one row per lap: lap, sha, verdict, triage_class, finding ids |
| `job_id` | bus JOBS id (`dev-<ticket>`) |
| `lane` | `foreground` \| `worker` |
| `worktree` | path if lane=worker |
| `worker_id` | spawn id if lane=worker |

Orchestrator writes `status`. Nodes write their section only.

## The QA lap is bounded

`apply_qa` FAIL+`PR_BUG` → `fix` → `mergeable` → `bot_review` → `request_qa` → QA → triage →
`apply_qa` is a ring across three graphs. fd bounds its own rings
(`review_fix_loops`, `test_fix_loops`, `ci_fix_loops`) but none of them reach
this one: mode `fix` patches the existing branch and never re-enters the fd
graph. So the cheapest rings in the system are capped and the most expensive
one — a full QA run plus a triage plus a fix — was not.

Two things make it fail to converge on its own. `qa.plan` replans from the
diff, and the diff changed, so each lap can surface a *different* finding and
look like progress. And `qa_verdict` is a single overwritten value, so lap 6
leaves a STATE identical to lap 1 — the loop is invisible even to a human
reading the file. `qa_verdict_log` exists to fix the second half.
