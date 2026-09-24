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
  the diff needs). Read `AGENTS.md` only if `CLAUDE.md` is absent.
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
| 6. Contract & data | diff touches service, hook, type, endpoint, migration, schema | ✅ | ✅ |
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

New meaningful logic with no test is a **major**, `axis: tests`. Also: test
asserts a mock instead of behaviour, error path untested, `it` description
missing the `should` prefix (project rule), test disabled or skipped in the
diff. New validation covered only by a happy-path test is a **nit**.

A test in the diff that cannot fail counts as no test: setup or spy inside the
`try` it tests, an assertion no value can break (`>= 0`), a skip or env gate
that no CI workflow turns on, a spy with no assertion on its calls.

### Phase 5 — Correctness & regression (never skipped)

For each changed exported symbol, find who else uses it:

```
code_graph_explore  →  "<ChangedSymbol> <OtherSymbol> callers"
```

`code_graph_explore` is an Optional MCP capability
([bulma-host](../../bulma-host/SKILL.md)). Absent → `Grep` the symbol name,
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

A write that spans two stores, or an external provider and a local table: say
what state is left when the second step fails, and what a retry or an
at-least-once redelivery writes or emits again. An audit, event, or webhook
emit gated on input presence instead of rows actually changed fires on replay.

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
plus `CONTRIBUTING.md` or `CODING_STANDARDS.md` at the repo root if that file
exists. Quote the rule you are applying. A repo rule broken is a **major**; a
style preference not written down is a nit.

Structure checks also run here. They are not repo rules. No extra reads.

- **1k-line crossing (nit).** A changed file that is ≥1000 lines at HEAD and was
  <1000 before this PR. `before ≈ head_lines - additions + deletions` from the
  Read line count and that file's diff stats. Skip files you did not Read. Skip
  lockfiles and generated snapshots. Files already over 1k stay silent.
- **Bolted special-case.** A new `if`, flag, or nullable inserted into a flow
  that does not own the feature. **Major** only with a concrete path, the extra
  branch, and what happens. No path or no trigger → drop.
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
  "title": "Retry count keeps old value.",
  "trigger": "concrete condition — input, state, call order",
  "impact": "what the user or system observes",
  "fix": "one imperative sentence",
  "refutation": "strongest argument that this is not a bug, and why it fails"
}
```

Cut rules, biased toward refutation:

- no concrete `trigger` → **drop in silence**
- no `axis` → **drop in silence**
- `refutation` holds → **drop in silence**
- depends on behaviour outside this repo (api-v2 contract, flag, production data)
  → move to `uncertainties`
- an uncertainty causes DEFER **only** if, were it true, it would be a blocker.
  Uncertainty about a major or a nit disappears.

Write the survivors to `$BULMA_ROOT/.bulma-code-review/findings.json`. Then:

```bash
python3 scripts/bind-findings.py \
  --patch "$BULMA_ROOT/.bulma-code-review/PATCH.diff" \
  --findings "$BULMA_ROOT/.bulma-code-review/findings.json" \
  --allow-path <each §4.2 carry-forward file>
```

`scripts/` sits next to this skill's `SKILL.md`. Replace the ledger with
`kept`. Count `dropped` for chat. Do not mention dropped findings on the PR.

Then [critic.md](critic.md), then [verdict.md](verdict.md).
