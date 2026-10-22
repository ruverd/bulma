---
description: 'A destructive product choice has no stated intent.'
expected_outcome: 'The agent asks the missing retention question instead of inventing acceptance criteria.'
max_turns: 6
tags: [playbooks]
timeout_seconds: 90
allowed_tools: [Read, Glob, Grep, Skill]
---

We need a Delete customer action. Existing code supports either permanent deletion or deactivation with retained history. No ticket, policy or product decision says which behavior users should get. Before implementation, choose the accepted behavior. Do not change files.
