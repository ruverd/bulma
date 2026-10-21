# Lessons for the implementer

The coder applies these while writing the code, before any review. Each rule
comes from a defect class that human reviewers kept catching after our gates
passed (`/bulma lookback`, `lesson: implementer`). The fd reviewer checks the
same rules, so a violation fails `quality_verdict`.

Each `###` heading is a lookback cluster name, and `lessons.py` reads the
first paragraph under it. Rewording a rule is how a lookback proposal lands
here. Keep each rule to one imperative paragraph.

### sibling-path parity

Before calling a guard, fix, header, or registry entry done, find its siblings
and give them the same change: every commit path that reaches the same write
(manual save, autosave, navigate-away, step-back), every `CASE` or `switch` arm
that computes the same value, the bulk branch of a single-item handler, a
second registry or allowlist of the same ids, and the inverse operation
(assign/unassign, grant/revoke). Name the siblings you checked in the summary.

### test that cannot fail

Make every new test able to fail. Before GREEN, break the code on purpose and
watch the test go red. Set up mocks and spies outside the `try` under test.
Assert on values that a bug would change, not `>= 0` or "was called". Do not
add a skip or env gate unless a CI workflow turns it on.

### multi-store write / side effect

When one operation writes to two stores, or to an external provider and a
local table, decide and test what is left after the second step fails, and
what a retry or an at-least-once redelivery writes or emits again. Gate audit,
event, and webhook emits on rows actually changed, not on the input being
present. Emit after the commit, outside the `try` that rethrows.

### acceptance-criteria completeness

Map every acceptance criterion to code and a test before `DONE`. When a
criterion says "all" or lists an inventory, enumerate it from the source with
a search and compare. Do not rely on the ticket's own list. Report a criterion
you deferred as `DONE_WITH_CONCERNS` with the reason. Never drop it silently.

### effect lifecycle

Every effect, listener, subscription, timer, or in-flight request you start
gets its cleanup in the same change: unsubscribe, `removeEventListener`, abort,
and a cancelled flag checked before every side effect after an `await`, not
only before `setState`.

### pagination / unbounded

Give every new list query a limit and every new loop over pages an exit on an
empty page. Test the empty, exact-page, and last-partial-page cases. Never
query or call out once per item inside a loop on a request path; batch it, or
check the one row you need instead of reading the whole set.

### authz / privilege

On any change to roles, permissions, or auth flows, check the caller's rank
against both the requested role and the target user's current role, on the
server. Fail closed on an unknown role or a failed lookup. Every id the caller
sends (tenant, account, owner, parent) is checked against what the caller may
access before a read or a write; take the scope from the session, not the body.

### untested branch

Every branch this change adds gets a test for each side: an `if`, a `??` or
`||` default, a `catch`, an early return, a cap, a status or error mapping.
Make the mock return the failing value for the failing side. A test that only
walks the happy path leaves the new branch unproven.

### null / empty / boundary

For each input the change reads, try null, undefined, empty string, zero, an
empty list, a malformed value and one past the limit. Use `??` when zero or
empty is valid. Input a client can get wrong fails as a typed client error
(400, 404, 409), never as an unhandled 500.

### silent catch / no error report

Catch only the error you expect and can handle. Rethrow or report everything
else. Never turn a failure into an empty result or a success response
(`catch { return [] }`). A failure an operator must act on goes to the
project's error reporting, not only to a log line.

### reuse before adding

Before adding a helper, hook, query, client, mapper or component, search the
repo for one that does the same job, by name and by its core verb and noun.
Reuse or extend it. Add a new one only when the contract really differs, and
say why in the summary.

### check-then-act race

Do not read, decide, then write when two requests can interleave. Use a
unique constraint with an upsert or conflict clause, a conditional update, or
a lock, and test the duplicate or concurrent case.

### test wired into CI

A new test file proves nothing until a CI job runs it. Check the test runner's
include patterns, the CI workflow's paths and any allowlist, and name the job
that picks the file up. Never assert wall-clock timing or sleep for a fixed
time in a test.

### clean branch

Start from a fresh base: merge or rebase the base branch, search the tree for
conflict markers, and read what the merge changed in files you did not touch.
Commit only what the ticket needs: no build output, reports, scratch notes,
local paths or unrelated refactors.

