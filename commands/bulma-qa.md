---
description: QA a PR (agent-browser or HTTP). Happy and user-break from the diff. Hands potential bugs to bulma_triage.
argument-hint: "<PR url or owner/repo#N>"
---

# /bulma-qa

Short alias: **`/qa`**.

Follow **`../skills/bulma-qa/SKILL.md`** in full.

Use arguments from the user request.

PR link is required. If the user passed a number, resolve it in the
current repo. If nothing was passed, ask.

Do not mark FAIL on a suspected product bug until `bulma_triage`
confirms, unless the failure is unambiguous.
