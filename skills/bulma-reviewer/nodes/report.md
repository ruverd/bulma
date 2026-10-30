# Node: report

**Verb:** close  
[../references/REPORT.md](../references/REPORT.md).
If the bus stack has a caller, write `REVIEW_RESULT` and pop.

After successful verdict publication, save the report outside the checkout.
Apply [JOBS.md review cleanup](../../bulma-bus/JOBS.md#review-cleanup).
The coordinator removes a worker's owned review checkout after that worker
exits; a foreground reviewer leaves its checkout first. Retain it when CI is
pending, publication failed, local files changed or ownership is uncertain.
Record the cleanup result in STATE and JOBS and include it in the report.

Include feedback outcomes from [FEEDBACK.md](../../bulma-bus/FEEDBACK.md):
confirmed gap and affected stage, prevention saved, draft path/existing issue
URL, or no action/pending with reason. Save assessment references outside the
checkout before cleanup. No task is required for an unverified concern.
