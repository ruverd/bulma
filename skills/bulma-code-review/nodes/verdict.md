# 6. Severity

| Tier | Meaning | Effect |
|---|---|---|
| **blocker** | proven defect, security flaw, broken contract (a reachable caller crashes, writes wrong data or loses data), data loss; request body written into role, tenant, price, or flag/permission | REQUEST_CHANGES |
| **major** | closed list only: new logic without a test; swallowed error or silent catch or masking fallback; missing error or loading state on a new data flow; `any` or cast that erases a real check; documented repo rule broken; a new helper, hook, query or component that duplicates an existing one (existing `path:line` named, same inputs and outputs); contract change whose unhandled callers degrade without a crash or bad write (wrong empty state, missing field); a new special-case branch bolted onto an unrelated flow (concrete path and trigger); user input concatenated into SQL, HTML, shell, or href; broad catch, or `?.` skipping a required operation | REQUEST_CHANGES |
| **nit** | everything else, including the reviewer preferences below | collapsed Nits block, max 5, never blocks |

Introduced or worsened by this PR, wherever it surfaces. A break in an
unchanged caller or test counts when a changed hunk causes it (`cause_path`).
Pre-existing problems the PR merely touches are nits. A defect reachable when
a flag is on keeps its severity.

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

Always silent, not even a nit: a missing release-notes or root changelog entry
when no repo rule file requires one.

A preference with no `path:line` in the diff is dropped, like any other nit.

## 7. Coverage — required before APPROVE

One row per changed file with what was verified. Silence is not evidence. A file
left unverified because of a cap is declared and forces **DEFER**, never APPROVE.

## 8. Verdict

Refresh [PREFLIGHT.md](../references/PREFLIGHT.md). Reaching this section does
not prove that earlier CI or review-context evidence is still current.

Pending CI is checked before selecting a publication verdict, including REQUEST_CHANGES.

Apply [pass_decision.md](pass_decision.md) §Convergence first when this would
be my third or later REQUEST_CHANGES on the PR.

Carried findings that still reproduce (§4.2) count exactly like new ones. APPROVE
requires zero surviving findings, new **and** carried.

| Findings | Verdict |
|---|---|
| ≥1 blocker (new or carried) | **REQUEST_CHANGES** |
| ≥1 major (new or carried), 0 blocker | **REQUEST_CHANGES** |
| clean, another reviewer's change request is open | **COMMENT** `reason=review_pending`. Their review is pending. The diff was reviewed |
| clean, room unknown because a read failed | **COMMENT**. The read error stays in the private job report. Do not DEFER |
| head moved and delta not reviewed | re-review delta; if unable, **DEFER** `reason=head_changed` |
| clean, full coverage, room clear, CI proven on reviewed live head, or `out_of_scope` for the base | **APPROVE** |
| any findings, CI pending | retain completed analysis, **wait_ci**, no publication yet |
| clean, full coverage, CI red (`--force` run) | **DEFER** `reason=ci_red`, marker keeps `pass=deep\|light` |
| clean, full coverage, CI readable but unknown (`--force` run) | **DEFER** `reason=ci_unknown`, marker keeps `pass=deep\|light` |
| clean or not, CI unverified | code verdict, CI cell `not verified (tooling)`, marker keeps `pass=deep\|light`. No Deferred comment, never APPROVE |
| clean, coverage incomplete | **DEFER** `reason=coverage` |
| blocker-level, or correctness/contract/security major-level, uncertainty | **DEFER** `reason=uncertainty` |
| risk high, critic did not complete | **DEFER** `reason=critic_failed`, marker `critic=failed` |
| prior own REQUEST_CHANGES, or DEFER `coverage\|uncertainty\|critic_failed`, and this pass was not deep on the full diff | run the deep pass; never APPROVE from a light pass |
| empty delta after my own APPROVE, all approval gates above pass | **APPROVE**, body says no code changes |
| `gate.py` exits 1 | do not APPROVE. REQUEST_CHANGES if the ledger has a blocker or major; otherwise DEFER only for a real gate (draft, conflict, CI red, coverage, uncertainty). Do not dismiss my approval |
| `gate.py` exits 3 (only bot approvals on this head) | **COMMENT** review, same body, `reason=bot_quorum` |
| `gate.py` exits 4 (open change request) | **COMMENT**, `reason=review_pending` |
| `gate.py` exits 5 (CI or evidence unreadable) | **COMMENT**, CI cell `not verified (tooling)` when that line is present. Other lines stay in the private job report |

A sensitive-path list stays in STATE and the private job report. It does not
DEFER and it does not block APPROVE. An unresolved thread whose author approved
this head is a clear room, not `review_context`. A prior DEFER with
`reason=human_signoff`, `review_context`, or `review_context_unknown` is
withdrawn policy: do not skip on it. Never write `I did not inspect the diff`
when the diff was reviewed.

Dismiss my standing approval only when this pass posts REQUEST_CHANGES for a
code defect on a new head ([PREFLIGHT.md](../references/PREFLIGHT.md) §Retire my stale approval).
A DEFER or a blocked pass does not dismiss it.

Critical/High maps to blocker/major, including any such finding in our inline
comments or body. The final payload cannot contain those severities alongside
APPROVE. Body findings rejected only for inline placement still count.

### 8.1 Promote

All must hold: SHA unchanged, prior artifact was a DEFER with `reason=ci*` or a COMMENT with `reason=ci_unverified`, its
marker says **`pass=deep` or `pass=light`**, `blockers=0 majors=0`, `open=-`. Then
re-run every approval gate, including room and head-bound CI. CI that is
`out_of_scope` for the base counts as green here; the first line then says
"I already reviewed this SHA. CI does not run on PRs into `<base>`, so this is
the approve." Name the
sensitive-path list in the private job report. It does not block promotion.
Older markers without preflight/one-hop evidence require a fresh deep pass.
Promotion reads no diff, so write `bound.json` as
`{"kept":[],"body":[],"dropped":[]}` from that clean marker for `gate.py`.
Only then post APPROVE whose body links the earlier comment. First line: "I already
reviewed this SHA while CI was still running. Checks are green now, so this is
the approve." Marker keeps the prior `pass=` and adds `reason=promote`.

`pass=none` never promotes — that marker proves no code was read. Run a deep pass.
