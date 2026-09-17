---
schema_version: 1
status: init
pr: ""
pr_url: ""
repo: ""
sha: ""
ci: ""
pass: ""
verdict: ""
defer_reason: ""
reviewed_shas: ""
loop_id: ""
risk: ""
critic: ""
caller: ruver-code-review
updated_at: ""
---

# Code review state

Fields and rules: [../STATE.schema.md](../STATE.schema.md).

`status`: `init` | `waiting_ci` | `reviewing` | `published` | `deferred` | `done`

## Passes

One row per pass, so the next one knows the carry-forward.

| SHA | pass | verdict | note |
|---|---|---|---|
