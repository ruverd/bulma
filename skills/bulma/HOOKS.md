# Hooks

One row per Jev decision. The first column is the `id` in `decisions.json`;
`tests/lib/check_bulma.py` fails when the two disagree. `graph/node` names
where the running graph is when the hook fires. `state recipe` says what the
orchestrator puts in the state JSON and how much (caps are characters).
`graph-answer` is what the graph's own rule says; pass it with
`--graph-answer q=v` whenever it is cheap, always under `shadow`. `apply` is
what to do with `act: true`; `act: false` always means the graph's own rule.

| hook | graph/node | fires when | state recipe | graph-answer | apply | outcome hook |
|---|---|---|---|---|---|---|
| `entry.route` | bulma / route | args are a PR or MR URL, `owner/repo#N`, or free text | `args`: raw text. `world`: `world.json` minus `prs[]` (keep `stack_top`, `jobs`, `states[]` trimmed to graph/status/waiting_user). `pr`: `world.json.pr` when a URL was given. `user_login`: `world.json.user` | none | `target` acted -> **spend** then overlay; `none` -> answer in chat and stop | none |
| `entry.next_step` | bulma / route | args empty or `resume` | `args`, `candidates`: `world.json.candidates[]` (id, target, why), `world`: same trim as above. `--criteria .ruver-bulma/candidates.json` | none | `user_blocked` decisive-yes -> print the pending question(s) first. `candidate` acted -> **spend** then overlay with that target. Else print top 3 with probabilities, one question, `waiting_user` | none |
| `entry.spend` | bulma / spend | after route has a target, before overlay | `args`, `target`, `target_args`. `ticket_title`, `ticket_body` (cap 6000), `acceptance_criteria`: tracker fetch, `world.json.pr`, or args. `--criteria` this session's model catalog plus `inherit` | `bulma.py spend --target` for `effort`; `inherit` for `session_model` | per field: `--effort` / `--session-model` flag wins; acted -> Jev; else graph-answer. Then host `session_effort` and `session_model`. `spawn_worker` gets the same pair | none |
| `fd.triage` | ruver-feature-delivery / triage | fd `triage` node, before writing `## Route (triage)` | `goal`: user text. `ticket_title`, `ticket_body` (cap 6000), `acceptance_criteria` (list): from the tracker context file summary. `topology`: PRODUCT.md discovery (`repos`, `sibling`, `pkg`). `files_mentioned`: paths named in the ticket. `labels`: tracker labels | ROUTING.md heuristic per field | per field: acted -> write Jev's value; else heuristic. `route_confidence`: `high` when `path` acted, `medium` when within 0.10 below `act_at`, else `low`. `route_reason` cites `decision_id` | none |
| `policy.ask` | ruver-feature-delivery / grill (also any DECISION_POLICY fork, lstm `unclear`) | orchestrator reaches a fork with two or more options and would consider ASK | `fork` (one sentence), `options` (list, each one line), `evidence` (paths, tracker facts, cap 3000), `recommendation` (one line), `acceptance_criteria` | DECISION_POLICY verdict `ASK` or `DECIDE` | ASK only when `important` and `uncertain` are both decisive-yes. Else DECIDE and write the `## Decisions` row with `Confidence:` from Jev | none |
| `qa.gate` | ruver-qa / execute | after the last planned step, per finding, before choosing `verdict` vs `request_triage` | `finding`: steps, expected, actual, evidence path (cap 4000). `pr.acceptance_criteria`, `pr.description` (cap 3000), `pr.files` (paths), `env_notes` | `FAIL` when VERDICTS.md items 1-5 hold, else `triage` | unambiguous FAIL only when the two facts (`reproduced_twice`, `evidence_attached`) hold AND `violates_pr_ac` yes AND `in_changed_code` yes AND `env_or_flake` no, all decisive. Otherwise `request_triage`. Never PASS from Jev | none |
| `triage.classify` | ruver-triage / classify | per finding, before the per-finding class row | `finding` (cap 4000), `reproducible` (yes/no/unknown), `pr.files`, `pr.hunks` (hunk headers only), `pr.description` (cap 3000), `open_issues` (id + title, max 10), `env_notes` | the orchestrator's own class | acted -> that class. Rollup by priority stays in `classify.md` | developer `apply_qa`: same finding id recurs after a `PR_BUG` fix -> `outcome <id> class reversed` |
| `lstm.verify` | ruver-lstm / verify | per in-scope comment, after binding `path:line` at HEAD | `comment` (body, cap 3000), `bound_path`, `bound_code` (+/- 20 lines), `neighbor_pattern` (one paragraph), `spec_bullet` | the orchestrator's own `claim_true` / `fix_ok_here` / `risk` | disposition derived in code: `fix` when `claim_true` yes and `fix_ok_here` in {yes, na}; `skip` when `claim_true` no or `fix_ok_here` no; else `unclear` (then `policy.ask`). Undecided Jev field -> orchestrator judgment for that field | lstm `prove` fails after a `fix` disposition -> `outcome <id> claim_true reversed` |
| `reviewer.failure_class` | ruver-reviewer / diagnose | a required check is red | `check_name`, `log_tail` (<= 200 lines, redacted), `pr.files`, `same_fail_on_base` (yes/no/unknown), `mergeable` | the orchestrator's own class | acted -> that class in `failure_class` and the report status | user corrects the class in chat -> `outcome <id> class reversed` |
| `review.risk` | ruver-code-review / critic | the engine runs `scripts/classify-risk.py` | `pr_title`, `pr_body` (cap 3000), `files` (paths), `changed_files`, `churn` | the script's `high` / `low` | spawn the high-risk critic when the script says `high` OR Jev says `high` and acted. Jev `low` changes nothing. Verdict phases untouched | none |

## State file

Write state JSON to `$RUVER_ROOT/.ruver-bulma/state/<hook>-<UTC ts>.json` and pass it with `--state`. Keep the file; humans read it if a decision looks wrong. Never put full files in it; observe caps and budgets.

## Context

Always pass `--context repo=<owner/repo> pr=<number> sha=<head> ticket=<id>` with what is known. Empty is fine.
