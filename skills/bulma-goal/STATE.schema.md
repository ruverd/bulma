# Goal STATE

**Path:** `.bulma-goal/STATE.md`

## status

```
init | waiting_ci | waiting_qa | delivering | fixing | done | cancelled
```

## Fields

| Field | Use |
|---|---|
| `goal` | user text or ticket, enough to restart without the tracker |
| `tracker` | linear \| github_issues \| gitlab \| jira \| none |
| `tracker_id` | ticket id when there is one |
| `pr_url` / `repo` | the PR this loop watches. One loop per PR |
| `sha` | head SHA at the last inspect. The QA comment must match **this** |
| `loop_id` | host `schedule_wake` id. Present means a loop exists; do not create a second |
| `host_goal` | the completion sentence, if the host has a goal register |

## Last inspect

`ci`, `mergeable`, `qa_comment`, `video_url`: what `gh` actually returned on the
last wake, not what was expected.

## Rules

- The bar is a QA comment with evidence on the **head** SHA. A comment on an
  older SHA does not satisfy it.
- Never `gh pr checks --watch`. CI outlives the tool timeout, which is the
  reason this graph exists.
- Never merge.

Template: [templates/STATE.md](templates/STATE.md).
