# Bulma feature delivery — graph

## Spine

Bundled primitives.

```
goal / resume
  → mcp_context
  → triage
       ├ scope=fullstack → fullstack (same branch, git worktrees; Orca optional) then this path per worker
       ├ full_feature → grill → spec → tickets → plan_critic → implement* → review → tester
       ├ debug_fix    → diagnose → one ticket → implement → review → tester
       └ light_change → tickets (single) → implement → review → tester
  → (more tickets? implement next)
  → evidence
  → blast (skip on light_change unless risk=elevated)
  → quality (thermo fix all)
  → shipper → ci_watch
```

After all tickets pass tester, **evidence**, then blast and/or quality.

`implement*` is one fresh coder subagent **per ticket**. Verify the
ticket before starting the next (bundled
`principle-sequence-verifiable-units`).

Grill, spec, and tickets run on the **main thread**. `plan_critic` is
main-thread too, except `risk=elevated` which spawns a read-only worker.
Implement / review / diagnose / tester / evidence / quality / shipper / ci
are nodes (subagents where the adapter says so).

## Edges

| From | Condition | To |
|---|---|---|
| start | resume with live STATE | current node (skip finished when invariants match) |
| start | fresh goal / ticket | **mcp_context** |
| mcp_context | mcp_gate=passed / passed_partial | **triage** |
| mcp_context | mcp_gate=failed | **STOP** + English error |
| triage | scope=fullstack | **fullstack** (FULLSTACK.md) |
| triage | path=full_feature | **grill** |
| triage | path=debug_fix | **diagnose** |
| triage | path=light_change | **tickets** (single) |
| triage | path unclear | DECIDE the narrower path; ASK only last-resort policy |
| grill | frontier empty | **spec** |
| grill | ungrillable | prototype, then DECIDE or ASK |
| grill | ASK in flight | `waiting_user` **stop** |
| spec | SPEC.md written | **tickets** |
| tickets | tickets written, seams decided, path=full_feature and risk≠low | **plan_critic** |
| tickets | tickets written, seams decided, else | **implement** (first unblocked ticket) |
| plan_critic | pass or skip | **implement** (first unblocked ticket) |
| plan_critic | revise + loops left | apply on main, **plan_critic** |
| plan_critic | revise + loops exhausted | DECIDE residuals; **implement** unless every path is a guess → **escalate** |
| diagnose | root cause + fix slice | **implement** (one ticket) |
| diagnose | this is a feature | re-route **grill** |
| diagnose | ASK needed | `waiting_user` |
| implement | DONE | **review** |
| implement | NEEDS_CONTEXT / BLOCKED | ASK or escalate |
| review | spec_verdict=fail or quality_verdict=fail + loops left | **implement** (same ticket) |
| review | either fail + loops exhausted | **escalate** |
| review | spec_verdict=pass and quality_verdict=pass | **tester** |
| tester | fail + loops left | **implement** |
| tester | fail + loops exhausted | **escalate** |
| tester | pass + more tickets | **implement** (next) |
| tester | pass + no more tickets | **evidence** |
| evidence | done + (not light_change or risk=elevated) | **blast** |
| evidence | done + light_change + risk≠elevated | **quality** |
| blast | done | **quality** |
| quality | ok | **shipper** |
| quality | blocked | **escalate** |
| shipper | PR created | **ci_watch** |
| shipper | `--no-pr` | `done_local` |
| ci_watch | all green | **done** |
| ci_watch | fail + loops left | **implement** (fix) → push → ci_watch |
| ci_watch | loops exhausted | **escalate** |
| plan/implement | missing contract or open blocker | **blocker_handler** |
| blocker_handler | blocker Done | resume implement |
| blocker_handler | blocker open | `waiting_blocker` → **end session** |
| any | user must decide | `waiting_user` **stop** |
| any | context/limit | **handoff** |
| triage | work_kind=spike | diagnose read-only → `done_report` |

## Defaults

```yaml
open_pr: true
thermo_nuclear: required_when_shipping
ci_green_required: true
ci_fix_loops: 5
review_fix_loops: 2
test_fix_loops: 2
plan_critic_loops: 1
tdd: required_for_behavior_change
subagents_on_implement: always
never_merge: true
stay_draft: true
chat_language: en  # user-facing messages; this file is English
voice: unslop
decide_by_default: true
ask_last_resort_only: true
architect_checkpoint: last_resort_only
```

## Skills

See [PSTACK.md](PSTACK.md). Grill is [GRILL.md](GRILL.md). Voice is [VOICE.md](VOICE.md).

## Anti-patterns

- Declaring **delivered** with CI red/pending
- full_feature on every small bug
- Main thread writing product code
- PR without thermo `fix all`
- Shipping without TDD evidence on behavior change
- Auto-merge
- Interviewing the user through the grill tree
- Pasting GRAPH.md, `why`, or the parent tool catalog into a worker
- Spawning plan_critic on debug_fix or light_change
- Spawning plan_critic on every full_feature (normal is main-thread)
