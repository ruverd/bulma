---
title: Require model and reasoning effort in reviews and PR descriptions
author: Ruver
date: 2026-10-30
id: l-2ebda63f
branch: fix/review-model-effort
touches:
  - skills/bulma-code-review/scripts/gate.py
  - skills/bulma-code-review/nodes/publish.md
  - skills/bulma-host/PR_ATTRIBUTION.md
  - skills/bulma-feature-delivery/templates/PR_BODY.md
---

## Decided
skills/bulma-code-review/scripts/gate.py requires nonempty Model and Reasoning effort rows for APPROVE, REQUEST_CHANGES and COMMENT. Publication instructions preserve both fields for DEFER and dry-run. Reviewer runtime metadata supplies actual model/effort; unknown is explicit when unavailable. skills/bulma-host/PR_ATTRIBUTION.md requires each PR, stacked child and fullstack sibling to carry its own Agent run section. The PR template distinguishes implementation from code review settings, copied from reviewer output and preserved on fixes.

## Tried and ruled out
A durable memory preference alone did not enforce attribution. Model-only rows omit reasoning effort. Requested config tiers or publisher/critic identity do not establish which session reviewed code. Tests cover absent/empty/unknown fields for all three review events. Repository, code-review and developer suites passed in an isolated current-main worktree.

## Watch out
Keep bulma-host SKILL.md within 250 lines by linking PR_ATTRIBUTION.md. Current main contains newer CI-scope and second-opinion work; preserve it instead of copying dirty source files wholesale. julius check flags lexical overlaps with old capture/provider/telemetry notes. These edits add attribution, not another capture system, provider-specific examples, telemetry claims or changes to prevention policy; conflicts are lexical and are explained in the PR. No live review POST was exercised.
