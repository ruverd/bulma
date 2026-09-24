# Developer graph

```
              start  (ARGS.md: goal | ticket | resume | fix)
                │
        ┌───────┴────────┐
        ▼                ▼
     resume            admit
   (STATE on disk)        │
        │          ┌──────┴────────┐
        │          ▼               ▼
        │     goal / ticket   QA_RESULT FAIL+PR_BUG
        │          │               │
        └────┬─────┘               │
             ▼                     ▼
          deliver                 fix
     (bulma-feature-delivery) (existing PR)
        │                │
        └───────┬────────┘
                ▼
            mergeable
                │
           ok   │   not MERGEABLE
                │        │
                ▼        ▼
           bot_review   resolve branch / escalate
                │
      skip/pass │   loops left / exhausted
                │        │
                ▼        ▼
           request_qa   wait/lstm / escalate
                │
      enqueue-or-start QA
                │
           QA_RESULT
                │
        ┌───────┼────────────┐
        ▼       ▼            ▼
      PASS   FAIL+PR_BUG   other
        │       │            │
   ready+done  fix ──┘    done_notes / escalate
```

## Edges

| From | Condition | To |
|---|---|---|
| start | `resume` / same tracker id or goal slug with live STATE | **resume** (reconcile, continue) |
| start | goal text, or tracker id / URL, no live STATE | **admit** |
| start | `QA_RESULT` FAIL + `PR_BUG` | **admit** then **fix** |
| start | empty args and live STATE | **resume** |
| start | no args, no STATE, no goal | **stop** (ask for the ticket or the goal) |
| admit | idle main | **deliver** or **fix** |
| admit | busy main | worker + worktree; **stop** this call |
| resume | delivery not done | **deliver** (skip finished when invariants match) |
| resume | delivery done, bot_review in flight | **bot_review** |
| resume | delivery done | **mergeable** or **apply_qa** as STATE says |
| deliver | fd `status=done` (CI green) | **mergeable** |
| deliver | escalated / waiting_user / handed_off / waiting_blocker | **stop** |
| fix | pushed to same PR | **mergeable** |
| mergeable | MERGEABLE + CI green | **bot_review** |
| mergeable | conflict / dirty | fix branch → mergeable |
| bot_review | no bot detected, or skip/pass | **request_qa** |
| bot_review | waiting for a bot review on head SHA | **wait** (schedule_wake) |
| bot_review | unresolved bot threads, loops left | **lstm** |
| bot_review | `LSTM_RESULT` | wait for a bot review on the new head SHA |
| bot_review | loops exhausted | **escalate** |
| request_qa | QA slot free | **bus → qa** |
| request_qa | QA slot taken | enqueue; stay on developer |
| apply_qa | `QA_RESULT` PASS | **ready** (`gh pr ready`) then **done** |
| apply_qa | FAIL + `PR_BUG` + loops left | **fix** (log the lap first) |
| apply_qa | FAIL + `PR_BUG` + same finding id as a previous lap | **escalate** (the fix is not converging) |
| apply_qa | FAIL + `PR_BUG` + loops exhausted | **escalate**, cite `qa_verdict_log` |
| apply_qa | NEW_BUG / EXISTING_BUG / NOT_A_BUG | **ready** + **done** (notes) |
| apply_qa | `PENDING_TRIAGE` | **wait** |
| apply_qa | BLOCKED | **escalate** |

## Node files

`nodes/resume.md` · `nodes/admit.md` · `nodes/deliver.md` · `nodes/fix.md` ·
`nodes/mergeable.md` · `nodes/bot_review.md` · `nodes/request_qa.md` ·
`nodes/apply_qa.md`

## Defaults

```yaml
never_merge: true
stay_draft: until_qa_pass
qa_fix_loops: 2   # laps of QA→fix→QA. A lap costs a full QA plus a triage
                  # plus a fix, so this is smaller than fd ci_fix_loops: 5
review_bot_loops: 3
review_bot_min_score: 5
open_pr: true
reuse_fd_graph: true
chat_language: en  # default; bulma-memory overrides. This file is English.
voice: unslop
decide_by_default: true
ask_last_resort_only: true
```
