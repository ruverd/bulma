# Direct QA reproduction

Answer selects a host-approved case using the current request and thread evidence.
A case can be tied to a PR preview or a product report without a PR. A PR case
requires the exact observed PR URL and an approved preview pinned to its current
head. The existing PR graph keeps its planning, verdict and publication rules.

The host configures the executor's JSON registry outside git. Each entry in
`targets` has an ID, `environment` label, `kind` (`local`, `dev`, or
`preview`), an exact `url`, a `checkout` root, public `steps`, up to eight
trusted `clicks` selectors, an `evidence_selector`, and distinct visible
`bug_text` and `success_text` assertions. For a preview add `pr` and `head`.
An optional `auth_state` points at an already provisioned test session state
used only by the browser. Mark `isolated_data` after verifying the target's
app, API, identity provider, and data boundaries using [LOCAL_SETUP.md](LOCAL_SETUP.md).
Set `synthetic_evidence` only after verifying that
the cropped area contains shareable synthetic data. The registry is host-owned
and its URLs, selectors and auth paths are not supplied by the model.

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
