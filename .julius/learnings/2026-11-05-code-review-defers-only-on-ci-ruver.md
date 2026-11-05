---
title: "Code review DEFERs only on CI red/unknown, draft or conflict"
author: Ruver
date: 2026-11-05
id: l-cc0ff286
branch: fix/review-defer-ci-only
---

## Decided
User rule (2026-11-05): bulma-code-review DEFER only for CI red/unknown, draft, conflict. Blocker/major -> REQUEST_CHANGES; nits only -> APPROVE; everything else (review_pending, CI unreadable, coverage, critic_failed, head_changed) -> COMMENT review. Facts outside the repo go under "Not verified" and never change the verdict. Never write "needs a human", owner sign-off, or tag people to approve (references/VOICE.md).

## Tried and ruled out
Rewording the "Human sign-off" row alone (closed #78): the "Needs a human" bodies came from the uncertainty DEFER rule, and most Deferred comments came from review_context (16 of 18 on 2026-11-05).

## Watch out
gate.py needs_deep counts my COMMENTED reviews with coverage/uncertainty/critic_failed, not only DEFER comments. Check PR state before pushing to an existing branch: #76 had merged, so the push never reached main.
