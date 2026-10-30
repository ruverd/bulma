---
title: Publish verified feedback changes from isolated main worktree
author: Ruver
date: 2026-10-30
id: l-f5edad5b
branch: feat/lstm-verified-feedback
touches:
  - skills/bulma-bus/INSIGHTS.md
  - skills/bulma-code-review/nodes/review.md
  - skills/bulma-feature-delivery/IMPLEMENTATION.md
  - skills/bulma-feature-delivery/nodes/coder.md
  - skills/bulma-feature-delivery/nodes/reviewer.md
  - skills/bulma-lstm/GRAPH.md
  - skills/bulma-lstm/SKILL.md
  - skills/bulma-lstm/STATE.schema.md
  - skills/bulma-lstm/nodes/report.md
  - skills/bulma-lstm/nodes/resume.md
---

## Decided
Create feat/lstm-verified-feedback from origin/main in a separate worktree because the original checkout contains unrelated edits and staged deletions. Transfer only this session's skills/bulma-bus/FEEDBACK.md contract, skills/bulma-lstm/nodes/learn.md node, feedback additions and tests/lib/check_graphs.py requirement. Keep skills/bulma-reviewer/templates/STATE.md feedback fields in frontmatter because they are state fields.

## Tried and ruled out
Do not copy complete dirty files from the original checkout because it predates newer main task-playbook and runtime-evidence changes. Apply only feedback additions onto current main. julius check reports lexical overlaps with prior learnings, including the feedback contract itself. These are not semantic contradictions: observations stay human-only, bot findings use separate assessments, stage attribution requires evidence, and visual sign-off proof stays required.

## Watch out
No additional runtime capture system or performance claim is introduced. The change uses existing project memory and observation tooling, adds verified assessment instructions, and keeps issue creation draft-only unless publication and destination are authorized. PR description must document lexical-check overrides and distinguish offline checks from exercising a live product PR.
