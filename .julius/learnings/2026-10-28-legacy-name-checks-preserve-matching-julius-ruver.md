---
title: Legacy-name checks preserve matching Julius author provenance
author: Ruver
date: 2026-10-28
id: l-ea23ed8c
branch: fix/jev-decision-reliability
touches:
  - tests/lib/check_legacy_name.py
  - tests/lib/test_legacy_name.py
---

## Decided
tests/lib/check_legacy_name.py now uses learning_identity() because CI failed when a Julius learning author's first name matched the obsolete product name. Only a dated learning's frontmatter author and matching filename suffix are exempt. Its title, body and remaining filename still undergo the branding check. tests/lib/test_legacy_name.py verifies these boundaries using temporary git indexes.

## Tried and ruled out
Rewriting existing authors would destroy provenance. Excluding the entire learning directory or allowing the first name globally would hide actual obsolete branding, so both alternatives were rejected.

## Watch out
The checker reads git ls-files, so untracked learning files escape local validation. Stage new learnings before the final repo checks because remote CI sees them as tracked files. This caused the initial Jev PR's local/remote validation mismatch.
