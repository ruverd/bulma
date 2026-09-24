# Blockers: advance as far as you can + draft + wait

When current work **depends** on something that does not exist / is not done
(another ticket, BE endpoint, flag, decision), the graph **does not stop at zero**.
**Advance everything you can** and leave the blocker **explicit** on the
**same tracker** as the current ticket ([PRODUCT.md](PRODUCT.md)).

| `tracker` | Create / comment |
|---|---|
| `linear` | tracker MCP `save_issue` / `save_comment` / `get_issue` ([LINEAR.md](LINEAR.md)) |
| `github_issues` | `gh issue create` / `gh issue comment` |
| `gitlab` | `glab issue create` |
| `none` | Write STATE. Tell the user. Do not invent a tracker workspace |

**Do not** invent that the blocker "is already ready".

## 1. Detect a blocker

| Situation | Action |
|---|---|
| FE needs an endpoint/contract that **does not exist** | block on a BE draft (or existing BE ticket) |
| Current ticket `blockedBy` an open issue | wait loop on that issue |
| Missing critical product / design decision | draft ticket or comment on the parent + wait if needed |
| Only part of the AC is unblocked | implement the unblocked slice; wait on the rest |

## 2. Advance as far as you can (before / during the wait)

Whenever the blocker does not stop 100%:

- Plan + unblocked tickets
- Types/mocks **documented** as temporary only if inevitable (prefer waiting for the real FE contract if a BE draft is created)
- UI shell with DS/refs (loading/empty) if the contract is the only gap
- Tests for what you can already do
- Contract comments on the BE ticket (below)

Record in STATE what shipped and what is still pending.

## 3. Create a draft ticket (same tracker)

If the blocker **has no ticket** yet (e.g. missing API task):

```
save_issue:
  title: "[Draft] BE: <endpoint/contract> for <current ticket>"
  team: <same team as the current ticket>
  state: Draft  # or the team's "Draft" / "Backlog" name — discover via list_issue_statuses
  description: |  (template below)
  parentId: <current issue id>   # if hierarchy fits
  blockedBy: []
  # relation: CURRENT is blockedBy the new draft
```

After creating the draft (`NEW-ID`):

```
save_issue id=<CURRENT>:
  blockedBy: ["NEW-ID"]   # append-only

# and/or on the draft:
save_issue id=NEW-ID:
  blocks: ["CURRENT"]
```

If a blocking ticket already exists → **do not** duplicate; use it + contract comments.

### Draft description template (required)

```markdown
## Explicit dependency

- **Blocks:** <ticket> (<current ticket title>)
- **Why:** current FE/work cannot finish without this contract/endpoint.
- **Target branch (same family):** feature/<id-lowercase> (align with the parent if fullstack)

## Expected contract (fill in and keep updated)

### Endpoint
- Method + path: `POST /v2/...`
- Auth: bearer / roles
- Query/path params: ...
- Request body (JSON / types):
```ts
// TypeScript interface or OpenAPI sketch
```
- Response 200 (JSON / types):
```ts
```
- Errors: relevant 4xx/5xx

### Behavior
- Short business rules
- Idempotency / pagination / filters

### Done criteria for this draft
- [ ] Endpoint implemented + BE tests
- [ ] Stable contract (no breaking vs the sketch below)
- [ ] Ticket marked Done

## How the consumer (<ticket>) will use it
- Screen/flow X calls Y
- Fields shown: ...

## Notes
- Created automatically by bulma-feature-delivery when a blocker was detected.
- Keep comments if the contract evolves.
```

## 4. Comments with the data needed (MCP `save_comment`)

On the **blocking** ticket (draft or existing), add comment(s) when detail is missing:

```markdown
## Contract consumed by <ticket>

**Endpoint:** `GET /api/v2/foo/:id`
**Params:** `id` uuid; query `?include=bar`
**Headers:** Authorization Bearer

**Request:** (n/a or body)
**Expected response:**
```json
{ "id": "...", "name": "..." }
```

**TypeScript (consumer):**
```ts
export interface FooDto { id: string; name: string }
```

**UI use:** Dialog X shows `name`; loading/empty per DS.

**Do not:** change the shape without telling <ticket>.
```

If the contract changes during the wait → **new comment** (do not erase history).

On the **current** (blocked) ticket, optional comment:

```markdown
## Waiting on NEW-ID
- Blocker: Foo endpoint
- Advanced: UI shell / local types / ...
- Next step when Done: wire the client + E2E tests
```

## 5. Loop waiting for ticket `Done`

External blockers resolve on a **human** timescale (hours/days).
**Forbidden** to sleep/poll in-session — the session will not survive the wait.

```
STATE status: waiting_blocker
1. get_issue(blocker_id) via MCP — check ONCE
2. statusType:
   completed/done → resume implement (re-fetch the contract first)
   canceled       → escalate / ASK the user
   still open     → END THE SESSION:
     - STATE: waiting_blocker + blockers[].last_check
     - English message: what you are waiting on, draft link, and
       "when NEW-ID is Done, run /bulma-fd resume"
     - optional: external routine re-invokes (runtime cron) — never sleep
```

**Done** = the team's terminal success state (map with `list_issue_statuses` if needed: `statusType === "completed"` is the safest).

On resume:

- Re-fetch issue + comments (the contract may have changed)
- Implement tickets that depended on the blocker
- Remove temporary mocks if any exist

## 6. Graph integration

```
... plan / fullstack detects a contract gap
 → advance free tickets
 → ensure_blocker_ticket (draft + relations)
 → comment the contract (endpoint, params, types)
 → STATE waiting_blocker → END session
 → `/bulma-fd resume` when the blocker is Done
 → resume implement
 → quality → ship
```

May run **in parallel** with fullstack workers: BE task = draft ticket or BE worker; FE waits if deps.

## 7. STATE

```yaml
blockers:
  - id: ABC-999
    role: api_contract
    status: waiting | done | canceled
    draft_created: true
    last_check: ISO
```

## 8. Anti-patterns

- Stopping without a draft/contract comment
- Empty draft ("do the API") with no shape
- Inventing that the endpoint already exists
- Comment spam every minute
- Full FE with a permanent mock instead of wait + an explicit contract
- Creating a draft without `blockedBy` / a mention of the parent ticket

## 9. Checklist

- [ ] Unblocked tickets advanced
- [ ] Draft or blocking ticket with a dependency description
- [ ] tracker blocked-by / blocks relation
- [ ] Comment with endpoint, params, request/response, types
- [ ] Wait until Done (MCP get_issue)
- [ ] Re-fetch the contract before integrating
- [ ] English summary for the user (what you wait on, draft link)
