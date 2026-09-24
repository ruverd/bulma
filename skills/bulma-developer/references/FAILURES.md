# Failure classes (developer)

Do not assume the implementation is wrong.

| Class | Meaning | Action |
|---|---|---|
| Implementation | Change introduced or exposed it | Fix the code |
| Test | Test/fixture/mock wrong | Fix test or code with evidence |
| CI / infrastructure | Runner, registry, network, Actions | Retry; do not change app code |
| Environment | Missing env, auth, services | Diagnose; report blocker |
| Requirement ambiguity | Behavior cannot be inferred | Search repo + tracker first; ask only if still blocked |

Never hide a failure. Never `--no-verify` to "pass".

Unrelated bugs: do not silently expand the PR. Record them. Recommend
or create a separate tracker issue when appropriate (search first;
assignee = current tracker user / Todo — same rules as `bulma-triage` LINEAR.md).
