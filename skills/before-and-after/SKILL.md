---
name: before-and-after
category: lib
description: >
  Use when a GitHub PR needs before/after UI stills on the body, or
  when ruver-qa / the shipper captures those stills with agent-browser.
---

# Before and after

Stills on the **PR body**. Video is QA's job (`gh pr comment --attach`).
Browser work is `agent-browser`. This skill owns session, capture
inventory, height alignment, and the marked block.

Run it headless. `agent-browser` launches its bundled Chrome for Testing
process as the rendering engine; that process is expected. It must include
`--headless=new` and must not open a visible window or the user's
`/Applications/Google Chrome.app`. Never use `--headed`, `--auto-connect`,
`--cdp`, `--profile`, the OS `open` command, or a host browser MCP.

Load `agent-browser skills get core` before clicking. Do not copy
vercel-labs/before-and-after (`format.mjs` is PolyForm Shield). Use
the scripts here (MIT).

## When

- Shipper, `forge=github`, the diff has UI (routes, screens, widgets,
  layout/CSS). After `gh pr create` / update.
- `/qa` on a GitHub UI PR whose body lacks the marked block
  (PR opened elsewhere, or capture failed at ship).

Skip: API-only, `--no-pr`, `forge=git` / `gitlab`, docs/chore with
no screen. Missing `agent-browser` on a UI PR is **BLOCKED**, not a
Playwright fallback.

## Session

Not per-worktree. Base and HEAD share cookies:

```bash
eval "$(../before-and-after/scripts/ensure-session.sh)"
agent-browser --session "$SESSION" --session-name "$SESSION" \
  --headed false open "$URL"
```

State: `$RUVER_HOME/agent-browser/ruver-<owner>-<repo>/`. Never git.
Never Chrome `--profile Default`.

After session restore, open a gated route. Login form still up → repo helper
(`qa:otp` / `qa:login`, `docs/ai/qa-login.md`, `AGENTS.md`) → continue
with `--session-name "$SESSION"` so the next run skips login.

Authenticate until the gated app route loads in that agent-browser session,
then `agent-browser --session "$SESSION" --session-name "$SESSION"
--headed false record start` with no URL and no `--state`
(ruver-qa `references/EXECUTION.md`). `record start`
opens a **new tab**. If that tab is Sign in / Check your email,
restore auth with the repo's documented helper into **that session** and
wait for the app shell before walking. Film and snapshot the same tab. A
login-wall `.webm` is never PASS.

## Inventory

Same surfaces as ruver-qa PLAN.md. One still per changed route (or
each host screen of a shared widget). **Desktop always.** Mobile only
when the diff touches layout, CSS, media queries, or the design
system. New route: after-only (`--before -`).

## Capture (shipper)

1. `command -v agent-browser` or stop (PR still opens; no fake block).
2. `eval "$(../before-and-after/scripts/ensure-session.sh)"`.
3. Merge-base worktree, start the app (AGENTS.md / `package.json`
   `dev`/`start`). Same origin and port as HEAD, **in sequence**.
4. Restore session. Screenshot each surface into `$CAPTURE_DIR`
   (`desktop-before.png`, …). Paths: no whitespace.
5. Stop that app. HEAD worktree, same port, same routes, `*-after.png`.
6. Equal height: read `document.documentElement.scrollHeight` on both,
   pad **below** the shorter page, `--full` screenshot. Confirm pixel
   height matches. Component diffs: same selector, no padding.
7. Reject login walls, blank frames, app errors, loading skeletons.
8. After all captures, `agent-browser --session "$SESSION" close`.
   `--session-name` keeps auth for the next run.

Cannot start the app or auth helper: open the PR without the block.
Do not invent a screen.

## Publish stills

Run from the product repo (the cwd `gh` uses):

```bash
../before-and-after/scripts/format.sh \
  --body-file /tmp/pr-body.md \
  --before "$CAPTURE_DIR/desktop-before.png" \
  --after  "$CAPTURE_DIR/desktop-after.png" \
  --label Desktop \
  > /tmp/pr-body-next.md

ATTACH=()
while IFS= read -r f; do ATTACH+=(--attach "$f"); done < <(
  ../before-and-after/scripts/format.sh --attach-list \
    --before "$CAPTURE_DIR/desktop-before.png" \
    --after  "$CAPTURE_DIR/desktop-after.png"
)
gh pr edit "$PR" --body-file /tmp/pr-body-next.md "${ATTACH[@]}"
```

Marker `<!-- ruver-before-and-after:start/end -->`. Replace that
block only. Place it near the top, after the opening summary, before
Details/Testing. Confirm the body has no leftover `./captures` paths.

`gh` must be ≥ 2.99 (`--attach`). Older CLI: skip the block, say so.

## `/qa`

Walk the plan with agent-browser. Record the plan walk (happy
and user-break) to `.webm`.
Product errors still FINDINGS → triage → FAIL.

If the body has no block and `forge=github`, capture the pair (base
worktree vs HEAD) and publish as above, then comment.

## Never

- Playwright / Cypress / host MCP as the agent's hands
- Video in the PR body
- `state save` inside the app repo
- Two browser executes at once (QA slot)
- PASS on a UI PR with no video
- PASS on a login-only .webm
