---
title: LSTM human sign-off requires visual QA evidence
author: Ruver
date: 2026-10-30
id: l-cf85580c
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
skills/bulma-lstm/nodes/request_qa.md routes sign-off and visual-proof requests through bulma-qa, including evidence-only comments. Require current-head proof for every requested behavior. skills/bulma-qa/references/LOCAL_SETUP.md permits reversible isolated local database/auth preparation, including Zitadel QA roles and claims. Automated QA supports human approval without granting it.

## Tried and ruled out
CI or source inspection alone cannot satisfy visual proof. Missing seed scripts alone do not justify skipping available local fixture setup. julius check reported lexical overlaps with efficiency-research notes in the dirty worktree; this change concerns review-to-QA routing, not decision caches or performance claims. Repository, LSTM and QA checks passed; no live product PR was exercised.

## Watch out
Verify database and auth mutation targets independently of localhost app origin. Preserve auth checks and clean up disposable fixtures. Existing external-provider policy and queue remain in force. developer -> lstm -> qa fills the three-frame stack; triage cannot push a fourth frame. Missing requested cases or attachments keep sign-off pending. Keep actual human approval requests open.
