# Triage graph

```
start (TRIAGE_REQUEST or args)
  → receive          # validate PR link
  → inspect          # PR diff + tracker + each finding
  → reproduce
  → classify         # one class per finding; STATE = PR rollup
  → act
       ├ each NEW_BUG → tracker issue (LINEAR.md)
       ├ PR_BUG       → no ticket, no switch to developer
       └ EXISTING / NOT_A_BUG / BLOCKED → no new ticket
       └ always: TRIAGE_RESULT → pop (back to qa)
```

**PR_BUG order (do not skip QA verdict):**

1. Write `TRIAGE_RESULT` (`classification=PR_BUG` if any finding is).
2. Pop (back to qa).
3. QA verdict writes `QA_RESULT` FAIL and pops to developer.
4. Developer `apply_qa` sees FAIL+PR_BUG → **fix**.

Do **not** write `PR_BUG_FIX` here. Do **not** jump qa → developer.

## Nodes

`nodes/receive.md` · `nodes/inspect.md` · `nodes/reproduce.md` ·
`nodes/classify.md` · `nodes/act.md`
