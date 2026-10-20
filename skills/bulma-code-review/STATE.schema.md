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
| `pr` | `<owner>/<repo>#<N>` |
| `pr_url` | full URL |
| `sha` | head SHA at the time of the pass |
| `reviewed_sha` | full SHA whose diff, callers and contracts were actually reviewed; never advance without reviewing the delta |
| `base_sha` | base SHA used for this pass; a base change invalidates the full PR diff |
| `review_context` | clear \| blocked \| unknown; evidence and concern URLs live in preflight files |
| `human_signoff` | required \| not_required; sensitive paths from the full PR file list |
| `ci_evidence` | run/check IDs, links, SHA and execution results; local tests recorded separately |
| `reviewer_model` | executing reviewer's runtime model name or id for this pass; `unknown` when unavailable |
| `ci` | pending \| green \| red \| unknown |
| `pass` | deep \| light, decided by [nodes/pass_decision.md](nodes/pass_decision.md) |
| `verdict` | APPROVE \| REQUEST_CHANGES \| DEFER \| COMMENT (bot quorum) |
| `defer_reason` | set whenever `verdict=DEFER` (CI red, draft, conflict, coverage, uncertainty, critic_failed, gate) |
| `gate` | last `gate.py` result: pass \| blocked \| bot_quorum, with its reasons |
| `dismissed_approvals` | ids of my own stale approvals dismissed this pass |
| `reviewed_shas` | SHAs already reviewed, so a light pass knows the carry-forward |
| `caller` | the graph that asked, when invoked over the bus |
| `loop_id` | host `schedule_wake` id while `waiting_ci` ([LOOP.md](LOOP.md)) |
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
- `waiting_ci` never posts to the PR. It waits, then reviews on green.
- A DEFER is recorded with its reason. It is not an APPROVE with caveats.

Template: [templates/STATE.md](templates/STATE.md).
