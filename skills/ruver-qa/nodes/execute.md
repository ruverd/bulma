# Node: execute

**Verb:** test  
Follow [../references/EXECUTION.md](../references/EXECUTION.md).
Walk `.ruver-qa/PLAN.md` in order. Do not skip `intent: user-break`.
Do not invent extra surface on the scripted walk. Clips:
[../references/VIDEO.md](../references/VIDEO.md). After the last
scripted step, exploratory (dogfood, do not follow `how`).

A red test is evidence, not a verdict.
Product suspicion → append FINDINGS immediately, **continue** the plan
unless the app cannot run (`BLOCKED`).
After the last step, if FINDINGS exist → **request_triage**.
