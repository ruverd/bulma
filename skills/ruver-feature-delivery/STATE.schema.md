# STATE schema v5

**Path:** `$RUVER_ROOT/.ruver-feature-delivery/STATE.md`

## status

```
init | mcp | triage | grilling | waiting_user | speccing | ticketing |
diagnosing | implementing | reviewing | testing | blasting | quality |
shipping | ci_watching | waiting_blocker | handed_off | done | done_local |
done_report | escalated
```

- `waiting_user` — last-resort ASK in flight. Next message is the answer.
- `waiting_blocker` — external blocker open. Terminal for this session.
- `handed_off` — other runtime owns the run.
- `done` — PR + CI green. `done_local` — `--no-pr`. `done_report` — spike.

## mcp_gate

`pending | passed | passed_partial | failed`

## Fields

| Field | Use |
|---|---|
| `schema_version: 5` | resume compat. v4 resume: missing `risk` → `normal` |
| `work_kind` | feature \| bug \| regression \| chore \| spike |
| `path` | full_feature \| debug_fix \| light_change |
| `risk` | low \| normal \| elevated |
| `risk_reason` | one line, why this risk |
| `route_confidence` | high \| medium \| low |
| `route_reason` | one line, why this path |
| `scope` | frontend_only \| backend_only \| mono \| fullstack |
| `forge` | github \| gitlab \| git |
| `tracker` | linear \| github_issues \| gitlab \| jira \| none |
| `pkg` / `*_cmd` / `qa_tool` | from PRODUCT.md |
| `assignee` / `reviewers` / `reviewers_status` | PRODUCT.md §6. `confirmed` \| `proposed` \| `missing` |
| `chat_language` | from `ruver-memory` home file. Default `en` |
| `spec_path` | `$RUVER_ROOT/.ruver-feature-delivery/SPEC.md` |
| `tickets_path` | `$RUVER_ROOT/.ruver-feature-delivery/TICKETS.md` |
| `current_ticket` | |
| `seams` | confirmed in spec/tickets |
| `tracker_id` | |
| `pr_url` / `sha` | |
| `review_fix_loops` / `test_fix_loops` / `ci_fix_loops` | remaining + `*_used` |
| `spec_verdict` | pending \| pass \| fail |
| `quality_verdict` | pending \| pass \| fail |

## Whitelist per node

| Node | Reads | Writes |
|---|---|---|
| mcp_context | goal, refs, PRODUCT.md, ruver-memory | mcp_gate, forge, tracker, pkg, *_cmd, qa_tool, tracker_*, branch, repos_*, assignee, reviewers, reviewers_status, chat_language |
| triage | goal, tracker-context | work_kind, scope, path, risk, risk_reason, route_* |
| grill | goal, repo, tracker | decisions, approaches, `waiting_user` |
| spec | decisions | SPEC.md, spec_path |
| tickets | SPEC.md | TICKETS.md, seams, tickets_path |
| diagnose | sentry/linear, repo | debug (root cause, evidence, one ticket) |
| implement | one ticket + spec excerpt | code, tdd evidence, files_touched |
| review | spec, ticket, diff, gates.log | spec_verdict, quality_verdict, review |
| tester | files, scripts | hard gate + gates.log |
| evidence | qa_tool, pr_url, sha | fragment, before/after png paths |
| blast | diff | blast section |
| quality | diff, files | quality section |
| shipper | gates | ship, ci.status=pending |
| ci_watch | pr_url | ci.status |
| blocker_handler | blockers | blockers[], waiting_blocker |
| fullstack | scope, branch | worktrees, run_id, prs |
| handoff | full | handed_off |
| orchestrator | full | status, run_log |

Orchestrator owns `status` transitions. Nodes report `result`.

## Rules

- Decision log required before spec/tickets.
- `tdd: required` — reviewer/shipper refuse without evidence on behavior change.
- Exit codes in `.ruver-feature-delivery/gates.log`. Cite them. Do not retype from memory.
- No secrets in STATE.
