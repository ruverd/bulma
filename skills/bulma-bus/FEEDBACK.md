# Verified feedback to prevention

LSTM is a learning checkpoint, not evidence that every earlier stage failed.
Conflicts, false claims, preferences, changed requirements and requests for
evidence do not by themselves prove a defect. This contract supplements
[INSIGHTS.md](INSIGHTS.md); it does not change its human-only telemetry or use
its proximity marker as proof of a missed review.

## Assess

After LSTM verification, assess every confirmed defect, including verified
bot findings. Reviewer also assesses a confirmed external concern absent from
its earlier review. An unverified request for changes remains a candidate.
No new reproduction is required when current verification already supplies it.

For each cause, record:

- Source repo, PR, comment or review URL and ID, author type, original head,
  verified head, trigger, expected and actual behavior, evidence and severity.
- Category: confirmed defect, false claim, changed requirement, preference,
  conflict, evidence request, or unknown. Only confirmed defects can promote.
- Development, fd review, PR review and QA separately: `missed`, `caught`,
  `not_run`, `not_applicable` or `unknown`, with artifact/SHA for each claim.
  A miss needs evidence that this stage ran while the defect existed and
  covered the affected behavior. Missing logs mean unknown. Compare findings
  by cause, not just nearby lines or the latest marker after the human comment.
- Why prevention failed: missing rule, existing rule not applied, weak test,
  missing fixture, or unknown. Cite the existing instruction when one exists.
- Smallest useful prevention, affected stage(s), applicability by path/flow,
  destination, regression case and evidence still missing.

Store one assessment per source finding at
`$BULMA_REPO/feedback/<pattern-key>/<source-key>.md`, outside git. Resolve
`BULMA_REPO` through [bulma-memory](../bulma-memory/SKILL.md), shared across
worktrees. Use a short stable cause slug for `pattern-key`; source keys include
GitHub object kind and ID, e.g. `review-comment-123`. Collapse repeated comments
about the same defect on one PR when counting recurrence. Reuse existing keys
on resume; keep original evidence and append changed conclusions with SHA/date.
Serialize writes to shared assessments and memory through the coordinator.
If no safe serialization is available, keep a job-local pending assessment
beside STATE for later reconciliation, never overwrite another worker's work.

## Feed the next run

A confirmed, reusable lesson gets one scoped entry in project memory
`## Prevention`, with pattern key, affected stages, applicability, concrete
check and source evidence. Merge with an equivalent entry. Keep project facts
in `## Gotchas`; do not duplicate repo instructions. If a rule already exists,
record how its application or proof failed instead of adding the same rule.
Unknown cause or a one-off without reusable prevention stays assessment-only.

Coder receives matching `development` entries. Both fd review and PR review
receive matching `review` entries. QA receives matching `qa` entries and maps
them to behavioral steps. Entries guide investigation; a finding still needs
current evidence. They do not add acceptance criteria or override approval,
QA-provider or safety rules. A missing file means no extra input.

General skill changes go through a normal reviewed change. Do not rewrite
installed skills or global instructions during a product PR fix.

## Decide whether a task is useful

Draft a task only for a confirmed, reusable gap with a concrete change to a
named rule, prompt, test helper, fixture or gate and a regression case. It must
either recur on at least two distinct PRs, or have one demonstrated high-impact
case involving security, permissions, money, data loss or a blocked core flow.
An existing rule applied incorrectly qualifies only with evidence explaining
why the current flow failed to enforce it. More checklist text alone is not
an improvement. Already covered gaps get an existing task link; false claims,
nits and unknowns get no task. Task drafts do not mean prevention is delivered.

Write `issue.md` under the pattern directory, in English, containing:

- Problem, source links, affected heads, reproduction and stage attribution.
- Existing guard and precise gap; proposed change and destination files.
- Acceptance criteria: old flow misses the case, new flow detects/prevents it,
  plus a counterexample that must remain allowed.
- Validation commands or executable scenario, scope and follow-up measurement.
- Stable marker `<!-- bulma-feedback: <pattern-key> -->`.

Default is a local draft. Publish only with authorized issue creation and a
known destination. Project memory may record `feedback_issues: publish` and
`feedback_repo: owner/repo` when the user authorizes that policy. Bulma skill
gaps belong in the configured Bulma source repo; product-specific gaps belong
in the product repo. Never infer the Bulma repo from the product PR remote.
Without a destination/authorization, retain the draft and report it without
blocking the product fix or asking at each run.

Before publishing, search open and closed issues in the exact destination for
the marker and cause, and inspect matching issue bodies. Reuse an open issue;
do not add a comment without comment authorization. A closed issue requires
fresh post-fix evidence before drafting a new recurrence task. Save its URL
only after confirmation. On timeout, search for the marker before retrying.
Use structured tools or `gh issue create --body-file`, never inline shell text.

## Validate later

Assessment outcomes are `no_action`, `lesson_saved`, `task_draft`,
`task_linked` or `pending`, with a reason and artifact path/URL. Record delivery
version/SHA and regression evidence when the prevention change lands. On a
later matching change, check whether the affected stage used the prevention
and caught the case. Link recurrence to the same cause. No recurrence without
relevant runs is not proof of improvement. Use existing `lookback` for aggregate
trends; these assessments add verified attribution, not a replacement metric.

Feedback failures stay pending in the report. They never change a product
verdict, dismiss a concern, delay a reply or grant human sign-off.
