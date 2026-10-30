# 5. Phases

Run in order. Do not begin a phase before the previous one is complete.
§4.0–§4.1 (patches, file list, risk) are already done. Product-file Reads
are not.

Correctness, Standards, and Self-verify are **never** skippable. "Diff is
large" is not a valid reason to skip an axis — it reduces files read, which
the Coverage block must declare.

### Phase 1 — Spec (before any product-file Read)

Do not Read product files in this phase.

- Repo conventions: `CLAUDE.md` at the repo root (deep only; light reuses what
  the diff needs). Read `AGENTS.md` only if `CLAUDE.md` is absent. Also read
  `REVIEW.md` at the repo root, and in the nearest parent directory of each
  changed path, when one exists. Code owners write it to say what failure
  looks like in their area and what to skip. It outranks the defaults in
  this skill, but not the invariants.
- Project gotchas: the `## Gotchas` lines in project memory
  ([bulma-memory](../../bulma-memory/SKILL.md)) whose path glob or keyword
  matches `FILES.txt` or the patch. They are domain facts (units, ids,
  provider quirks) that the code alone does not show. Treat each as a lead:
  a finding still needs the trigger in this diff, never the note alone.
- Verified prevention: matching project memory `## Prevention` entries for
  `review`, per [FEEDBACK.md](../../bulma-bus/FEEDBACK.md). Map each to an
  applicable check and record evidence or why it does not apply. A lesson is
  a lead; findings still require the trigger in the current diff.
- PR title and body: stated intent and acceptance criteria.
- Tracker ticket: extract `[A-Z][A-Z0-9]+-\d+` from `headRefName` or title. If
  found, one `tracker_fetch_issue` call
  ([bulma-host](../../bulma-host/SKILL.md), Optional MCP). If the capability is
  absent or no ID exists, continue on the PR body alone.

Write `$BULMA_ROOT/.bulma-code-review/AC.md` before any product-file Read:

- one `- [ ]` bullet per acceptance criterion from the ticket, else the PR body
- if neither has criteria, the file is the single line `none`

Then run [fetch.md](fetch.md) §4.2 (carry-forward) and §4.3 (product-file Read).
Then Phase 2.

### Phase 2 — Plan

Pick axes from the table below by diff shape. In chat, one short line before
you review: which axes you are running, which you skipped and why.

| Axis | Runs when | Deep | Light |
|---|---|---|---|
| 3. Requirements | ticket or AC exists | ✅ | only if new diff touches AC surface |
| 4. Tests | diff adds logic | ✅ | ✅ |
| 6. Contract & data | diff touches service, hook, type, endpoint, migration, schema, or a UI API consumer | ✅ | ✅ |
| 7. Security & permissions | diff touches auth, RBAC, token, storage, user input, URL, upload, impersonation, SQL, `$queryRaw` | ✅ | ✅ |
| 9. Perf | diff touches list, render path, query, effect, loop | ✅ | only if new diff is exactly that |
| 9b. Accessibility | diff touches `tsx`, `jsx`, `vue`, `svelte`, `css`, `html` | ✅ | only if new diff is exactly that |
| 9c. Dependencies | diff touches `package.json`, a lockfile, `go.mod`, `Cargo.lock`, `pyproject.toml`, `Gemfile` | ✅ | ✅ |

### Phase 3 — Requirements

Map each `AC.md` bullet to code in the diff. Rewrite `AC.md` as:

```
- done | <criterion>
- partial | <criterion>
- missing | <criterion>
```

`missing` or a behaviour added beyond the ticket that changes existing flows:
finding, `axis: spec`. Wording mismatches are nits — silent.
`AC.md` of `none` → skip this phase as the table above.

### Phase 4 — Tests

Run **before** correctness. Tests state what the PR claims to do.

Apply [EVIDENCE.md](../references/EVIDENCE.md), Tests that distinguish the
defect. Trace assertions to production code, inspect weakened tests and record
whether a regression comparison actually ran. Use isolated execution for
local checks. Static inspection is not a runtime reproduction.

New meaningful logic with no test is a **major**, `axis: tests`. Also: test
asserts a mock instead of behaviour, error path untested, `it` description
missing the `should` prefix (project rule), test disabled or skipped in the
diff. New validation covered only by a happy-path test is a **nit**.

A test in the diff that cannot fail counts as no test: setup or spy inside the
`try` it tests, an assertion no value can break (`>= 0`), a skip or env gate
that no CI workflow turns on, a spy with no assertion on its calls.

### Phase 5 — Correctness & regression (never skipped)

For each changed exported symbol, find importers, callers and tests one hop
outside the diff, even when tests in the diff pass. For changed API consumers,
read the provider/serializer or shared client wrapper too. Use existing caps;
if a required hop cannot be checked, declare incomplete coverage and DEFER.
For config or workflow changes without exports, search for scripts/tests that
assert the changed keys, action names or paths. A checkout-action replacement
can break a security guard test outside the workflow diff.

