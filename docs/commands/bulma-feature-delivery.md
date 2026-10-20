# `/bulma-feature-delivery`

Alias: `/bulma-fd`.

Delivery **engine** inside [`/bulma-developer`](bulma-developer.md).
Grill → spec → tickets → plan_critic (gated) → TDD implement → review → CI.
The main thread still does not write product code.

Small, known tasks use one canonical contract for spec and ticket. Elevated risk
and structural changes use deep quality before independent review. Focused quality
reuses the coder. On Codex, invoke `$bulma-feature-delivery` through its skill.

Skill: [`../../skills/bulma-feature-delivery`](../../skills/bulma-feature-delivery).

## When

- `/bulma-fd ABC-123`
- `/bulma-fd login button does nothing`
- `/bulma-fd resume`
- `/bulma-fd … --no-pr`
- Implicitly, from developer `deliver`

Prefer `/bulma-developer` when you also want MERGEABLE + QA after CI.
`/bulma-fd` alone stops at CI green (it does **not** call QA).

## Spine

```
bounded decisions → spec → tickets → plan_critic → implement (TDD)
  → blast when required → quality → review → tester → evidence → shipper → CI
```

| Path | When |
|---|---|
| `full_feature` | new behavior |
| `debug_fix` | bug — diagnose first, one TDD ticket |
| `light_change` | chore — one ticket, one coder |
| `scope: fullstack` | FE and BE, same branch |

Grill, spec, and tickets stay on the **main thread**. `plan_critic`
runs there too, except `risk=elevated` (one read-only spawn). Implement /
tester / quality / shipper are workers (`bulma-fd-coder`, …).

## What “delivered” means here

Draft PR **and** required CI green. `--no-pr` or `forge=git`: commit
(+ push). No PR. Until then `status ≠ done`.
Forge, tracker, toolchain, reviewers, assignee:
[PRODUCT.md](../../skills/bulma-feature-delivery/PRODUCT.md).

## Never

- Merge.
- Product edits on the main thread.
- Skip TDD on a behavior change.
- Edit product code after final validation without repeating affected checks.
- Invent tracker AC when that URL cannot be read — stop. Local goal is fine without a tracker.

## Related

[`/bulma-developer`](bulma-developer.md) · [`/bulma-goal`](bulma-goal.md) ·
worker contracts in [`agents/`](../../agents/)
