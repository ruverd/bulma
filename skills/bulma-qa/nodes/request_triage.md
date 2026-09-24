# Node: request_triage

**Verb:** switch  
Envelope `TRIAGE_REQUEST` using [../references/HANDOFF.md](../references/HANDOFF.md).
Attach every `## F<n>` from `.bulma-qa/FINDINGS.md` (or `payload_path`
if huge). PR link required.

STATE: `status=triage_requested`, `qa=PENDING_TRIAGE`,
`findings_path=.bulma-qa/FINDINGS.md`.

Bus switch to `triage`. Do not spawn `bulma_triage`.
Do not post a PR comment yet.
