# Handoff Claude Code ↔ Grok (usage limit)

When the current runtime (Claude Code **or** Grok) is **near a usage/context
limit**, **do not abandon** the task: write a continuity artifact and
**continue on the other runtime** until CI green / delivered.

## Signals of "limit near"

Treat as handoff if **any** of these:

- UI/CLI warning of usage limit / rate limit / "approaching limit"
- Session context **very full** (slow re-reads, truncates, aggressive compaction)
- Estimate: expensive phases still remain (quality + CI loops) and most of the budget
  already went to grill/implement
- User asks to "continue on Grok/Claude"

**Do not** wait for a hard stop without an artifact.

## What to write (required)

Everything under **`$RUVER_ROOT`** ([DISK.md](../ruver-bus/DISK.md)) — **never**
the git root, a worktree, or `git add`:

```
$RUVER_ROOT/.ruver-feature-delivery/
  STATE.md              # current status (already exists)
  HANDOFF.md            # this handoff (template below)
  tracker-context.md     # if any
  mcp-sources.md
  *-context.md
```

Claude and Grok on this Mac read the same `$RUVER_ROOT`. Do not commit.

## Template `.ruver-feature-delivery/HANDOFF.md`

```markdown
# Ruver-FD Handoff

- **from_runtime:** claude-code | grok
- **to_runtime:** grok | claude-code
- **written_at:** ISO-8601
- **reason:** usage_limit_near | context_full | user_request

## Goal
<one line>

## Tracker
- id: <ticket>
- branch: feature/<id-lowercase>
- url:

## Position in graph
- status: handed_off (full enum: STATE.schema.md)
- active_runtime: <to_runtime>
- position: <node> (full enum: STATE.schema.md `status`)
- path: <path> (full enum: STATE.schema.md)
- risk: <risk> (full enum: STATE.schema.md)
- scope: <scope> (full enum: STATE.schema.md)
- mcp_gate: <gate> (full enum: STATE.schema.md — `passed_partial` is real,
  do not flatten it to passed or failed)

## Done so far
- [ ] short bullets

## Next steps (ordered, concrete)
1. ...
2. ...

## Open tickets / blockers
- ticket N: ...
- blocker DEV-YYY: waiting | contract in comment

## Repo / worktrees
- frontend path / PR:
- backend path / PR:
- orca run_id: (if fullstack)

## Do NOT redo
- MCP full re-fetch unless mcp_gate failed
- Re-grill settled decisions / rewrite SPEC.md if it exists
- Re-implement finished tickets

## Invariants

Read-only snapshot. Resume replays each command and compares to `# expect:`.
Drift re-enters the node that produced the stale output. Match may skip.

```bash
git rev-parse HEAD                    # expect: <sha>
git branch --show-current             # expect: <branch>
git status --porcelain                # expect: empty or the known in-progress files
```

If a PR exists:

```bash
gh pr view --json headRefOid,mergeable -q .headRefOid   # expect: <sha>
gh pr checks --json bucket -q '.[].bucket'              # expect: matches STATE.ci
```

If a tracker id exists, re-read it. `updatedAt` newer than STATE `updated_at`
and the AC changed: re-read AC. Do not re-grill settled decisions unless an AC
line contradicts a DECIDE row.

## Pass criteria (delivery)
- [ ] thermo fix all done
- [ ] PR(s) open
- [ ] gh pr checks ALL green
- [ ] status done only after CI green

## Commands for resume
```text
# in the correct repo/worktree, on branch feature/<id-lowercase>
/ruver-fd resume
# or
/ruver-feature-delivery resume from $RUVER_ROOT/.ruver-feature-delivery/HANDOFF.md
```
```

## How to resume

### On Grok (coming from Claude)

1. Open a Grok session on the **same repo/worktree** (or `git fetch && checkout branch`).
2. Confirm `$RUVER_ROOT/.ruver-feature-delivery/HANDOFF.md` + `STATE.md`. If missing:
   **rebuild** from git/gh/tracker (fallback), do not restart from a raw goal.
3. Invoke: **`/skills ruver-feature-delivery`** and ask **resume**
   (`/ruver-fd` **does not exist** as a Grok slash command — those are built-in).
4. **RECONCILE first** (required): replay `## Invariants`. Compare actual vs
   `# expect:`. Drift is information. Unverified "done" becomes "unknown" and
   is re-checked. PR already exists → do not recreate. Skip a node only when
   its outputs exist **and** its invariants match. Then run **Next steps**.
5. Write `active_runtime: grok`. Continue until **CI green**.

**Autonomy:** Grok on this setup runs `permission_mode = always-approve` — push,
PR, and CI fixes happen **without a human prompt**. The resume message to the user
must say that.

### On Claude Code (coming from Grok)

Same: checkout branch, `/ruver-fd resume` (real command on Claude), **RECONCILE**,
`active_runtime: claude-code`, follow HANDOFF.

### Fullstack

Include in HANDOFF: worktree paths, which worker stopped, Orca `run_id` if used.
Resume workers with the same branch name; do not recreate worktrees if they exist.

## Message to the user (English, short)

```text
S: limit near on this runtime (claude|grok)
D: wrote $RUVER_ROOT/.ruver-feature-delivery/HANDOFF.md + STATE (global, not git)
P: open the other runtime on branch <feature/<id-lowercase>> and run:
   Claude: /ruver-fd resume · Grok: /skills ruver-feature-delivery + "resume"
   (note: Grok runs always-approve — push/PR with no prompt)
   Continues from: <next>
```

## Economy on handoff

- HANDOFF ≤ ~80–120 lines; details stay in context files already on disk.
- Do not paste huge diffs into HANDOFF — only `git status` / paths.
- The other runtime **reads disk**; it does not need the previous session transcript.

## Anti-patterns

- Resuming without RECONCILE (git/gh vs STATE) — duplicate PR, reimplemented ticket
- Two runtimes active on the same branch (check `active_runtime` before acting)
- Stopping at the limit without HANDOFF
- Asking the user to "explain the ticket again" if tracker-context.md exists
- Re-grilling from zero on runtime B
- Declaring delivered without CI green after handoff
