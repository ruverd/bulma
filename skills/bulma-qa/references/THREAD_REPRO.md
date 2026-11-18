# Direct QA reproduction

Answer selects a host-approved environment and plans from the current request
and thread evidence. The environment can be tied to a PR preview or a product
report without a PR. A PR case
requires the exact observed PR URL and an approved preview pinned to its current
head. The existing PR graph keeps its planning, verdict and publication rules.

The host configures the executor's JSON registry outside git. Each entry in
`targets` has an ID, `environment` label, `kind` (`local`, `dev`, or
`preview`), a base `url` with its approved origin, and a `checkout` root.
For a preview add `pr` and `head`.
An optional `auth_state` points at an already provisioned test session state
used only by the browser. Mark `isolated_data` after verifying the target's
app, API, identity provider, and data boundaries using [LOCAL_SETUP.md](LOCAL_SETUP.md).
Set `synthetic_evidence` only after verifying that
the cropped area contains shareable synthetic data. Inspection scopes, URLs,
selectors and auth paths are host-owned.

For new reports, define `surfaces` by ID. Each surface has a `label`, a
fixed `path` on the approved origin, and an `evidence_selector`. Its optional
`controls` maps IDs to a `label` and a trusted click `selector`. Approve
only controls whose effects are safe for the test identity and whose steps
stay on the same path. The published catalog contains labels and IDs.
Answer derives the ordered control IDs (at most eight) and the two distinct
visible assertions from the conversation. It requests one missing detail
when it cannot ground a complete plan. The host passes the plan through
standard input with `--plan-stdin`. The executor resolves and rechecks it
against the private registry. It stores a plan hash in the receipt to reject
a different plan for the same request. No arbitrary navigation, forms,
shell commands, selectors, scripts, or credentials can come from the plan.

Existing targets with no `surfaces` still use their configured `steps`,
`clicks`, `evidence_selector`, `bug_text` and `success_text`.

The executor claims the checkout's existing Bulma QA lease after older PR QA
work. While busy, the host keeps the request pending and retries. It records the
case plan, opens the approved origin in agent-browser, checks the asserted
outcome and captures a cropped PNG. It verifies the assertion in local OCR and
rejects recognizable sensitive content before clearing the artifact. It closes
the test browser and releases the lease on terminal outcomes.

Report `reproduced`, `not_reproduced` under those exact conditions, or
`blocked` with the concrete prerequisite. Deliver through the original thread.
Use a configured synthetic QA tenant or local app only. Authentication screens,
raw data, secrets, and uncleared images stay private. CI and automatic GitHub
publication are outside this entry point.
