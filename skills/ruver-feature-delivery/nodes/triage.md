# Node: triage (router)

**Verb:** classify
**Capability:** read-only on code; write STATE only
**Output:** `work_kind` + `path` + `risk` + reason

## Mission

Classify the goal and pick the graph path ([ROUTING.md](../ROUTING.md)).
Do not implement. Do not debug in depth (that is **diagnose** on path debug_fix).

## Steps

1. Read the goal (+ ticket if a URL/ID is in the text).
2. Light repo scan if the goal cites files/errors (stack, test name).
3. Classify `work_kind`: feature | bug | regression | chore | spike.
4. Classify **`scope`**: frontend_only | backend_only | mono | **fullstack**
   ([PRODUCT.md](../PRODUCT.md)). Fullstack only if a sibling resolved.
5. Choose `path`: full_feature | debug_fix | light_change
   (if fullstack, path is the mode **per worker**; coordination is FULLSTACK.md).
6. Choose `risk`: low | normal | elevated ([ROUTING.md](../ROUTING.md) §Risk).
   Path is the spine. Risk only toggles extra gates. An auth **bug** is
   `debug_fix` + `elevated`, not `full_feature`.
7. DECISION_POLICY: DECIDE the path and risk. ASK only last-resort. Do not ASK "feature or bug?" when the title already says.
8. Write STATE + Decisions.

## Output

```text
result: ok | ask | blocked
work_kind: feature | bug | regression | chore | spike
scope: frontend_only | backend_only | mono | fullstack
path: full_feature | debug_fix | light_change
risk: low | normal | elevated
risk_reason: one sentence
confidence: high | medium | low
route_reason: one sentence
question: ...  # if ask; speak in the chat language
```

## Minimum heuristic (do not invent)

- Break/error/stack/fail words → prefer **debug_fix**
- "add/new/implement/support" + new behavior → **full_feature**
- 1 file / rename / config → **light_change**
- Auth/billing/secret **bug** → **debug_fix** + `risk=elevated`
- Auth/billing/secret **feature** → **full_feature** + `risk=elevated`

## Hard rules

- Zero product code.
- Always record path and risk (reviewer/shipper trust them).
- Harmful doubt → short ASK, not full_feature "to be safe" on an obvious bug.
