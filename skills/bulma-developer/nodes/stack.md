# Node: stack

**Verb:** orchestrate children and umbrella
**Capability:** stack helper, `spawn_worker`, branch preparation, CI and QA handoff, write STACK and JOBS. No product code.

Follow [../STACKED.md](../STACKED.md).

1. On admission, persist `mode=stack`, the validated plan and registry rows.
   On resume, load the same plan. Preserve the per-row job and worker receipts.
2. Reconcile from origin and GitHub. Use the verified active row and actual
   bases. A missing prerequisite or drift stops dependent work.
3. For a new row, prepare its destination and dispatch its feature-delivery
   worker at the verified start SHA. The final row packages and validates the
   integrated tree against parent acceptance.
4. On RESULT, QA return or wake, recheck the active row's head, base and
   gates. CI pending → schedule wake. CI red → bounded fix worker.
   A child with verified CI out of scope may advance on matching local tests.
   Under developer, every PR goes through mergeability and bot review.
   Only the umbrella with `active.qa_required: true` goes to **request_qa**,
   using the full parent acceptance on the current combined head.
   Under fd alone, use its existing CI and evidence gates.
5. After gates, wait for a human to merge that child into the next branch.
   Resume only after verifying the merge result. When the umbrella's gates
   pass, report the release PR and its actual review status.

## Output

`STACK.md` rows, parent status, and the verified order of linked PRs with
destinations. Identify unopened positions as planned.
