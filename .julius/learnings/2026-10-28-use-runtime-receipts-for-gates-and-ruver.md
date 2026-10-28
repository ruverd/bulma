---
title: Use runtime receipts for gates and report observed phase rework
author: Ruver
date: 2026-10-28
id: l-210c96db
branch: fix/test-evidence-and-phase-metrics
touches:
  - skills/bulma-bus/scripts/runtime.py
  - skills/bulma-feature-delivery/nodes/tester.md
  - tests/lib/test_runtime.py
---

## Decided
Use runtime receipts as the source of test exit codes across TDD, tester, evidence, shipper, STATE schema and PR templates. The former test-then-echo wrapper could expose echo's success instead of the test failure. Pass runner argv directly, inspect saved logs afterward, and keep timeout or launch failure distinct from an expected RED assertion.

## Tried and ruled out
Do not create another capture system or promise faster delivery. skills/bulma-bus/scripts/runtime.py already captures child exit, output and duration. Extend its existing measurement report to aggregate retry deltas, optional boolean rework classification and coverage; missing fields remain unknown. A run filter supports inspection of one delivery without conflating overlapping work with elapsed delivery time.

## Watch out
The regression test in tests/lib/test_runtime.py deliberately invokes tail on the saved failed-test log, verifies that tail succeeds, and still rejects the failed test receipt. julius check matched that tail source to a learning about statistical probability tails and calibration. This is a lexical false positive: no probability calibration or threshold code changed, and the test prevents summary-command status from becoming a gate verdict. Retry deltas belong to the active observation; separate wait observations record zero. Rework sample counts include marked observations, not independent tasks or defects.
