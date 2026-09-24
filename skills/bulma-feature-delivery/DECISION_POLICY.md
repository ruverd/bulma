# Decision policy

Talk to the user **as a last resort**. Almost every call is **DECIDE**.
Chat language: `bulma-memory`. Forge text stays English.

ASK only when **both** are true:

1. **Very important.** Hard to reverse, or it changes product / security / money / tenant / public API in a way the ticket does not already settle.
2. **High uncertainty.** After reading the repo, the tracker, and (if needed) a prototype, you still cannot defend a recommendation.

Importance alone is not enough. Uncertainty on a small call is not enough. Pick the smaller local option, log it, continue.

## Three modes

| Mode | When | Action |
|---|---|---|
| **DECIDE** | Default. You have a recommendation you can defend, or the call is not that important | Choose, log, continue. Do not wait. |
| **ASK** | Last resort: very important **and** high uncertainty | One question in the chat language. Show the recommendation. Wait. Then continue. |
| **ESCALATE** | Loops exhausted, missing critical MCP, cannot run the graph | Freeze. Chat summary in the chat language. Tracker and PR notes stay English. Wait. |

Before ASK, spend the lookup: `how`, the tracker, neighbor files, a throwaway prototype. Load `why` only if that still leaves a last-resort fork. If the lookup produces a rec you would ship, **DECIDE**.

Test: would you stop a senior engineer at 11pm for this. If no, DECIDE.

## How to DECIDE when you are not 100% sure

Prefer, in order: stated the ticket AC, existing pattern in the same feature, YAGNI (smaller change), CLAUDE.md / AGENTS.md / the repo's schema and module rules.

Log residual risk. Do not convert leftover doubt into a question.

## ASK (last resort only)

All of these must hold:

- Very important (auth / tenant / PII / money / destructive migration, or a product fork the ticket does not settle).
- High uncertainty (two+ options with similar force; looking it up did not break the tie).
- Last resort (you already tried repo + tracker + prototype if the question is ungrillable).

If any bullet fails: **DECIDE**.

Forbidden ASK:

- "Which seam?"
- "Full feature or bug?" when the ticket title already says.
- "Close the spec / grill?"
- Rubber-stamping a recommendation you already believe.
- Path choice when ROUTING.md already classifies it.
- Anything you asked because the topic felt important.

TDD looking impossible without a redesign: ASK the redesign. Do not skip TDD.

## How to ASK

Chat language. **One question.** Then `waiting_user`. After the answer, DECIDE the rest. Do not restart.

Shape (speak this in the chat language):

```
Q: <only the tie lookup did not break>
A. ...
B. ...
Recommendation: A, because <fact>.
I am asking because: important + high uncertainty after <paths / tracker>.
```

## Grill vs implement

Grill decides internally. Implement does not reopen the plan. `NEEDS_CONTEXT` from a coder: parent DECIDE from spec + repo. ASK only if that too is last-resort.

## Facts

Never ask for a fact you can grep. No tracker on a **fresh start**: you may run as a local goal, but prefer the ticket id if the user gave one. Do not invent ACs.

## Anti-invention

- Do not invent a lib, state pattern, folder, or abstraction if a neighbor already solves it.
- Do not "improve the architecture" outside the goal.
- Do not skip TDD because "it is simple".
- Do not invent product AC. If it is missing, ASK or escalate with an explicit testable hypothesis.
- UI: do not invent visual. [UI_DESIGN_SYSTEM.md](UI_DESIGN_SYSTEM.md).
- Missing contract: [BLOCKERS.md](BLOCKERS.md). Do not fake the endpoint.

## Log

STATE → `## Decisions`:

```markdown
- **ISO-TIME | DECIDE|ASK**
  - **Choice:** ...
  - **Who:** agent | user
  - **Confidence:** high | medium | low
  - **Evidence:** path or tracker id
  - **Residual risk:** ...
```

Also append `decisions.tsv` when grilling. Chat a short rollup of auto-decisions. Do not hide DECIDE.

## Escalate

1. STATE `status: escalated`. No new dispatch.
2. Chat summary: PR / ticket / red checks. tracker comment if any: English.
3. Optional tracker comment with the same summary.
4. End the turn. Resume at the named node.

Slice loop exhaustion (`review_fix_loops` / `test_fix_loops`): mark the ticket `blocked` and escalate. Never skip to the next ticket or to shipper.
