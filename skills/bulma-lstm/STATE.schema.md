# LSTM STATE

**Path:** `.bulma-lstm/STATE.md`

## status

```
init | resolving | rebasing | verifying | grilling | patching | proving | replying | waiting_user | done | escalated
```

## Fields

| Field | Use |
|---|---|
| `pr_url` | target PR |
| `repo` | `owner/name` |
| `branch` | head ref |
| `sha` | head oid |
| `mergeable` | MERGEABLE / CONFLICTING / DIRTY / … |
| `ci` | green / red / pending / unknown |
| `review_ids` | comma list of review `databaseId` in this run |
| `processed_comment_ids` | inline comment ids that already have 👍 **and** a thread reply |
| `processed_review_ids` | review ids whose every in-scope comment is acked, plus 👍 on the review body |
| `dispositions` | `fix` / `skip` / `unclear` counts or path |
| `claim_true` | yes \| no \| unknown (per comment, in Dispositions table) |
| `fix_ok_here` | yes \| no \| na |
| `risk` | low \| normal \| elevated (per comment) |
| `conflict_fixed` | yes / no / n/a |
| `patched` | yes / no |
| `grill` | skipped / done / waiting |
| `coder_status` | DONE / NEEDS_CONTEXT / BLOCKED |
| `spec_verdict` | pending \| pass \| fail |
| `quality_verdict` | pending \| pass \| fail |
| `tester` | pending \| pass \| fail |
| `prove_fix_loops` / `prove_fix_loops_used` | remaining + used. Default 2 |
| `job_id` | bus JOBS id (`lstm-pr-N`) |
| `lane` | `foreground` \| `worker` |
| `worktree` | path if lane=worker |
| `worker_id` | spawn id if lane=worker |
| `waiting_user` | ASK text if stopped |

A comment is processed only when it has author 👍 **and** a thread
reply. A review is processed only when every in-scope comment on it
is in `processed_comment_ids` and the review body has 👍. A later
re-review (new ids) that restates old findings is still **new**.
