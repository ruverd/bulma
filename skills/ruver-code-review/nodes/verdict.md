# 6. Severity

| Tier | Meaning | Effect |
|---|---|---|
| **blocker** | proven defect, security flaw, broken contract, data loss; request body written into role, tenant, price, or flag/permission | REQUEST_CHANGES |
| **major** | closed list only: new logic without a test; swallowed error or silent catch or masking fallback; missing error or loading state on a new data flow; `any` or cast that erases a real check; documented repo rule broken; contract change leaving callers unhandled; a new special-case branch bolted onto an unrelated flow (concrete path and trigger); user input concatenated into SQL, HTML, shell, or href; broad catch, or `?.` skipping a required operation | REQUEST_CHANGES |
| **nit** | everything else, including the reviewer preferences below | collapsed Nits block, max 5, never blocks |

Introduced or worsened by this PR, and anchored to a changed path. Pre-existing
problems the PR merely touches are nits.

### Reviewer preferences — always nits

Personal standards, not repo rules. They are worth saying once and never worth
blocking a merge over. A preference stated in the repo's `CLAUDE.md` stops being a
preference and becomes a **major** under §6 instead.

- `it(...)` descriptions start with `should`
- names spelled out, not abbreviated — `knowledgeCheck`, never `kc`
- a file this PR pushed from under 1000 lines to 1000 or more
- at most one code-judo nit: name the layer, branch, or helper to delete
- new validation covered only by a happy-path test
- a comment this PR added or changed that contradicts the code, or only restates it
- a new nested ternary, or new nesting an early return would flatten
- a new optional-field bag that admits illegal combinations (no `as`/`!` in the diff)

A preference with no `path:line` in the diff is dropped, like any other nit.

## 7. Coverage — required before APPROVE

One row per changed file with what was verified. Silence is not evidence. A file
left unverified because of a cap is declared and forces **DEFER**, never APPROVE.

## 8. Verdict

Reaching this section means §3 passed, so CI is green — unless `--force` was used.

Carried findings that still reproduce (§4.2) count exactly like new ones. APPROVE
requires zero surviving findings, new **and** carried.

| Findings | Verdict |
|---|---|
| ≥1 blocker (new or carried) | **REQUEST_CHANGES** |
| ≥1 major (new or carried), 0 blocker | **REQUEST_CHANGES** |
| clean, full coverage, CI green | **APPROVE** |
| clean, full coverage, CI not green (`--force` run) | **DEFER** `reason=ci_red\|ci_pending\|ci_unknown`, marker keeps `pass=deep\|light` |
| clean, coverage incomplete | **DEFER** `reason=coverage` |
| blocker-level uncertainty | **DEFER** `reason=uncertainty` |
| empty diff, CI green | **APPROVE**, body says no code changes |

### 8.1 Promote

All must hold: SHA unchanged, prior artifact was a DEFER with `reason=ci*`, its
marker says **`pass=deep` or `pass=light`**, `blockers=0 majors=0`, `open=-`. Then
post APPROVE whose body links the earlier comment. First line: "I already
reviewed this SHA while CI was still running. Checks are green now, so this is
the approve." Marker keeps the prior `pass=` and adds `reason=promote`.

`pass=none` never promotes — that marker proves no code was read. Run a deep pass.