A break that surfaces in a file this PR did not change still counts. A test
in an unchanged test file that now fails, a caller that now crashes, a type
error in an untouched importer: record it at the file where it surfaces
(`path`/`line`) and point `cause_path`/`cause_line` at the changed hunk that
causes it. Check CI test output for failures outside `FILES.txt` too.

```
code_graph_explore  →  "<ChangedSymbol> <OtherSymbol> callers"
```

`code_graph_explore` is an Optional MCP capability
([bulma-host](../../bulma-host/SKILL.md)). Absent → use the host Trail Code adapter when a fresh map exists; otherwise
`Grep` the symbol name,
same cap. Then check (`axis: correctness`):

- signature, prop, return-shape or enum change that its callers do not handle
- a public export that callers outside the diff still use, with no migration
  in this PR
- this write, cache invalidation, or subscription now runs on a path other
  features share
- null / undefined reaching a call that assumes a value
- state that is not reset between runs (retry, pagination, wizard step, filters)
- stale closure or missing dependency in `useEffect`, `useCallback`, `useMemo`
- React Query: wrong or missing key member, mutation without invalidation,
  missing `enabled` guard on a dependent query
- async ordering: unawaited promise, race between two writes, unmounted-component
  update
- early return that skips required cleanup or a required write
- off-by-one and empty-collection paths in new logic
- broad `catch` (`Error`, `unknown`, or untyped) that can hide an unexpected failure
- `?.` skipping an operation that must run
- a guard, fix, header, or registry entry this PR adds on one path while a
  sibling in the same file or module still lacks it: another commit path
  (autosave, navigate-away), another `CASE` arm, the bulk branch of a
  single-item handler, a second registry of the same ids, the inverse
  operation. The finding names the sibling `path:line`

### Phase 6 — Contract & data

`axis: contract`. Request and response shape versus the type, error branch
handled, pagination and default values, nullable field treated as required,
migration reversibility and backfill, id or tenant scoping on every query that
touches shared tables. User input reaching a typed column (uuid, int, enum)
with no format check, so a bad value is a 500 instead of a 400 or 404.

Trace provider → client wrapper → consumer and compare test mocks with that
actual wire shape. For `{ success, data }`, identify exactly where the envelope
is unwrapped. A mock returning a bare array cannot prove a consumer handles the
real envelope. Read neighboring contract tests even if this diff has tests.
Record the paths and shapes checked in Coverage. An unavailable external
contract that could crash the feature is a blocker-level uncertainty.

A write that spans two stores, or an external provider and a local table: say
what state is left when the second step fails, and what a retry or an
at-least-once redelivery writes or emits again. An audit, event, or webhook
emit gated on input presence instead of rows actually changed fires on replay.

When compatibility depends on another deployment, apply
[EVIDENCE.md](../references/EVIDENCE.md), Paired changes and rollout. Check
intermediate version combinations, merge/deploy order, flags and rollback.
Keep counterpart evidence and unavailable contracts in Coverage. Use existing
read/query caps; required evidence left unchecked means incomplete coverage.

Spreading the request body into a write is mass assignment. **Blocker** if that
can set role, tenant, price, or a flag/permission. Otherwise drop.

New or changed types only: an optional-field bag that admits illegal combinations
(e.g. `{ done?: boolean; doneAt?: Date }`) is a **nit**. **Major** only if the
same diff already uses `as` or `!` to paper over it. Skip when the diff does not
create or change a type.

### Phase 7 — Security & permissions

`axis: security`. Permission checked on the actual action rather than only in
the UI, token or secret in logs or query strings, user input concatenated into
SQL (`$queryRaw`, string-built query), HTML, shell, or href, redirect target
validated, object ownership verified before read or write, PII in analytics or
Sentry payloads. User-controlled URL fetched by the server (SSRF), user path
concatenated onto a filesystem root, cookie-auth state change with no CSRF
token. String-built SQL/HTML/shell/href with user input is a **major**. A proven
exploit with a concrete trigger stays a **blocker**.

### Phase 8 — Standards (never skipped)

`axis: standards`. Only rules written in the repo's `CLAUDE.md` / `AGENTS.md`,
`REVIEW.md`, plus `CONTRIBUTING.md` or `CODING_STANDARDS.md` at the repo root
if that file exists. Quote the rule you are applying. A repo rule broken is a
**major**; a style preference not written down is a nit.

Never ask for a release-notes or root changelog entry, and never treat a
missing one as a finding, unless one of those rule files requires it. A
package's own changelog is the author's call.

Structure checks also run here. They are not repo rules. No extra reads.

- **1k-line crossing (nit).** A changed file that is ≥1000 lines at HEAD and was
  <1000 before this PR. `before ≈ head_lines - additions + deletions` from the
  Read line count and that file's diff stats. Skip files you did not Read. Skip
  lockfiles and generated snapshots. Files already over 1k stay silent.
- **Bolted special-case.** A new `if`, flag, or nullable inserted into a flow
  that does not own the feature. **Major** only with a concrete path, the extra
  branch, and what happens. No path or no trigger → drop.
