# Fix contract (`PR_BUG` only)

Do **not** spawn or switch to the developer graph from triage.
After QA writes `QA_RESULT` FAIL, the bus pops to developer and
that graph enters **fix** (`apply_qa`).

Copy this block into the `TRIAGE_RESULT` / later `QA_RESULT` body
so the developer `fix` node has a complete contract.

```text
You are bulma_developer in Fix mode for a confirmed PR_BUG.
Follow ../../bulma-developer/SKILL.md (Fix mode).

Constraints:
1. Work on the EXISTING PR branch only.
2. Fix the root cause, not the symptom.
3. Add or update tests when the failure is behavioral.
4. Run the relevant validation (targeted tests / typecheck as needed).
5. Commit the fix.
6. Push to the existing PR.
7. Do NOT create a new PR.
8. Do NOT change unrelated files.

PR: <url>
Repo: <owner/repo>
Branch: <head>
SHA tested: <sha>

Failure:
<one paragraph>

Reproduction:
1. ...

Expected:
<...>

Actual:
<...>

Evidence:
<paths / excerpts>

Root cause:
<triage analysis>

Relevant files:
<paths>

Return:
- commit sha
- files changed
- tests run + result
- PR url (same PR)
```

If the later fix cannot push, stay `PR_BUG` and say what blocked —
do not open a replacement PR.
