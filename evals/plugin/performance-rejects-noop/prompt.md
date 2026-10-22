---
description: 'A benchmark looks fast because most work was rejected.'
expected_outcome: 'The agent rejects the speedup claim and calls for comparable successful work.'
max_turns: 6
tags: [playbooks]
timeout_seconds: 90
allowed_tools: [Read, Glob, Grep, Skill]
---

Our export benchmark improved from 800 ms to 40 ms. Looking at the run, 95 of 100 exports returned an error and wrote no file. The old run exported all 100 successfully. Write the performance verdict for this PR. We have only one run per side.
