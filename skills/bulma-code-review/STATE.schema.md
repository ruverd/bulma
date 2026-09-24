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
| `ci` | pending \| green \| red |
| `pass` | deep \| light, decided by [nodes/pass_decision.md](nodes/pass_decision.md) |
| `verdict` | APPROVE \| REQUEST_CHANGES \| DEFER |
| `defer_reason` | set whenever `verdict=DEFER` (CI red, draft, conflict) |
| `reviewed_shas` | SHAs already reviewed, so a light pass knows the carry-forward |
| `caller` | the graph that asked, when invoked over the bus |
| `loop_id` | host `schedule_wake` id while `waiting_ci` ([LOOP.md](LOOP.md)) |
| `risk` | from `scripts/classify-risk.py`; high enables the critic |
| `critic` | whether the critic spawned |

## risk

```
low | high
```

## critic

```
skip | ran
```

## Rules

- One artifact per PR per SHA. Re-running on an unchanged SHA does not publish
  a second review.
- `waiting_ci` never posts to the PR. It waits, then reviews on green.
- A DEFER is recorded with its reason. It is not an APPROVE with caveats.

Template: [templates/STATE.md](templates/STATE.md).
