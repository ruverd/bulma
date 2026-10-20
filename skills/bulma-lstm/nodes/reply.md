# Node: reply

**Verb:** acknowledge and complete the review lifecycle.

Commands: [GITHUB.md](../references/GITHUB.md). Enter only after prove passes,
or verify finishes a skip-only run. Never dismiss a failed or unresolved fix.

1. For every in-scope comment, react with 👍 and reply with its disposition,
   final SHA and evidence. Rewrite through bundled `unslop` before POST. English.
   React to the parent review once. Preserve per-comment answers for grouped fixes.
2. Publish one COMMENT summary per final SHA and analyzed comment set, including
   fixed/skipped items, test evidence and remaining concerns. A body-only COMMENT
   review can serve as this summary. Use a stable marker and check existing
   artifacts on resume or ambiguous network failure before posting again.
3. Resolve each conversation whose claim is proved fixed on the final head,
   after its reply. Skip/disputed or unresolved comments stay open.
4. When code changed and prove passed, dismiss active `CHANGES_REQUESTED` reviews
   whose entire feedback, including body findings, is proved addressed. Include
   fix SHA, evidence and summary URL in the dismissal reason. Re-fetch the exact
   review and live head before dismissal. Never dismiss an APPROVED review,
   another unresolved concern, or a request just to unblock merge.
5. Refresh review state. Re-request each original reviewer only when code changed
   and their latest decisive status is not `APPROVED`, overall review decision is
   not `APPROVED`, and they are not already requested. Record successful requests
   by reviewer + fix SHA. A later COMMENTED review does not erase an approval.
6. Record completed replies, resolutions, dismissals, summary URL and requests
   only after GitHub confirms them. Failed permission/API actions remain pending
   and appear in report. Continue independent replies; never claim completion of
   a rejected mutation. New head during mutations returns to verify/prove.

Use `scripts/review-actions.py` with freshly collected state as the deterministic
planner for steps 4–5. Its input and API operations are in GITHUB.md. Recompute
after dismissal rather than replaying an old plan. Dismissal is not approval;
reviewer gates still require the original reviewer to clear their concern.

Skip-only runs still reply and comment, but never dismiss or re-request. A new
comment ID needs its own reply even if it repeats an old finding. `done` requires
all applicable actions confirmed or a report that explicitly names pending API
failures; processed comment IDs alone do not prove the lifecycle completed.
