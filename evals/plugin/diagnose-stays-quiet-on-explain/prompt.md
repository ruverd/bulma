---
description: "A question about how working code works. diagnose must not fire."
expected_outcome: "An explanation of the function; diagnose is never invoked."
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

How does this function work? Just explain it, I am not changing anything.

```js
// Splits an amount in cents across n people. The first (total % n) people get one extra cent.
function splitCents(total, n) {
  const share = Math.floor(total / n);
  const extra = total % n;
  return Array.from({ length: n }, (_, i) => share + (i < extra ? 1 : 0));
}
```
