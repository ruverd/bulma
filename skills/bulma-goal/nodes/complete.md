# Node: complete

**Verb:** close the loop.

## Steps

1. Check every line of [COMPLETE.md](../references/COMPLETE.md). All true, or
   this is not complete.
2. `cancel_wake` with `loop_id`. If it fails, report the id in chat. Never leave
   a silent loop running.
3. STATE `status: done`. Clear `loop_id`.
4. Report in the chat language: PR, head SHA, QA verdict, comment URL, evidence
   URL.

## Never

- Claim done without a QA comment carrying evidence on the **head** SHA.
- Merge. Ready is not merge, and ready only follows QA `PASS`.
