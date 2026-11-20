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
     done      fix ──┘    done_notes / escalate
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
| resume | `mode=stack` | **stack** (reconcile saved plan against GitHub and origin) |
| resume | delivery not done | **deliver** (skip finished when invariants match) |
| resume | delivery done, bot_review in flight | **bot_review** |
| resume | delivery done | **mergeable** or **apply_qa** as STATE says |
| stack | active child, CI green or verified out of scope with local proof | **mergeable** → **bot_review** |
| stack | active umbrella, CI green | **mergeable** → **bot_review** |
| stack | any child CI red + loops left | fresh fix worker for that child, re-check |
| stack | child loops exhausted | that child **escalated**; others continue |
| stack | child gates passed | wait for verified human merge, then **stack** for next row |
| stack | umbrella gates passed | **done** (report its current review status) |
| deliver | fd resolved or planned a stack ([STACKED.md](STACKED.md)) | **stack** on the foreground |
| deliver | fd `status=done` (CI green) | **mergeable** |
| deliver | escalated / waiting_user / handed_off / waiting_blocker | **stop** |
| fix | pushed to same PR | **mergeable** |
| mergeable | MERGEABLE + applicable CI gate passed | **bot_review** |
| mergeable | conflict / dirty | fix branch → mergeable |
| bot_review | stack child, no bot detected or skip/pass | **stack** (wait for verified human merge) |
| bot_review | single delivery or QA-enabled umbrella, no bot detected or skip/pass | **request_qa** |
| bot_review | waiting for a bot review on head SHA | **wait** (schedule_wake) |
| bot_review | unresolved bot threads, loops left | **lstm** |
| bot_review | `LSTM_RESULT` | wait for a bot review on the new head SHA |
| bot_review | loops exhausted | **escalate** |
| request_qa | QA slot free | **bus → qa** |
| request_qa | QA slot taken | enqueue; stay on developer |
| apply_qa | `QA_RESULT` PASS | **done** (stack row returns to **stack**) |
| apply_qa | FAIL + `PR_BUG` + loops left | **fix** (log the lap first) |
| apply_qa | FAIL + `PR_BUG` + same finding id as a previous lap | **escalate** (the fix is not converging) |
| apply_qa | FAIL + `PR_BUG` + loops exhausted | **escalate**, cite `qa_verdict_log` |
| apply_qa | NEW_BUG / EXISTING_BUG / NOT_A_BUG | **done** (notes) |
| apply_qa | `PENDING_TRIAGE` | **wait** |
| apply_qa | BLOCKED | **escalate** |

## Node files

`nodes/resume.md` · `nodes/admit.md` · `nodes/deliver.md` · `nodes/stack.md` · `nodes/fix.md` ·
`nodes/mergeable.md` · `nodes/bot_review.md` · `nodes/request_qa.md` ·
`nodes/apply_qa.md`

## Defaults

```yaml
never_merge: true
new_pr_status: ready_for_review
qa_fix_loops: 2   # laps of QA→fix→QA. A lap costs a full QA plus a triage
                  # plus a fix, so this is smaller than fd ci_fix_loops: 5
review_bot_loops: 3
review_bot_min_score: 5
open_pr: true
reuse_fd_graph: true
chat_language: en  # default; bulma-memory overrides. This file is English.
voice: kevin
decide_by_default: true
ask_last_resort_only: true
```
