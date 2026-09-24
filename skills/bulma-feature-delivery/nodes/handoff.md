# Node: handoff (limit / cross-runtime)

**Verb:** checkpoint
**When:** usage limit near, context full, or user asks to switch Claude↔Grok

## Mission

1. Persist continuity in `$BULMA_ROOT/.bulma-feature-delivery/HANDOFF.md` + STATE (global, [DISK.md](../../bulma-bus/DISK.md)).
2. **Do not** `git add` / commit those files.
3. Instruct the user (short English) to open the **other** runtime and `/bulma-fd resume`.
4. **Do not** abandon delivery (CI green remains the target on the other side).

Follow [HANDOFF.md](../HANDOFF.md) + [TOKEN_ECONOMY.md](../TOKEN_ECONOMY.md).

## Steps

1. Update STATE: `status: handed_off`, `active_runtime: <destination>`, tickets, ci, blockers.
2. Fill the compact HANDOFF template.
3. Do not commit. The other runtime reads `$BULMA_ROOT` on this Mac.
4. S/D/P message to the user with the resume command **per runtime**
   (Claude: `/bulma-fd resume` · Grok: `/skills bulma-feature-delivery` + "resume").
5. `result: handed_off` — stop this runtime cleanly.

## Resume (on the destination runtime)

1. Read HANDOFF + STATE.
2. **RECONCILE** (git/gh vs STATE): unverified "done" → "unknown" and re-check.
3. Skip `Do NOT redo` only for what was verified; run `Next steps` until CI green.
4. Switch `active_runtime` to itself.
5. Economy: do not re-fetch MCP if gate passed and files exist.
