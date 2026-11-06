# Code review STATE

**Path:** `.bulma-code-review/STATE.md`

One entry per PR. A pass is decided from what earlier passes already covered on
which SHA, so this file is what makes deep-then-light work across turns.

## status

```
init | waiting_ci | reviewing | published | deferred | done
```

## Fields

| Field | Use |
|---|---|
| `review_dir` | per-PR snapshot and retained analysis directory |
| `pr` | `<owner>/<repo>#<N>` |
| `pr_url` | full URL |
| `sha` | head SHA at the time of the pass |
| `reviewed_sha` | full SHA whose diff, callers and contracts were actually reviewed; never advance without reviewing the delta |
| `base_sha` | base SHA used for this pass; a base change invalidates the full PR diff |
| `review_context` | clear \| blocked \| unknown; evidence and concern URLs live in preflight files |
| `human_signoff` | `not_required`, or `required` plus the sensitive paths. Private job report and STATE only. Never a PR row |
| `ci_evidence` | run/check IDs, links, SHA and execution results; local tests recorded separately |
| `reviewer_model` | executing reviewer's runtime model name or id for this pass; `unknown` when unavailable |
| `reviewer_effort` | executing reviewer's actual reasoning effort for this pass; `unknown` when unavailable; preserve paired role attribution across contributing sessions |
| `ci` | pending \| green \| red \| unknown \| unverified |
| `pass` | deep \| light, decided by [nodes/pass_decision.md](nodes/pass_decision.md) |
| `verdict` | APPROVE \| REQUEST_CHANGES \| DEFER \| COMMENT (bot quorum, review pending, CI not verified, coverage, critic_failed, head_changed) |
| `defer_reason` | set whenever `verdict=DEFER` (CI red, CI unknown, draft, conflict only) |
| `gate` | last `gate.py` result: pass \| blocked \| bot_quorum \| review_pending \| ci_unverified, with its reasons |
| `dismissed_approvals` | ids of my own stale approvals dismissed this pass |
| `reviewed_shas` | SHAs already reviewed, so a light pass knows the carry-forward |
| `caller` | the graph that asked, when invoked over the bus |
| `loop_id` | host `schedule_wake` id while `waiting_ci` ([LOOP.md](LOOP.md)) |
| `batches` | very large PRs only: batch count and ids still open; `-` otherwise ([nodes/batches.md](nodes/batches.md)) |
| `risk` | from `scripts/classify-risk.py`; high enables the critic |
| `critic` | whether the critic ran; `failed` on a high-risk run whose critic did not complete |

## risk

```
low | high
```

## critic

```
skip | ran | failed
```

`skip` only when `risk=low`.

## Rules

- One artifact per PR per pass. Re-running with an unchanged SHA and unchanged
  evidence does not duplicate an artifact. New concerns, a legacy marker needing
  revalidation, or a valid CI promotion can require a new verdict on that SHA.
- `waiting_ci` never posts to the PR. It retains analysis, then revalidates on green.
- A DEFER is recorded with its reason. It is not an APPROVE with caveats.

Template: [templates/STATE.md](templates/STATE.md).
