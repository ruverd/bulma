# Node: verify

**Verb:** judge
**Capability:** read-only on product code. Write STATE dispositions.

Load skill **`receiving-code-review`**. Verify before implementing.
Do not implement in this node.

Fetch reviews + inline comments + issue comments
([GITHUB.md](../references/GITHUB.md)).

Skip a comment only if STATE `processed_comment_ids` already has 👍
**and** a reply on that comment. A review in `processed_review_ids`
is not enough if any of its comments are missing. A new id that
restates old F-ids is still new.

`COMMENTED` is not a skip. Medium / High / Critical in a body-only
review is feedback. Lows / nits: still fill the row. A one-line skip
is allowed only after the checks below.

## Per comment (current HEAD)

Bind the comment to a `path:line` that exists at HEAD (or `path` if
the line moved). If the comment names a symbol, grep it. A disposition
without a bind is not a verify.

Two questions, then a disposition:

| Field | Meaning |
|---|---|
| `claim_true` | yes / no / unknown. Does the claimed defect still reproduce at HEAD? |
| `fix_ok_here` | yes / no / na. Is the suggested change right for **this** codebase (neighbor pattern, YAGNI, would not break)? `na` when the comment does not propose a fix |
| `risk` | low / normal / elevated. Comment text + bound path. Tokens from [ROUTING.md](../../ruver-feature-delivery/ROUTING.md) §Risk (auth, tenant, billing, …). Do not run `classify-risk.py` here (no file list yet) |
| `disposition` | **fix** / **skip** / **unclear** |

| Disposition | When |
|---|---|
| **fix** | `claim_true=yes` and (`fix_ok_here=yes` or `na` with a real defect) |
| **skip** | claim false, already gone, YAGNI, out of scope, or suggested fix wrong for this repo (`fix_ok_here=no`) |
| **unclear** | cannot verify without a fact you do not have |

`skip` must cite a path, test, or DECIDE row. "stale" with no cite is
not a skip.

`risk=elevated`: extra lookup (`how` on the subsystem) before skip.
Do not skip Medium+ auth/tenant/billing because it "looks outdated".

Unclear + last-resort ASK → `waiting_user`, stop.
Otherwise DECIDE skip or fix and log the row.

## Output

STATE `## Dispositions`, one row per in-scope comment:

```text
id | path:line | claim_true | fix_ok_here | risk | disposition | evidence
```

`dispositions` rollup: fix/skip/unclear counts.
