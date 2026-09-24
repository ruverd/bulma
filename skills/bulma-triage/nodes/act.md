# Node: act

**Verb:** route

- Each finding classified `NEW_BUG` → create **one** tracker issue
  ([../references/LINEAR.md](../references/LINEAR.md)). Record ids
  on STATE `tracker_issue_created` (comma-separated).
- `PR_BUG` → no ticket. Do **not** switch to developer. QA verdicts
  FAIL; developer `fix` runs after `QA_RESULT`.
- `EXISTING_BUG` → cite the open issue. No new ticket.
- `NOT_A_BUG` / `BLOCKED` → no ticket.

Always write `TRIAGE_RESULT` (rollup + per-finding table) and **pop**.

Fix payload QA will forward: [../references/DEVELOPER.md](../references/DEVELOPER.md).
