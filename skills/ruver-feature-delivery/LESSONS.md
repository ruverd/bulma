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
empty page. Test the empty, exact-page, and last-partial-page cases.

### authz / privilege

On any change to roles, permissions, or auth flows, check the caller's rank
against both the requested role and the target user's current role, on the
server. Fail closed on an unknown role or a failed lookup.
