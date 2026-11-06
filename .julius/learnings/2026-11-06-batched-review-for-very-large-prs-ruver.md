---
title: Batched review for very large PRs
author: Ruver
date: 2026-11-06
id: l-10615653
branch: feat/review-batched-large-prs
touches:
  - skills/bulma-code-review/scripts/batch-plan.py
  - skills/bulma-code-review/scripts/snapshot.py
  - skills/bulma-code-review/nodes/batches.md
---

## Decided
skills/bulma-code-review/scripts/batch-plan.py batches only very large PRs (>50 files, >5000 changed lines, or API diff HTTP 406): plan writes batches of <=15 files / ~1500 lines (hotspots first, mechanical last); merge writes one coverage.json/findings.json for one review artifact. skills/bulma-code-review/scripts/snapshot.py collect --checkout falls back to local git diff base...head on 406. Flow lives in skills/bulma-code-review/nodes/batches.md.
## Tried and ruled out
Batching every PR over the 15-file deep cap: user wants batching only for very large PRs. gh pr diff for the deep diff: also 406s on big PRs.
## Watch out
Published findings (10) and nits (5) caps stay per PR, not per batch. AC.md, critic, verdict and publish run once on the merged ledger.
