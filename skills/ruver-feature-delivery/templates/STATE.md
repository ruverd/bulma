---
schema_version: 5
status: init
spec_path: ""
tickets_path: ""
current_ticket: ""
seams: ""
goal: ""
goal_source: ""
repo: ""
branch: ""
base_branch: main
started_at: ""
updated_at: ""
autonomy: smart
open_pr: true
tdd: required
chat_language: en
assignee: ""
reviewers: ""
reviewers_status: ""
work_kind: ""
path: ""
risk: ""
risk_reason: ""
scope: ""
route_confidence: ""
route_reason: ""
spec_verdict: pending
quality_verdict: pending
plan_critic_verdict: pending
plan_critic_loops: 1
plan_critic_loops_used: 0
tracker_id: ""
tracker_url: ""
tracker_branch: ""
tracker_context_path: ".ruver-feature-delivery/tracker-context.md"
mcp_gate: ""
mcp_gate_error: ""
fullstack_run_id: ""
worktrees_frontend: ""
worktrees_backend: ""
repos_frontend: ""
repos_backend: ""
forge: ""
tracker: ""
pkg: ""
typecheck_cmd: ""
test_cmd: ""
lint_cmd: ""
e2e_cmd: ""
qa_tool: ""
review_fix_loops: 2
review_fix_loops_used: 0
test_fix_loops: 2
test_fix_loops_used: 0
ci_fix_loops: 5
active_runtime: ""
decision_mode: ""
decision_confidence: ""
---

# Ruver feature delivery — state

## MCP gate

- **mcp_gate:** pending | passed | passed_partial | failed (enum: STATE.schema.md)
- **error:** (if failed — full message to the user, English)

## MCP sources

| source | critical | status | path / notes |
|--------|----------|--------|--------------|
| linear | | | |
| figma | | | |
| sentry | | | |
| notion | | | |
| other | | | |

Index: `.ruver-feature-delivery/mcp-sources.md`

## Tracker / repo (PRODUCT.md)

- **forge:** github | gitlab | git
- **tracker:** linear | github_issues | gitlab | jira | none
- **pkg / cmds:**
- **qa runner:** agent-browser | http | none
- **assignee / reviewers / reviewers_status:** (PRODUCT.md §6)
- **ID / URL:**
- **Branch:**
- **Context file:**

## Route (triage)

- **work_kind:** feature | bug | regression | chore | spike
- **scope:** frontend_only | backend_only | mono | fullstack
- **path:** full_feature | debug_fix | light_change
- **risk:** low | normal | elevated
- **risk_reason:**
- **confidence:**
- **reason:**

## Fullstack (if scope=fullstack)

- **branch (same both repos):**
- **run_id:**
- **backend worktree / task / PR:**
- **frontend worktree / task / PR:**

## Blockers / wait

- **blocker_status:** none | waiting_blocker | unblocked
- **blockers:**
  - id:
    role: api_contract | ticket | product
    draft_created:
    last_check:
- **advanced_while_waiting:**

## Debug (debug_fix path only)

- **Root cause:**
- **Evidence:**
- **Hypotheses tried:**
- **fix_slice:** (text for the coder)

## Done criteria

- [ ] (from spec / tickets)

## Spec

- **path:** `.ruver-feature-delivery/SPEC.md`

## Tickets

- **path:** `.ruver-feature-delivery/TICKETS.md`
- **current:**
- **seams:**

## Plan critic

- **plan_critic_verdict:** pending | skip | pass | revise
- **plan_critic_mode:** main | spawn | skip
- **findings:**
- **summary:**

## Decisions

<!--
- ISO | DECIDE|ASK
  - Choice:
  - Who: agent | user
  - Confidence:
  - Evidence:
  - Residual risk:
-->

## Question to the user (if waiting_user)

- **Question:**
- **Options:**
- **Answer:**

## TDD evidence

<!--
- behavior:
  - test:
  - red:
  - green:
-->

## Context whitelist notes

- Detect test/typecheck scripts in the repo.
- Prefer the neighbor feature's pattern.

## Files touched

## Review

- **spec_verdict:** pending | pass | fail
- **quality_verdict:** pending | pass | fail
- **Verdict:** pending (pass only if both pass)
- **Summary:**
- **Findings:**
- **TDD check:** pending

## Test / hard gate

- **Hard gate:** pending
- **Commands run:**
- **Summary:**

## Evidence

- **Before:** n/a | gist raw URL
- **After:**
- **Route / viewport:**
- **Fragment:** `.ruver-feature-delivery/pr-body-evidence.md`

## Blast radius

- **Safety fact:**
- **Proven:** no | yes (command)
- **Unproven:**
- **Summary:**

## Quality (thermo-nuclear)

- **Status:** pending | done | blocked
- **Mode:** fix all
- **Findings fixed:**
- **Remaining:**
- **Hard gate after:** pending
- **Summary:**

## Ship

- **Commit:** none
- **Pushed:** no
- **PR:** none
- **Summary for human (English):**

## CI (delivery)

- **ci.status:** pending | watching | fixing | green | escalated | skipped_no_pr
- **pr_url:**
- **fix_loops_used:** 0
- **checks_summary:**
- **delivered:** no   # yes only if green (or explicit skipped_no_pr)

## Handoff / continuity

- **handoff_ready:** no
- **from_runtime:**
- **to_runtime:**
- **handoff_path:** .ruver-feature-delivery/HANDOFF.md

## Escalations

## Lessons

## Run log
