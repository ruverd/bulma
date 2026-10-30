---
title: LSTM verified feedback closes prevention loop
author: Ruver
date: 2026-10-30
id: l-eb3b6586
branch: feat/unslop-humor-pr-body
touches:
  - ".claude-plugin/plugin.json"
  - ".grok-plugin/plugin-index.json"
  - CHANGELOG.md
  - THIRD_PARTY.md
  - docs/ARCHITECTURE.md
  - docs/commands/bulma-developer.md
  - docs/commands/bulma-feature-delivery.md
  - docs/commands/bulma-goal.md
  - docs/commands/bulma-lstm.md
  - docs/commands/bulma-qa.md
---

## Decided
LSTM now runs learn after reply and before report. skills/bulma-bus/FEEDBACK.md defines verified per-cause assessments outside git, scoped project Prevention entries consumed by coder, fd review, PR review and QA, and eligible GitHub improvement issue drafts. Requests for changes or LSTM invocation alone do not prove a defect or an earlier-stage miss. Task eligibility requires a concrete regression and prevention change, plus recurrence on two PRs or one demonstrated high-impact case. Publication defaults to draft and needs authorization and an exact destination.

## Tried and ruled out
Existing observe.py and lookback.py already provide telemetry and aggregate clusters; duplicating them would not establish verified stage attribution. Append-only telemetry may retain unknown claims, so promotion uses separate evidence-based assessments. Do not treat path proximity as causality or false/bot/evidence-only feedback as human missed-defect metrics. Repository, LSTM, code-review and QA checks passed. No live product run or GitHub issue publication was exercised.

## Watch out
Current worktree already contained many unrelated changes. julius check reported lexical conflicts across those changes and the new memory/LSTM text. These changes do not add caches/batching, claim performance gains, or replace visual QA with source inspection; they preserve existing sign-off requirements. Issues remain local drafts until publication policy and destination are authorized. Shared assessments and memory require coordinator serialization; otherwise retain pending job-local records. No commit or PR was created in this session.
