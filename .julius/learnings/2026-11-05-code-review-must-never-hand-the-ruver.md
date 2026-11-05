---
title: Code review must never hand the merge to a human
author: Ruver
date: 2026-11-05
id: l-a798f97e
branch: fix/review-no-human-review-phrasing
touches:
  - skills/bulma-code-review/references/VOICE.md
---

## Decided
User rule: bulma-code-review output never says "needs a human", "human review", "human/owner sign-off", or tags people to approve. Unverified checks are stated as facts ("Not verified: terraform plan for dev"). Enforced in skills/bulma-code-review/references/VOICE.md; template rows are "Sensitive paths" and "Review focus"; gate.py REQUIRED_ROWS must match publish.md.

## Tried and ruled out
Renaming template rows alone is not enough: the offending example (empath-api-v2#2668) was free prose, not the table, so the voice rule is the real fix.

## Watch out
Internal names (--signoff, --human-signoff, STATE human_signoff) still say "human"; they are not posted. gate.py reasons land in DEFER bodies, so keep their wording neutral too.
