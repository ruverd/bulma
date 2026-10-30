---
schema_version: 1
status: init
pr: ""
pr_url: ""
repo: ""
review_dir: ""
sha: ""
reviewed_sha: ""
base_sha: ""
review_context: unknown
human_signoff: ""
ci_evidence: ""
reviewer_model: "unknown"
reviewer_effort: "unknown"
ci: ""
pass: ""
verdict: ""
defer_reason: ""
reviewed_shas: ""
loop_id: ""
risk: ""
critic: ""
gate: ""
dismissed_approvals: ""
caller: bulma-code-review
updated_at: ""
---

# Code review state

Fields and rules: [../STATE.schema.md](../STATE.schema.md).

`status`: `init` | `waiting_ci` | `reviewing` | `published` | `deferred` | `done`

## Passes

One row per pass, so the next one knows the carry-forward.

| SHA | pass | verdict | note |
|---|---|---|---|
