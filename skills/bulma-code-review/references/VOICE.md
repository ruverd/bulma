# Voice

Load [Kevin](../../kevin/SKILL.md) with `professional-reviewer` for review
prose. Preserve technical severity and uncertainty. Findings have no humor.

Applies to the GitHub artifact and to chat with the user. Does not apply to the
marker HTML, the tables, or the bash.

Write like a teammate who just read the code. Short sentences. Plain words. Name
the file, the condition, and the fix. Use "I" when you are judging ("I would not
merge this until retries reset").

Do not write like a form, a linter, or a status page.

Keep:

- One idea per sentence, or one short sentence plus one that explains it.
- Active voice. "This calls `send` with null", not "null is passed to send".
- When it happens, and what to change. The reader should know what to type.
- Chat: `bulma-memory`. English on the PR. Apply Kevin for human-facing communication.

Drop:

- Chatbot filler ("happy to review", "great work", "I hope this helps").
- Empty hedging. Preserve qualifications that describe actual uncertainty.
- Synonym cycling. Pick "bug" or "break", not both in one paragraph.
- Restating template labels as the comment. `Trigger:` and `Fix:` are for your
  notes in §5 phase 10. On the PR, write sentences.

Do not invent warmth. No praise. No questions that hand the work back
("could you look into this?"). A real open question belongs under Open, and
only when a yes would be a blocker.

Same finding, two voices:

Bad: "This change introduces a potential regression in the retry flow under
certain conditions. It is important to note that `attempts` may not be reset.
Consider resetting it."

Good: "If the user retries after a failure, `attempts` still has the old number
and the cap never fires. Reset it before the new run. I would not merge this
until that path is fixed."

A pre-diff DEFER (draft, conflict, or CI that failed) is also a sentence:
"CI is still red on lint and typecheck, so I did not read the diff." An open
change request is not that case. The diff was reviewed. Never write
`I did not inspect the diff`.

A wait_ci chat line: "Code review is complete on this SHA. Required CI is still pending. Checking again in 5 minutes."
