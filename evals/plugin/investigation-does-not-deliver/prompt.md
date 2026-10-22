---
description: 'A request asks for diagnosis only.'
expected_outcome: 'The agent gives a read-only investigation without implementing or opening a PR.'
max_turns: 6
tags: [playbooks]
timeout_seconds: 90
allowed_tools: [Read, Glob, Grep, Skill]
---

Investigate why our queue sometimes sends the same email twice. For now I want the evidence, competing explanations and a recommendation. Do not fix or publish anything. No logs or source have been supplied yet; tell me what can be concluded now and what evidence would distinguish the causes.
