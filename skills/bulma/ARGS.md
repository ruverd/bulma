# Args

`$ARGUMENTS` (and the rest of the user message) resolve to **one** mode. Run
this table **before** any Jev call. Trim, then match in order.

| Args | Mode |
|---|---|
| empty | **inventory** → `entry.next_step` |
| `power [shadow\|cautious\|balanced\|bold]` | print or set the global level; stop |
| `power <level> <hook>` | set one hook's level (`power_by_hook`); stop |
| `tune <hook.question> <0.50-0.99>` | per-question `act_at`; stop |
| `model [<id>]` | print or pin the model; stop |
| `report [--hook H] [--since D] [--repo-only]` | calibration table; stop |
| `status` | STATE + power + last five ledger rows; stop |
| `doctor` | run doctor and print; stop |
| `resume` | **inventory** → `entry.next_step` restricted to `resume:*` candidates |
| tracker id `[A-Z][A-Z0-9]+-\d+` or tracker issue URL | **developer** directly, no Jev |
| only PR or MR URLs, or `owner/repo#N` (one or more) | **inventory** per PR → **qa** when `pr.author_is_user`, else **reviewer**; no Jev |
| PR or MR URL plus other words | **inventory** with PR facts → `entry.route` |
| free text | **inventory** → `entry.route` |
| `--power <level>` anywhere | override for this run only |

When STATE has `waiting_user` and args are not a verb, args are the answer
to the pending question: a candidate id (`lstm:pr-805`), a target name, or
the user's own words. Log it, clear `waiting_user`, continue at **route**.

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
```
