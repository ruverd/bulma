# Node: request QA for human sign-off

**Verb:** collect behavioral proof through `bulma-qa`.
**When:** verify found a sign-off request without code fixes, or final patch
proof passed. This node does not execute browser QA itself.

## Handoff

1. Refresh PR head. Honor any explicit repository QA-provider policy. If it
   specifies an external provider, `qa_provider=external` means
   record the external QA handoff and pending sign-off, without a QA_REQUEST,
   slot claim or direct execution. Never claim evidence was produced.
2. Save `status=qa_requested`, `qa_sha`, request ID and `qa_status=pending`.
   Write `QA_REQUEST` from `lstm` to `qa` using
   [PROTOCOL.md](../../bulma-bus/PROTOCOL.md). Include PR URL, repo, branch,
   final SHA, job ID, `purpose: human-signoff` in the body, `signoff_path`
   contents, source comment IDs and every requested acceptance criterion.
   Include local origin, auth helper, fixture/role/tenant needs and known gaps.
   Request an AC → step → expected/actual → attached evidence matrix.
3. Bus switch to `qa`, loading
   [bulma-qa](../../bulma-qa/SKILL.md). Respect provider admission and single
   execute slot, including queueing. Never spawn `bulma_qa`. If the stack
   refuses a push, preserve its frames and report pending proof. A nested
   `developer → lstm → qa` cannot push triage at depth four; return the blocker
   rather than fabricating a verdict or abandoning live frames.
4. On `QA_RESULT`, resume here, not at execute. Match PR, request, job and
   `sha` to saved `qa_sha` and live HEAD. A changed head invalidates QA proof;
   re-verify affected comments and obtain fresh proof before reply.

## Apply result

Store `qa_status`, `qa_comment_url`, `qa_evidence_path` and returned SHA.
PASS requires a posted QA comment with working attachments and a completed
coverage matrix for every requested behavior. UI needs recorded walks plus
stills; endpoint-only needs HTTP stills. Unit/CI/logs alone do not satisfy it.
Coverage gaps, failed uploads, missing roles or unwalked requested cases leave
`signoff_status=pending`, even when QA otherwise reports PASS.

Complete visual PASS sets `signoff_status=evidence_ready`, then **reply**.
Link evidence on each requesting comment and in the summary. State that the
human's approval remains pending. Never impersonate a human, submit APPROVED
as that human, or dismiss/resolve a request for actual human approval merely
because automated QA passed. A request only for visual evidence can be
resolved once its requested proof is complete.

FAIL with triaged PR_BUG returns to **verify**, then the normal patch/prove
loop on the same branch. Charge the existing `prove_fix_loops` budget for
QA-driven fixes too; exhaustion escalates. Other bug classes follow QA's
triage mapping, but any unmet requested criterion keeps sign-off pending.
BLOCKED or PENDING_TRIAGE preserves evidence and the exact blocker; no success
reply or dismissal of the sign-off concern. Independent comments may still
receive truthful dispositions. Report pending work and resume when unblocked.
