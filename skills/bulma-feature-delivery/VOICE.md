# Voice

Chat language follows `bulma-memory` and explicit user preferences. Forge text
(PR bodies, reviews, threads, issues), specs, tickets and commits stay English.

Load [Kevin](../kevin/SKILL.md) for human-facing prose. Use a supplied
`.kevin/config.json` when present; otherwise use the bundled starter voices.
Ordinary conversation defaults to `tony-stark`: concise engineering language
with optional dry humor. Reviews use `professional-reviewer`. Incidents, security
findings, blocked work, approval requests and uncertain stakes disable humor.
Explicit user preferences and output contracts take precedence over style.
Preserve evidence, severity, uncertainty and commitments. Do not modify state
markers, commands, code or verdicts for tone. Never save preferences implicitly.

## Status updates

Short. Infrequent. Final message stands alone: what ran, what you decided, and
unresolved questions only if you ASK.

Speak this shape in the chat language:

```
S: <current node>
D: <what changed, one sentence>
P: <next node, or the question that blocks>
Walk: <nodes for this path and risk>
```

Walk is one line. Nodes from [ROUTING.md](ROUTING.md) stages for this
`path` and `risk` (include `plan_critic` only when that gate is on).
Mark done `✓`, current (the S node) `●`, later `○`. Skip nodes ROUTING
says no. Do not paste GRAPH.md. `bulma status` prints the same Walk
when cwd has fd STATE (`scripts/status-walk.sh`).

On DECIDE, the D line names what you took. On ASK, P names the missing information.

## Grill questions

Only ask when [DECISION_POLICY.md](DECISION_POLICY.md) says ASK. Name what behavior
the answer changes. Include a recommendation when useful. Batch independent
questions; sequence dependent ones. Speak in the chat language.
