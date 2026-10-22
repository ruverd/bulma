---
description: 'External QA reports BLOCKED for the current head.'
expected_outcome: 'The agent keeps external QA ownership and does not treat transport success as a QA pass.'
max_turns: 6
tags: [playbooks]
timeout_seconds: 90
allowed_tools: [Read, Glob, Grep, Skill]
---

This repo delegates QA to an external provider. Its status on the current head is success, with description AI QA BLOCKED (browser runner timeout). Unit tests passed. Should Bulma run its own QA now or call this a QA PASS? Do not contact the provider or post anything.
