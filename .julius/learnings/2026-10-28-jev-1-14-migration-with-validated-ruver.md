---
title: Jev 1.14 migration with validated answers and outcome calibration
author: Ruver
date: 2026-10-28
id: l-fc200921
replaces: l-6c6877cb
branch: fix/jev-decision-reliability
touches:
  - skills/bulma/scripts/bulma.py
  - skills/bulma/POWER.md
  - tests/lib/test_jev_reliability.py
---

## Decided
skills/bulma/scripts/bulma.py now pins DEFAULT_MODEL to jev-1.14.0 at the user's explicit request to include the upgrade in this PR. This supersedes the earlier audit's suggestion to delay the default migration. Explicit model settings still win. No measured improvement in model accuracy or latency is claimed. judge() rejects malformed probabilities, invalid enums and Noul ties. prepare() rejects missing required state before the batch sends anything; truncated states fall back without inference. State projection retains recipe roots and entry.route.pr as an optional field.

## Tried and ruled out
Do not add another cache or batching layer: both already existed. Do not calibrate from heuristic agreement or count unlabeled outcomes as correct. cmd_report() normalizes Noul categorical answers and evaluates both probability tails, splitting model, policy, source and power cohorts. suggest_threshold() requires at least 20 confirmed/reversed labels above a cut and at least 95 percent confirmed. Replay and cached rows cannot recommend cuts. Historical 17/19-column ledgers remain readable and migrate by header. tests/lib/test_jev_reliability.py covers these cases offline.

## Watch out
post_json() shares a request/retry budget across attempts and backoff: 3 seconds for entry hooks, 8 elsewhere, with timeout overrides. It rejects late answers but cannot guarantee hard real-time bounds for OS DNS or socket reads. skills/bulma/POWER.md documents paired shadow batches and held-out labels before trusting a model or retuning thresholds. No hosted model evaluation was performed. Images, Box and long context remain disabled. The old learning remains an audit record; this learning records the subsequent user-authorized implementation.
