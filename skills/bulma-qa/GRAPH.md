# QA graph

```
start (PR from args or QA_REQUEST)
  → admit            # one QA slot; else enqueue and stop
  → resolve
  → plan             # inventory + blast radius + happy + user-break
  → execute          # clips + HTTP stills; exploratory; append FINDINGS
  → gate
       ├ no findings / unambiguous FAIL → verdict
       └ any product suspicion          → request_triage
                                              │
                                       bus → triage
                                              │
                                       TRIAGE_RESULT
                                              │
                                           verdict
                                              │
                              QA_RESULT + pop + dequeue
```

## Edges

| From | Condition | To |
|---|---|---|
| start | no PR | **stop** (ask) |
| start | PR present | **admit** |
| admit | `qa_active` holds another **live** PR | **enqueue** and **stop** |
| admit | slot free, this job, or a claim that expired / was abandoned | **resolve** (claim, or take over and say so) |
| resolve | ok | **plan** |
| plan | PLAN.md gate (blast-radius, happy + user-break) | **execute** |
| plan | no route and no endpoint | **stop** (ask) |
| execute | plan finished, no findings, user-break walked | **verdict** (`PASS` or infra `BLOCKED`) |
| execute | plan finished, findings exist | **request_triage** |
| execute | unambiguous FAIL (VERDICTS.md) | **verdict** `FAIL` |
| execute | cannot run (env/auth/app) | **verdict** `BLOCKED` |
| request_triage | envelope written | **bus → triage** |
| verdict | after execute or TRIAGE_RESULT | comment + `QA_RESULT` + pop + apply_qa + **release lease** + **dequeue** |
| any | `blocked` / `handed_off` / `escalated` | **release lease** then stop (`../bulma-bus/JOBS.md`) |

Unambiguous FAIL: [references/VERDICTS.md](references/VERDICTS.md).  
Plan how: [references/PLAN.md](references/PLAN.md).  
Handoff body: [references/HANDOFF.md](references/HANDOFF.md).  
Execute how: [references/EXECUTION.md](references/EXECUTION.md).
Clips: [references/VIDEO.md](references/VIDEO.md).

## Nodes

`nodes/admit.md` · `nodes/resolve.md` · `nodes/plan.md` ·
`nodes/execute.md` · `nodes/request_triage.md` · `nodes/verdict.md`

Queue and lease: `../bulma-bus/JOBS.md`. Never two executes. The slot is a
lease with an expiry, so a dead run cannot park the queue for good.
