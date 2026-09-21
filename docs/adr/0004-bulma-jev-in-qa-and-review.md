# 4. Jev inside the QA walk and the review verdict

Status: accepted. Date: 2026-09-21. Extends
[0003](0003-bulma-jev-at-forks.md).

Context: 0003 put Jev at nine one-shot forks and drew the boundary at
"code-review verdict and deterministic tables stay in code". Two costs stayed
outside that boundary. A `ruver-qa` screen step spends most of its wall clock
in a read-think-click loop: the session model reads a snapshot, reasons about
it in prose, emits a command, repeats. Every cycle is a full model turn for a
decision whose whole answer space is visible in the snapshot.
[jev-ultrafast](https://github.com/browser-use/jev-ultrafast) (Browser Use ×
TypeSafe) shows the alternative: an indexed action space, the operation and
every target answered in one request, and a measured median of 9.45 s → 7.09 s
with browser protocol calls dropping 1,092 → 101 on their benchmark task. The
second cost is the review verdict. The table that picks APPROVE is
deterministic arithmetic, but two of its inputs are judgment: which tier a
finding belongs to, and whether the coverage rows actually cover the diff.
Those were being decided once, in the session model's head, with no number and
no record.

Decision: three more hooks in `skills/bulma/decisions.json`.

`qa.browse` fires per observation at `ruver-qa` execute. `scripts/browse.py
state` turns one `agent-browser snapshot -i --json` into an element table and
one criteria head per operation that takes a target. One request answers
`operation` plus `click_target`, `type_text_target` and `select_target`;
`scripts/browse.py resolve` keeps the head the operation names, discards the
speculative ones, and prints a single `agent-browser` argv. agent-browser
already hands out `@eN` refs, so those refs are the action space and no index
layer was invented.

`review.severity` fires per surviving finding and `review.verdict` once per
run, both at `ruver-code-review` verdict. Together they answer whether the run
may approve.

Boundaries, tighter than 0003's on purpose:

- A ref that was not in the observed snapshot never resolves to a command. Jev
  output never becomes a selector, a coordinate, a shell command or
  JavaScript. `TYPE_TEXT` takes its string from the session model.
- `DONE` ends the navigation loop and proves nothing. `pass_if`, the clips and
  `VERDICTS.md` decide the step exactly as without Jev, so a fast walk cannot
  buy a PASS.
- Severity is asymmetric. Raising a tier needs only a confident answer;
  lowering the reviewer's tier needs a confident tier **and** a decisive-no on
  `introduced_by_pr` — which is the pre-existing clause the review contract
  already has in writing. Jev can make a review stricter freely and can relax
  it only through an existing rule.
- Jev never produces an APPROVE. `review.verdict` can only turn an APPROVE the
  table would have posted into a DEFER, or leave it alone. The CI gate, the
  coverage rows and the `pass=deep|light` marker still hold.
- The verdict arithmetic itself stays in `ruver-code-review`. 0003's rule
  holds: Jev picks among options the node already has.

Consequences: `browse.py` exit 5 ("no actionable decision") is the ordinary
fallback, not an error — that cycle is driven by hand and the walk continues,
so a missing key or a Jev outage costs speed and nothing else. `ruver-qa` and
`ruver-code-review` are still unedited and still run without a Jev key.
`tests/lib/check_bulma.py` gained a parser so the severity criteria stay
pinned to the tier table in `ruver-code-review/nodes/verdict.md`. Both review
hooks are `stakes: high`: run them under `shadow` and read `/bulma report`
before letting either act.
