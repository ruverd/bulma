---
title: "Jev audit: Noul calibration and response validation gaps"
author: Ruver
date: 2026-10-28
id: l-6c6877cb
branch: feat/unslop-humor-pr-body
touches:
  - skills/bulma/scripts/bulma.py
  - skills/bulma/scripts/decision_cache.py
---

## Decided
Read-only audit found two reproducible Noul gaps in skills/bulma/scripts/bulma.py. judge() correctly treats p=.1 as decisive no at act_at=.8, but rows_for() logs answer=.1 and confidence=.1. cmd_report()/suggest_threshold() compare this numeric answer directly against categorical graph_answer values such as yes/no, and the suggestion scan only considers confidence >= .5. Normalize categorical agreement and handle both probability tails before using Noul reports to tune thresholds. Outcome-based evaluation must distinguish unlabeled decisions from confirmed correctness.

## Tried and ruled out
Verified both cases with offline imports and assertions; no API calls or runtime config changes. Cache and ask-many already exist, so recommending their addition duplicates current implementation. Current default pins jev-1.13.0; official TypeSafe documentation lists jev-1.14.0, but any migration needs a labeled comparison rather than an assumed accuracy or speed gain.

## Watch out
judge() accepts a malformed Noul answer {} as p=0 and act=true. Missing or invalid typed values must trigger fallback rather than a decisive no. post_json() uses four attempts with a 20-second per-attempt timeout plus backoff, without a total decision deadline. prepare() warns on missing state keys but still allows inference. Audit findings only; fixes were not requested or applied.
