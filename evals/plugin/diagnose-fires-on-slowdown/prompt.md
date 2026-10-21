---
description: "A performance regression report with no code. diagnose should fire."
expected_outcome: "The reply starts a diagnosis loop: reproduce and measure before guessing a cause."
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

The orders page got about three times slower after yesterday's deploy. Nothing errors, it is just slow. Help me figure out what happened.
