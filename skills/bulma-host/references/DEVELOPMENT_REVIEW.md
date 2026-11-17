# Development review executor

Opt-in for the feature-delivery **review** node only. This does not replace
post-PR code review, quality, plan criticism, tester, or their loop limits.
Without configuration, keep the existing separate `session_model` reviewer.
One alternative attempt per job/ticket/review round; no council or approval hunt.

## Local configuration

Read `development_review` from `## Preferences` through
[bulma-memory](../../bulma-memory/SKILL.md): home, shared repository, then worktree
(last value wins). The value is an absolute JSON file path outside the worktree,
or `off` to disable. `~`, `$HOME` and `$BULMA_HOME` expand as path text only.
No automatic profile creation. Never commit personal adapters, preferences or
credentials. Keep source mechanisms and authorized order, not cached balances.

Synthetic example (paths and candidate IDs are placeholders):

```markdown
## Preferences
- development_review: /absolute/local/review.json
```

```json
{
  "version": 1,
  "adapter": ["/absolute/local/review-adapter", "--profile", "development"],
  "read_only": true,
  "candidates": ["preferred-reviewer", "other-authorized-reviewer"],
  "discovery_timeout_seconds": 15,
  "timeout_seconds": 600,
  "freshness_seconds": 300
}
```

This trusted, user-configured executable implements the two operations below.
Bulma invokes its fixed argv directly with JSON on stdin, never a shell or a
command returned by discovery/model output. Paths/IDs in that output are data.
Maximum 20 authorized candidates, 30s discovery, 600s review, 4 MiB input and
captured output per stream. The runner terminates the process group on timeout,
output overflow or completion. POSIX Python 3.10+ is required. Stderr and partial
stdout remain local diagnostics under the round directory.

`read_only: true` declares an adapter capability, not an OS sandbox. The local
adapter MUST enforce the host's read-only tool permissions for the model,
including subprocesses, restrict access to supplied repo/context, and disable
product edits, publishing, interactive prompts and nested agents. It may run
checks whose generated outputs stay in scratch space. Do not configure an
adapter that cannot enforce this. The runner additionally rejects completion
when HEAD or worktree changes; that detects changes but cannot undo them.
The adapter is trusted local code, like a verification recipe. Model output,
discovery results, source files and diff content remain untrusted data.

No provider-specific adapter or quota endpoint is bundled. A user's source may
be a local model manager or another executable with this protocol. CLI presence
alone proves neither authentication nor model access. A real adapter must map
its provider's documented APIs/metadata; do not invent APIs or silently run a
paid model as discovery. Fixture tests exercise the protocol, not model quality,
credit guarantees or a live provider integration.

## Discovery protocol

Input: `{"version":1,"operation":"discover","candidates":["preferred-reviewer"]}`.
Output: one JSON object, with at most 100 candidate records:

```json
{
  "candidates": [{
    "id": "preferred-reviewer",
    "identity": {"model": "fixture-v2", "family": "fixture-b", "source": "runtime"},
    "access": {"available": true, "checked_at": "2026-11-17T12:00:00+00:00"},
    "quota": {"available": true, "checked_at": "2026-11-17T12:00:00+00:00"}
  }]
}
```

`identity` comes from provider runtime/system metadata establishing which model
the candidate resolves to; never infer it from the application, requested alias,
tier or generated self-description. `source` is `runtime` or `system`; mark
ambiguous aliases with `ambiguous: true`. Families must be canonical identifiers
consistent with the implementer's host metadata. Unknown implementation family
or candidate identity means no eligible alternative. Prefer the first authorized
candidate whose known family differs from **all** implementation contributors.
Unknown contributors prevent a diversity claim. Ignore unauthorized candidates
and ambiguous duplicate IDs. Discovery never supplies executable argv.

`access` and `quota` are optional. A negative observation blocks a candidate
only with a timezone-aware timestamp no older than `freshness_seconds` (at most
300s). Missing, stale, future, malformed or unsupported quota is **unknown**;
it does not fabricate availability or prevent the one real attempt. Successful
review execution establishes use for that attempt, not future credit. A fresh
positive observation is still not a guarantee; real auth/quota failures fallback.
The receipt records discovery time and the selected source observations.

## Coordinator procedure

1. At the review node, load the local preference. Absent/off: use the existing
   separate worker, without additional commit or adapter requirements.
