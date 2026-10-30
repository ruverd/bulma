# LSTM STATE

**Path:** `.bulma-lstm/STATE.md`

## status

```
init | resolving | rebasing | verifying | grilling | patching | proving | qa_requested | replying | waiting_user | done | escalated
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
| `dismissed_review_ids` | confirmed dismissals of fully proved change requests |
| `summary_url` | idempotent COMMENT summary for final SHA and analyzed IDs |
| `re_requested` | confirmed reviewer + fix SHA pairs |
| `pending_actions` | unconfirmed API operations, with errors |
| `review_ids` | comma list of review `databaseId` in this run |
| `processed_comment_ids` | inline comment ids that already have 👍 **and** a thread reply |
| `processed_review_ids` | review ids whose every in-scope comment is acked, plus 👍 on the review body |
| `groups` | path to groups.json; every fix comment belongs to exactly one cause group |
| `completed_groups` | group IDs with resulting tree/evidence; not proof of final acceptance |
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
| `signoff_required` | yes / no, including evidence-only review requests |
| `signoff_status` | pending / evidence_ready; never human approval |
| `signoff_path` | requests, source IDs and required ACs beside STATE |
| `qa_provider` | bulma / external, honoring explicit repository policy |
| `qa_request_id` / `qa_sha` | request identity and final head sent to QA |
| `qa_status` | pending / PASS / FAIL / BLOCKED / PENDING_TRIAGE |
| `qa_comment_url` / `qa_evidence_path` | published evidence and coverage matrix |
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
