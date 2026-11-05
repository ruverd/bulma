---
title: git add -A pulls julius cache into commits and fails legacy-name CI
author: Ruver
date: 2026-11-05
id: l-dafcafbb
branch: fix/review-no-human-review-phrasing
touches:
  - tests/lib/__pycache__/frontmatter.cpython-313.pyc
  - tests/repo.sh
---

## Decided
Stage explicit paths in this repo. Commit only .julius/learnings/, never .julius/cache/.

## Tried and ruled out
`git add -A` after running tests committed .julius/cache/.cache/julius-branches.json (it lists branch names that contain the legacy product name) and a rewritten tests/lib/__pycache__/frontmatter.cpython-313.pyc. tests/repo.sh legacy-name failed in CI; fix was `git rm --cached` the cache file and restore the pyc from origin/main.

## Watch out
.julius/cache/ and __pycache__/ are not gitignored on main, and the pyc is tracked, so every local test run dirties it.
