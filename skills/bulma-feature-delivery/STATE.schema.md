# STATE schema v5

**Path:** `$BULMA_ROOT/.bulma-feature-delivery/STATE.md`

## status

```
init | mcp | triage | grilling | waiting_user | speccing | ticketing |
critiquing | diagnosing | implementing | reviewing | testing | blasting | quality |
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
| `playbook` | Selected id from playbooks.json; missing on older runs selects once from recorded intent |
| `playbook_version` / `playbook_digest` | Frozen catalog version and selected contract digest; reconcile drift on resume |
| `verification_recipe` | Existing project-local recipe path, or empty; see bulma-host VERIFICATION.md |
| `path` | full_feature \| debug_fix \| light_change |
| `risk` | low \| normal \| elevated |
| `plan_mode` | compact or detailed; missing on resume means detailed |
| `quality_mode` | focused or deep; recomputed from actual diff; unknown means deep |
| `validated_tree` | tree identity shared by final review, tests and visual evidence |
| `risk_reason` | one line, why this risk |
| `route_confidence` | high \| medium \| low |
| `route_reason` | one line, why this path |
| `scope` | frontend_only \| backend_only \| mono \| fullstack |
| `forge` | github \| gitlab \| git |
| `tracker` | linear \| github_issues \| gitlab \| jira \| none |
| `pkg` / `*_cmd` / `qa_tool` | from PRODUCT.md |
| `assignee` / `reviewers` / `reviewers_status` | PRODUCT.md §6. `confirmed` \| `proposed` \| `missing` |
| `chat_language` | from `bulma-memory` home file. Default `en` |
| `spec_path` | SPEC.md in detailed mode; TICKETS.md in compact mode |
| `tickets_path` | `$BULMA_ROOT/.bulma-feature-delivery/TICKETS.md` |
| `current_ticket` | |
| `seams` | confirmed in spec/tickets |
| `tracker_id` | |
| `pr_url` / `sha` | |
| `review_fix_loops` / `test_fix_loops` / `ci_fix_loops` | remaining + `*_used` |
| `spec_verdict` | pending \| pass \| fail |
| `quality_verdict` | pending \| pass \| fail |
| `plan_critic_verdict` | pending \| skip \| pass \| revise |
| `plan_critic_mode` | main \| spawn \| skip |
| `second_opinion` | off \| ran \| failed |
| `plan_critic_loops` | remaining + `plan_critic_loops_used`. Default 1 |

## Whitelist per node

| Node | Reads | Writes |
|---|---|---|
| mcp_context | goal, refs, PRODUCT.md, bulma-memory | mcp_gate, forge, tracker, pkg, *_cmd, qa_tool, tracker_*, branch, repos_*, assignee, reviewers, reviewers_status, chat_language |
| triage | goal, tracker-context | work_kind, scope, path, risk, risk_reason, route_*, playbook, playbook_version, playbook_digest |
| grill | goal, repo, tracker | decisions, approaches, `waiting_user` |
| spec | decisions | SPEC.md, spec_path |
| tickets | SPEC.md | TICKETS.md, seams, tickets_path |
| plan_critic | SPEC.md, TICKETS.md, decisions | plan_critic_verdict, plan_critic section |
| diagnose | sentry/linear, repo | debug (root cause, evidence, one ticket) |
| implement | one ticket + spec excerpt | code, tdd evidence, files_touched |
| review | spec, ticket, diff, runtime receipts | spec_verdict, quality_verdict, review, reviewer_model, reviewer_effort |
| tester | files, scripts | hard gate, floor_guard, floor_allowed + runtime receipt paths |
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
It also owns the single `## Playbook` checklist. Rows come from playbook.py;
workers report evidence and the coordinator updates their rows. Required rows
cannot skip. Keep all historical baseline pointers when after evidence expires.

## Rules

- Decision log required before spec/tickets.
- `tdd: required` — reviewer/shipper refuse without evidence on behavior change.
- Cite recorded exit codes and receipt paths from
  [runtime evidence](../bulma-bus/PERFORMANCE.md), never from memory or a
  log-summary command's status.
- No secrets in STATE.
