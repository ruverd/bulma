---
title: Keep QA identity-provider setup vendor neutral
author: Ruver
date: 2026-10-30
id: l-42b0cf45
branch: feat/lstm-signoff-visual-qa
touches:
  - docs/commands/bulma-lstm.md
  - skills/bulma-qa/references/LOCAL_SETUP.md
  - tests/bulma-code-review.sh
---

## Decided
skills/bulma-qa/references/LOCAL_SETUP.md describes the identity provider discovered in the target repository. The setup contract still covers user activation, organization/project grants, roles, claims and dev client settings without naming a provider.

## Tried and ruled out
A named provider example failed tests/bulma-code-review.sh in PR #71. That suite scans skills, agents and commands for product/vendor names. Running only repo.sh, bulma-qa.sh and bulma-lstm.sh did not exercise that guard.

## Watch out
Run the affected workflow suites rather than treating repo.sh as the entire CI pipeline. Keep concrete provider details in the target project's setup docs; discover them at runtime. This changes wording, not the scope of local QA fixture authorization.
