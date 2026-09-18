# Args

`$ARGUMENTS` (and the rest of the user message) resolve to **one** mode. Run
this table **before** any Jev call. Trim, then match in order.

| Args | Mode |
|---|---|
| empty | **inventory** → `entry.next_step` |
| `power [shadow\|cautious\|balanced\|bold]` | print or set the global level; stop |
| `tune <hook.question> <0.50-0.99>` | per-question `act_at`; stop |
| `model [<id>]` | print or pin the model; stop |
| `report [--hook H] [--since D] [--repo-only]` | calibration table; stop |
| `status` | STATE + power + last five ledger rows; stop |
| `doctor` | run doctor and print; stop |
| `resume` | **inventory** → `entry.next_step` restricted to `resume:*` candidates |
| tracker id `[A-Z][A-Z0-9]+-\d+` or tracker issue URL | **developer** directly, no Jev |
| PR or MR URL, or `owner/repo#N` | **inventory** with PR facts → `entry.route` |
| free text | **inventory** → `entry.route` |
| `--power <level>` anywhere | override for this run only |
| `--effort <low\|medium\|high\|max>` anywhere | implementer effort for this run; skip that Jev question |
| `--session-model <id>` anywhere | implementer model id from **this host catalog**, or `inherit`; skip that Jev question |

`--effort` and `--session-model` are the coding session that will do
the work, not Jev (`model` above). Both set → skip `entry.spend`.
Details: [SPEND.md](SPEND.md).

When STATE has `waiting_user` and args are not a verb, args are the answer
to the pending question: a candidate id (`lstm:pr-805`), a target name,
an effort level, `ok`, `inherit`, a catalog model id, or the user's own
words. Log it, clear `waiting_user`, continue at **route** (or **spend**
when that was the question).

Examples:

```text
/bulma
/bulma DEV-4772
/bulma https://github.com/org/repo/pull/805
/bulma review the api pagination PR
/bulma power cautious
/bulma tune fd.triage.path 0.70
/bulma report --hook lstm.verify
/bulma --power bold
/bulma --effort low DEV-4772
/bulma --session-model inherit --effort medium review the pagination PR
```
