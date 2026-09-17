# Node: resume

**Verb:** reconcile and continue. No product code.

Follow [../ARGS.md](../ARGS.md).

1. Load developer STATE, delivery STATE, HANDOFF, bus stack.
2. Replay invariants (fd HANDOFF `## Invariants` if present, then the ARGS.md table). Compare actual vs `# expect:` / STATE. Drift re-enters the node that produced the stale output.
3. If `waiting_user`: treat the current user message as the ASK answer. Log it. Clear waiting. Continue the node that asked.
4. Skip a node only when its outputs exist **and** its invariants match. Matching STATE files is not enough.
5. Hand off to **deliver**, **mergeable**, **bot_review**, **apply_qa**, or **fix** as STATE says.

Missing STATE → stop. Ask for the ticket or the goal. Do not start a blank job.
