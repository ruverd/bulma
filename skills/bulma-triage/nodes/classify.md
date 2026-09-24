# Node: classify

**Verb:** decide

One class **per finding**. Then one rollup on STATE + envelope
`classification` (drives the QA verdict for **this PR**):

| Priority | If any finding is… | Rollup |
|---|---|---|
| 1 | `PR_BUG` | `PR_BUG` |
| 2 | `BLOCKED` and none is `PR_BUG` | `BLOCKED` |
| 3 | `NEW_BUG` | `NEW_BUG` |
| 4 | `EXISTING_BUG` | `EXISTING_BUG` |
| 5 | all `NOT_A_BUG` | `NOT_A_BUG` |

Write the per-finding table into the envelope body:

```text
| id | class | linear | notes |
| F1 | PR_BUG | | in this PR's diff |
| F2 | NEW_BUG | ABC-123 | unrelated screen |
```

`NEW_BUG` only when the bug is real **and** not caused by this PR.
`EXISTING_BUG` when the tracker already tracks that underlying problem.
`PR_BUG` when this PR introduced or exposed it.
Do not invent product behavior — `BLOCKED` that finding.
