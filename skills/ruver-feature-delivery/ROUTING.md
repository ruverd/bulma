# Routing

Do this after `mcp_context`. Evidence first, not "everything is a feature".

## Classification

Write into STATE:

```yaml
work_kind: feature | bug | regression | chore | spike
path: full_feature | debug_fix | light_change
risk: low | normal | elevated
risk_reason: "..."
scope: frontend_only | backend_only | mono | fullstack
route_confidence: high | medium | low
route_reason: "..."
```

| Looks like | path |
|---|---|
| New behavior, UX, or a rule that needs grilling | `full_feature` |
| Bug, regression, red test, "X is broken" | `debug_fix` |
| Chore, rename, 1–2 obvious files, no product fork | `light_change` |

If the ticket is both a bug and a redesign: DECIDE `debug_fix` when the AC is "restore X"; DECIDE `full_feature` when the ticket asks for new behavior. Do not ASK the path.

`debug_fix` never skips root cause. If diagnose finds a missing feature, re-route to `full_feature` (grill).

`light_change` still TDD if behavior changes. If you cannot write a failing test, upgrade the path yourself (DECIDE). Do not ASK to upgrade.

## Risk

Orthogonal to `path`. `path` is the spine. `risk` only toggles extra gates.

| | `low` | `normal` | `elevated` |
|---|---|---|---|
| `full_feature` | grill stays. no plan_critic | grill stays. plan_critic on main | grill stays. plan_critic spawn |
| `debug_fix` | diagnose stays | diagnose stays | diagnose stays. Do not re-route to grill because the files look like auth |
| `light_change` | no blast | no blast | **blast** |

Triage-time `risk` is from the goal and ticket text. PR-diff risk is `../ruver-code-review/scripts/classify-risk.py` after there is a diff. Do not run that script here.

### Heuristic (goal + ticket text)

- `elevated`: auth, tenant, billing, payment, migration, secret, session, rbac, PII, public API/contract, webhook
- `low`: docs, rename, copy, CSS with no behavior
- `normal`: everything else

Auth/billing/secret **bug** → `debug_fix` + `elevated`.
Auth/billing/secret **feature** → `full_feature` + `elevated`.
Do not pick `full_feature` because the area is dangerous.

Missing `risk` on a v4 STATE resume → `normal`.

## Scope

| scope | When |
|---|---|
| `frontend_only` | this git root is UI only |
| `backend_only` | this git root is API only |
| `mono` | UI and API in **this** git root |
| `fullstack` | ticket needs both sides **and** a sibling resolved ([PRODUCT.md](PRODUCT.md)) |

Signals: new endpoint + screen; "backend and frontend"; AC on both repos.

On fullstack, `path` applies **per worker**.

## Paths

### `full_feature`

```
triage → grill → spec → tickets → plan_critic → implement* (TDD) → review → tester
       → evidence → blast → quality (thermo) → shipper → ci_watch
```

`plan_critic` skips when `risk=low`. Main-thread scan when `normal`. Spawn when `elevated`.

Use when: new feature, multi-file design still open. Auth/billing/contract as **new behavior** still `full_feature` (and `risk=elevated`). A bug in those areas is `debug_fix` + `elevated`.

### `debug_fix`

```
triage → diagnose → one ticket (RED repro) → implement → review → tester
       → evidence → blast → quality → shipper → ci_watch
```

Skip grill and multi-ticket split. Do **not** skip root cause, TDD, review, thermo.

Iron law: no product fix before root cause.

### `light_change`

```
triage → one ticket → implement → review → tester → evidence → quality → shipper
```

Skip grill. Skip blast unless `risk=elevated`. Still a subagent for product code. Docs-only outside `src/` may be edited on the main thread.

### `spike`

Read-only diagnose. `done_report`. No PR. If it is a bug, re-route `debug_fix`. If it is a feature, re-route `full_feature`.

## Stages

| Stage | full_feature | debug_fix | light_change |
|---|---|---|---|
| triage | yes | yes | yes |
| grill | yes | no | no |
| diagnose | no | **required** | no |
| spec + tickets | yes | one ticket | one ticket |
| plan_critic | skip if `risk=low`; else yes | no | no |
| TDD | yes | yes (repro test) | if behavior |
| review | yes | yes | yes |
| tester | yes | yes | yes |
| evidence | yes | yes | yes |
| blast-radius | yes | yes | no, unless `risk=elevated` |
| thermo fix all | yes if ship | yes if ship | yes if ship |

## Anti-patterns

- full_feature on a null-check
- Upgrading a bug to full_feature because it touches auth
- Skipping blast on light_change when `risk=elevated`
- Spawning plan_critic on a bug, or on every full_feature
- Quick fix of a bug with no diagnose
- Skipping TDD because "I reproduced it by hand"
- Skipping thermo when a PR will open
- Staying on debug_fix after you found a missing feature
