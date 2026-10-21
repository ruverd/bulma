---
description: "A pasted bug with an explicit regression-test request. tdd is user-invoked only, so this grades the reply, not a fire."
expected_outcome: "A failing test that reproduces the lost cent comes before any fix."
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

Add a regression test for this bug before fixing it: splitCents(100, 3) returns [33, 33, 33], so a cent goes missing.

```js
// Splits an amount in cents across n people. The total must be preserved.
function splitCents(total, n) {
  const share = Math.floor(total / n);
  return Array.from({ length: n }, () => share);
}
```
