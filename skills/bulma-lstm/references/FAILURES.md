# Failure classes (LSTM)

| Class | Action |
|---|---|
| Review still valid | **fix** |
| Review stale / wrong / YAGNI | **skip** + cite (path, test, or DECIDE) |
| Patch did not address the comment | **prove** fail → patch; do not dismiss |
| Merge conflict | rebase, always |
| Test / CI red after patch | fix or escalate; never `--no-verify` |
| Unclear product / security | ASK last resort or escalate |
| Unrelated bug | note; do not pad this PR |
| Comment with no 👍 or no reply | reply is not done; go back |
| `CHANGES_REQUESTED` still on a processed review | dismiss it ([GITHUB.md](GITHUB.md)); 403 → note, do not fake success |
| GitHub reply posted without unslop | rewrite and POST again; never leave the first draft |
