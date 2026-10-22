---
description: 'A handoff carries completed steps and unchanged invariants.'
expected_outcome: 'The agent preserves settled decisions and resumes at the pending node.'
max_turns: 6
tags: [playbooks]
timeout_seconds: 90
allowed_tools: [Read, Glob, Grep, Skill]
---

Take over this delivery. Handoff says discovery, acceptance and implementation are complete. The recorded branch, HEAD, working-tree fingerprint and acceptance revision all still match the current read-only reconciliation. Review passed; tester has not run yet. Where should we resume? Do not change files or start processes in this turn.
