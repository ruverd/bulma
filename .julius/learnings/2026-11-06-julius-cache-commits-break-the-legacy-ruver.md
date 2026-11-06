---
title: ".julius/cache commits break the legacy-name check in tests/repo.sh"
author: Ruver
date: 2026-11-06
id: l-10455b25
branch: feat/review-batched-large-prs
touches:
  - tests/lib/__pycache__/frontmatter.cpython-313.pyc
  - tests/repo.sh
---

## Decided
Never commit .julius/cache/ or tests/lib/__pycache__/*.pyc churn; stage files by path instead of git add -A.
## Tried and ruled out
git add -A on a branch: it committed .julius/cache/.cache/julius-branches.json, which carries the legacy product name, and tests/repo.sh legacy-name check failed in CI (repo invariants). Fixed with git rm --cached and restoring the pyc from origin/main.
## Watch out
.julius/cache is not in .gitignore; tests/lib/__pycache__/frontmatter.cpython-313.pyc is tracked on main and changes whenever tests run locally.