- **Reuse (major).** A function, hook, component, query, client or mapper this
  PR adds that does the same job as one the repo already has. Search each new
  exported or module-level symbol by its name and by its core verb and noun
  (`formatDate`, `fetchUser`, `uuid`), within the caller-query cap; light
  passes search only symbols the delta adds. **Major** only with the existing
  `path:line` and the same inputs and outputs. A similar name with a
  different contract is not a finding.
- **Code judo (nit, max 1).** A visible way to delete a layer, branch, or helper
  without changing behaviour. Name what to delete. No concrete deletion → drop.
  Does not block. At most one per run.
- **Nested ternary / deep nesting (nit).** A new nested ternary, or new nesting
  that an early return would flatten. Skip pre-existing nesting the PR only
  touches.
- **Lying or slop comments (nit).** A comment this PR added or changed that
  contradicts the code, or only restates it. Do not ask for new comments.

### Phase 9 — Perf, accessibility, dependencies

**Perf** (`axis: perf`). Only concrete and reachable: unbounded query or list
render, work in a render body, N+1 request in a loop, a new effect that
refetches on every render. Anything requiring a benchmark to prove is a nit.

**Accessibility** (`axis: a11y`). Skip unless the plan table says it runs. No
extra Reads. A new control the user must operate with no accessible name
(icon-only button, input without label) is a **major** with a concrete
element. Keyboard-unreachable click target, missing focus, form error not
tied to the field: same bar. Contrast or "could use aria" without a trigger
is a nit or drop.

**Dependencies** (`axis: deps`). Skip unless a manifest or lockfile is in
`FILES.txt`. No extra Reads. A new direct dependency with no caller in this
diff is a **nit**. A lockfile hunk that cannot be explained by the
`package.json` (or equivalent) change is a **major**.

### Phase 10 — Self-verify then bind (never skipped)

No new reading in this phase. Every surviving finding must carry all of:

```json
{
  "severity": "blocker | major",
  "axis": "spec | tests | correctness | contract | security | standards | perf | a11y | deps",
  "path": "src/x.ts",
  "line": 42,
  "in_diff": true,
  "cause_path": "src/x.ts (only when the defect surfaces outside the patch)",
  "cause_line": 40,
  "pre_existing": false,
  "title": "Retry count keeps old value.",
  "trigger": "concrete condition — input, state, call order",
  "impact": "what the user or system observes",
  "fix": "one imperative sentence",
  "refutation": "strongest argument that this is not a bug, and why it fails",
  "instances": ["src/z.ts:88", "src/w.ts:12"]
}
```

`instances` is optional. When the same defect appears in more than one place
(the same unchecked null, the same missing guard on sibling handlers), file
**one** finding at the first place, list the others there (max 10), and write
the fix for the pattern, not the line. One finding per class lets the author
fix every copy in one commit instead of one per review round. Search for the
copies with the same caps; do not post them as separate findings.

Cut rules, biased toward refutation:

- no concrete `trigger` → **drop in silence**
- a `trigger` that needs a chain of unlikely conditions nobody can reach from
  a real caller, user action or input today → **drop in silence**. Name the
  caller or input that produces it, or the finding is speculation. A fix for
  it costs a commit and a review round and protects nothing
- no `axis` → **drop in silence**
- `refutation` holds → **drop in silence**
- a defect in this diff that is reachable when a flag is on keeps its severity.
  A flag, a rollout plan or an external contract does not lower it
- only facts that genuinely cannot be checked from this repo, its linked
  counterparts or CI (an unavailable provider response, production data) go
  to `uncertainties`
- an uncertainty causes DEFER `reason=uncertainty` if, were it true, it would
  be a blocker, or a major on the `correctness`, `contract` or `security`
  axis. Uncertainty about a nit disappears
- a claim about pre-existing code the diff neither changed nor broke sets
  `pre_existing: true`; that is the only way a blocker or major leaves the
  ledger without a placement

Write the survivors to `$BULMA_ROOT/.bulma-code-review/findings.json`. Then:

```bash
python3 scripts/bind-findings.py \
  --patch "$BULMA_ROOT/.bulma-code-review/PATCH.diff" \
  --findings "$BULMA_ROOT/.bulma-code-review/findings.json" \
  --allow-path <each §4.2 carry-forward file>
```

`scripts/` sits next to this skill's `SKILL.md`. It prints
`{kept, body, dropped}` and exits 3 when a blocker or major sits in `body`, or
in `dropped` without `pre_existing: true`. Save the output as
`$BULMA_ROOT/.bulma-code-review/bound.json`; [publish.md](publish.md) passes it
to `gate.py` as the ledger.

`kept` become inline comments. `body` findings are introduced by this PR and
surface elsewhere; publish them in the body with their `path:line` and the
causal changed hunk. A blocker or major in `dropped` that is not pre-existing
needs its anchor or `cause_path` fixed and a re-run, never a silent drop.
Count actual drops for chat. A placement miss must never erase a
Critical/High and turn REQUEST_CHANGES into APPROVE.

Then [critic.md](critic.md), then [verdict.md](verdict.md).
