---
name: grill-with-docs
category: lib
description: >
  Grilling session that challenges your plan against the existing domain model,
  sharpens terminology, and updates CONTEXT.md and ADRs inline. Use when the
  user wants to stress-test a plan against the project's documented decisions.
---

<what-to-do>

For a requested design interview, challenge consequential decisions against the
documented domain model. Routine delivery uses
[bounded discovery](../bulma-feature-delivery/GRILL.md) instead.

Resolve recoverable facts from supplied context, code and docs. Ask about missing
intent that changes the plan. Challenge assumptions with concrete scenarios.
Explain what each answer changes and give a recommendation when useful;
confidence does not establish user intent.

Ask dependent questions one at a time. Bundle up to three independent questions
when this saves a round trip. Preserve answered decisions. Stop when the
requested scope, constraints and acceptance criteria are actionable or the user
ends the interview; do not exhaust branches with no consequence for the plan.

</what-to-do>

<supporting-info>

## Domain awareness

During codebase exploration, also look for existing documentation:

### File structure

Most repos have a single context:

```
/
├── CONTEXT.md
├── docs/
│   └── adr/
│       ├── 0001-event-sourced-orders.md
│       └── 0002-postgres-for-write-model.md
└── src/
```

If a `CONTEXT-MAP.md` exists at the root, the repo has multiple contexts. The map points to where each one lives:

```
/
├── CONTEXT-MAP.md
├── docs/
│   └── adr/                          ← system-wide decisions
├── src/
│   ├── ordering/
│   │   ├── CONTEXT.md
│   │   └── docs/adr/                 ← context-specific decisions
│   └── billing/
│       ├── CONTEXT.md
│       └── docs/adr/
```

Update existing documentation when a consequential term or decision changes.
Create a new CONTEXT or ADR tree only when the user requests domain documentation.
Otherwise keep rationale in the current decision record.

## During the session

### Challenge against the glossary

When the user uses a term that conflicts with the existing language in `CONTEXT.md`, call it out immediately. "Your glossary defines 'cancellation' as X, but you seem to mean Y — which is it?"

### Sharpen fuzzy language

When the user uses vague or overloaded terms, propose a precise canonical term. "You're saying 'account' — do you mean the Customer or the User? Those are different things."

### Discuss concrete scenarios

When domain relationships are being discussed, stress-test them with specific scenarios. Invent scenarios that probe edge cases and force the user to be precise about the boundaries between concepts.

### Cross-reference with code

When the user states how something works, check whether the code agrees. If you find a contradiction, surface it: "Your code cancels entire Orders, but you just said partial cancellation is possible — which is right?"

### Update CONTEXT.md inline

When a consequential term is resolved, update existing `CONTEXT.md` using
[CONTEXT-FORMAT.md](CONTEXT-FORMAT.md). Do not duplicate the conversation.

Don't couple `CONTEXT.md` to implementation details. Only include terms that are meaningful to domain experts.

### Offer ADRs sparingly

Only offer to create an ADR when all three are true:

1. **Hard to reverse** — the cost of changing your mind later is meaningful
2. **Surprising without context** — a future reader will wonder "why did they do it this way?"
3. **The result of a real trade-off** — there were genuine alternatives and you picked one for specific reasons

If any of the three is missing, skip the ADR. Use the format in [ADR-FORMAT.md](ADR-FORMAT.md).

</supporting-info>
