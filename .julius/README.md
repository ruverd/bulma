# .julius

What coding sessions on this repo worked out, kept next to the code so the
next session, yours or a teammate's, starts from it instead of digging again.

- learnings/   one file per session that took real digging: what was decided,
               what was tried and ruled out, and what to watch out for, plus
               what it took to work out
- hook.cjs     what Claude Code runs at session start (`.claude/settings.json`).
               With julius installed it hands over to julius. Without it, it
               shows Claude these learnings and offers to set julius up.

Commit this folder and `.claude/settings.json` once. After that, commit new
learnings with the change they came from. Learnings are short summaries, never
transcripts, and plain markdown without julius installed. What
`.julius/.gitignore` lists stays on each machine.
