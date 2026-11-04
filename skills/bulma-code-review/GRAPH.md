# Code-review graph

```
start (PR url / number / branch)
  → resolve           # SKILL §1–§2
  → review            # patches, spec, axes, bind
  → critic            # no-op when risk=low
  → wait_ci?          # retained analysis, CI pending, no PR artifact
  → publish
  → defer             # CI red / readable-unknown / draft / conflict — issue comment
```

## Edges

| From | Condition | To |
|---|---|---|
| start | always | **resolve** |
| resolve | CLOSED or MERGED | **stop** |
| resolve | draft or conflict | **defer** |
| resolve | another reviewer's change request is open | **review** (COMMENT if the diff is clean) |
| resolve | room unknown from an access or tooling failure | **review** (no Deferred comment) |
| resolve | `ci_overall` pending | **review** |
| resolve | `ci_overall` failure | **defer** |
| resolve | `ci_overall` unknown and `ci-tooling.json` verified false | **review** (CI cell `not verified (tooling)`) |
| resolve | `ci_overall` unknown and CI was readable | **defer** |
| resolve | `ci_overall` success | **review** |
| resolve | `ci_overall` out_of_scope | **review** (publishes like success) |
| wait_ci | still pending | **stop** (loop wakes in 5m) |
| wait_ci | success and retained analysis valid | **publish** (verdict and fresh gates) |
| wait_ci | head/base/context changed | **review** |
| wait_ci | failure, or unknown after a successful CI read | **defer** |
| wait_ci | CI unreadable (`verified: false`) | **publish** the code verdict, CI cell `not verified (tooling)` |
| wait_ci | CLOSED or MERGED | delete loop, **stop** |
| review | always | **critic** |
| critic | CI pending | **wait_ci** (retain analysis) |
| critic | otherwise | **publish** |
| publish | head or base changed | **review** (fresh diff, repeat preflight) |
| publish | approval gate blocked (`gate.py` exit 1) | **defer** only for a real gate; do not dismiss my approval |
| publish | `gate.py` exit 3 (only bot approvals on head) | **publish** as COMMENT |
| publish | `gate.py` exit 4 (open change request) | **publish** as COMMENT |
| publish | `gate.py` exit 5 (CI or evidence unreadable) | **publish** as COMMENT, no Deferred comment |
| publish | posted | delete loop, **stop** |
| defer | posted | delete loop, **stop** |

`--force` skips failure/unknown inspection gates and goes to **review**.
Pending CI always allows review but never publication.
`--dry-run` never creates a loop and never posts.
Room evidence is loaded before pass selection. All approval gates run again
at publish, including promotion. See [PREFLIGHT.md](references/PREFLIGHT.md).

## Nodes

`nodes/wait_ci.md` · `nodes/review.md` · `nodes/critic.md` ·
`nodes/publish.md` · wait mechanics in [LOOP.md](LOOP.md)

Defer stays in [nodes/publish.md](nodes/publish.md) (issue comment).
