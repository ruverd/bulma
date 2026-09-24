# Node: apply_qa

**Verb:** route  
**Capability:** read envelope, write STATE

Read `QA_RESULT`. Follow the GRAPH apply_qa edges.
Write `qa_verdict` and any tracker ids from the envelope notes.

**Log the lap before routing.** Append one row to `qa_verdict_log`: lap number,
tested sha, verdict, `triage_class`, and the finding ids the envelope carries.
`qa_verdict` is a single field that the next lap overwrites, so this table is
the only record that the ring turned at all.

Then decide, in this order:

1. Finding id already in the log from an earlier lap → **escalate**. The same
   defect survived a fix, so another lap buys nothing. Cheaper than waiting out
   the cap, and it is the failure that actually happens.
2. `qa_fix_loops_used` has reached `qa_fix_loops` → **escalate**, quoting the
   log so the reader sees what changed each lap.
3. Otherwise increment `qa_fix_loops_used` and route per the GRAPH edge.
`PENDING_TRIAGE` → stay put. `PASS` with `NEW_BUG` → cite tickets,
do not pad this PR.

On **`QA_RESULT` PASS** (including PASS + NEW_BUG / EXISTING_BUG /
NOT_A_BUG when this PR's ACs still hold): mark the PR Ready for
Review — `gh pr ready "$PR" --repo "$REPO"`. Confirm `isDraft=false`.
Still **never merge**.

Do not invent product behavior on ambiguity → escalate.
Do not dequeue the next QA here — `verdict` does that after
this node returns.