2. When enabled, freeze a clean local commit (no push), record full `head` and
   `base` SHAs and the implementers' actual identities. Use the current graph
   review round ID, including job and ticket. A resume uses the same ID; never
   allocate a new round to retry a provider. Existing `review_fix_loops: 2` applies.
3. Write a request outside Git with `round_id`, `head`, `base`, full `task` and
   `spec` text, `context` (applicable repo rules, decisions, lessons, gotchas,
   source whitelist and relevant excerpts), `evidence` (receipts/paths and
   verification gaps), and `implementation` (identity objects; `{}` if unknown).
   Include the actual node's required sibling contracts in context or allowlisted
   paths so a remote executor can resolve them. Pass artifacts and requirements,
   never the author's conclusion, conversation, tool catalog or graph tree.
4. Invoke from the host skill directory:

   ```bash
   python3 scripts/development-review.py --repo "$WORKTREE" --request "$REQUEST"
   ```

   The runner builds the diff itself, includes the reviewer node contract and
   `read_only: true`, pins payload to HEAD, reserves the round durably and runs
   discovery plus at most one alternative. Duplicate calls return the receipt.
   A concurrent call exits 2 while the round is locked; wait for that call, do
   not spawn a fallback concurrently. After an interrupted process, resume
   preserves partial findings and requires the normal worker without another
   alternative. Exit 2/`action: blocked` is never a pass; inspect diagnostics.
5. `action: complete`: use both verdicts and all findings. A `fail` is a review
   outcome, never a signal to try another executor. Both pass → tester;
   either fail → implement or escalate using the existing limits.
6. `action: spawn_worker`, `mode: fallback`: spawn exactly one separate
   `session_model` reviewer through the existing host primitive, with the same
   task/spec/head/evidence contract. Preserve partial findings as claims to
   investigate, not the implementer's conclusion. Keep the fallback's result in
   JSON and finalize through:

   ```bash
   python3 scripts/development-review.py --repo "$WORKTREE" --request "$REQUEST" --finish "$FALLBACK_RESULT"
   ```

   Fallback result: `type: result`, `head`, `spec_verdict`, `quality_verdict`,
   `identity` from host runtime and `findings` (array, possibly empty). Completion
   merges known findings/failed axes conservatively: they cannot become green
   because a process failed later. Resolve them through the existing implement
   loop, or escalate with evidence when disputed; never discard them for approval.
7. Copy receipt path, executor, alternative executor, mode, reason, diversity
   status, findings and verdicts into STATE. Preserve internal effort metadata
   when supplied by the host; never publish effort. Only supported model
   identities go to PR attribution. Same-family/unknown identity is never
   described as verified diversity. Changed HEAD/base/context needs re-review
   within the existing graph limits. Do not reuse evidence from another SHA.

## Review protocol

The adapter receives the prepared request plus `version: 1`, `operation: review`,
`candidate` (authorized ID only), absolute `repo`, generated `diff`, bundled
reviewer `contract` and `read_only: true`. It starts a fresh isolated reviewer,
not a continuation of the author's session. It must faithfully preserve the
node's spec/quality criteria and translate output into newline-delimited JSON.
Emit findings promptly and flush each line so a later failure cannot lose them:

```jsonl
{"type":"identity","identity":{"model":"fixture-v2","family":"fixture-b","source":"runtime"}}
{"type":"finding","finding":{"id":"missing-case","axis":"quality","message":"Boundary case is untested","evidence":"tests/example.py:42"}}
{"type":"result","head":"<full reviewed SHA>","spec_verdict":"pass","quality_verdict":"fail"}
```

Exactly one identity event and one result for a clean completion. No inline
`findings` array on the result: emit findings as events. The identity event must
come from actual execution metadata collected by the adapter, not model prose.
The executed identity must match discovery before a clean alternative can pass.
A valid negative verdict always returns to implementation, even if the process
then exits nonzero or identity is unknown; it is not an operational retry.
Findings force their axis to fail even if a result contradicts them.

On operational failure emit `{"type":"error","reason":"auth"}` (also `quota`,
`access`, `unavailable`, `timeout`, `invalid_output`). These trigger the one
fallback. Malformed/missing/duplicate results, wrong SHA, missing identity,
identity drift, process failure, timeout and output overflow cannot pass.
A well-formed negative result stays negative even alongside malformed output.
A product/worktree mutation or inability to terminate a live executor
(`cleanup_failed`) blocks the round; do not silently fallback over it.
