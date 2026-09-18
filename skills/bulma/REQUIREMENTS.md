# Requirements

Bulma needs TypeSafe Jev. Everything else in this repo does not.

## Doctor

`scripts/bulma.py doctor` checks, in order:

| Check | Pass | Fail |
|---|---|---|
| `python3` | 3.9 or newer | exit 2 |
| `TYPESAFE_API_KEY` | set in the environment | exit 2 |
| `decisions.json` | parses and validates | exit 4 |
| `$RUVER_HOME/bulma.json` | parses, or is absent | exit 4 |
| power | resolves to a known level | exit 4 |
| Jev | `GET /v1/models` answers within 5 s | exit 3 |

`--offline` skips the last check. `--json` prints the same as a document.

## Requirement message (exit 2)

Printed by the script in English. `admit` repeats it in the chat language
and stops with `status: blocked`.

```text
/bulma needs TypeSafe Jev.
  missing: TYPESAFE_API_KEY  (create one at https://console.typesafe.ai)
  python3: ok (3.13.9)
Set the key, then run /bulma again.
Without Jev, run the graph directly: /developer, /qa, /reviewer, /lstm, /ruver-triage.
```

Exit 3 prints `Jev unreachable.` with the status or error instead; `admit`
stops the same way. After `admit`, a failed call is not fatal: the hook
falls back to the graph rule, the ledger row says `acted=false
note=error:...`, and the run continues.

## Data handling

State sent to Jev leaves the machine: ticket text, changed file paths and
hunk headers, review comments, CI log tails, QA findings. The script redacts
common credential shapes (`ghp_`, `github_pat_`, `sk-`, `apikey_`, `AKIA`,
`Bearer ...`, `password=`) and caps size (8,000 characters per string,
90,000 total). That is a filter, not a guarantee. Never put whole files in
the state; HOOKS.md caps are the budget. TypeSafe's terms and data handling
page apply to what is sent.

## Install

Nothing to install beyond `python3`. Create a key at the TypeSafe console,
then in your shell profile:

```sh
export TYPESAFE_API_KEY="..."
```

`ruver status` prints `jev ok` or `jev missing (optional)`. The Python and
JavaScript TypeSafe SDKs are not required; the script speaks HTTP directly.
