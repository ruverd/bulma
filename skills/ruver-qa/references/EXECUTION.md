# QA execution

Walk [PLAN.md](PLAN.md) (`.ruver-qa/PLAN.md`). That file is the
surface. Do not skip steps. Do not add ad-hoc screens unless a step
is impossible without them (record the extra step in PLAN.md first).

UI execute is **agent-browser** only. Do not run the app's Playwright
or Cypress suite (`e2e_cmd` is CI). Load
[before-and-after](../../before-and-after/SKILL.md) for session,
stills, and attach. Load `agent-browser skills get core` before
clicking.

Run agent-browser headless. It launches bundled Chrome for Testing as its
rendering engine; that process is expected. It must include `--headless=new`
and must not open a visible browser window or the user's Google Chrome.app.
Never use `--headed`, `--auto-connect`, `--cdp`, `--profile`, the OS `open`
command, or a host browser MCP. If agent-browser fails, report `BLOCKED`.
Do not switch tools.

## Per step

1. If `kind` is `endpoint` and there is no UI: HTTP the changed
   path. Record status + body excerpt.
2. If `kind` is a screen / widget / visual / state: agent-browser.
   Restore the shared session, then follow that step's `how`
   (happy or user-break).
3. Check `pass_if`. Do not skip `intent: user-break` because a
   happy step passed.
4. Record: command + exit, failing names, artifact paths, a short
   excerpt — not the full log.
5. **Evidence is mandatory.** UI: `agent-browser record` of the
   whole plan walk (`.webm`), including user-break steps, plus
   stills of the AC paths. API-only: recorded HTTP of happy and
   user-break. Notes without that evidence are not enough for PASS.

One screenshot is not enough for a screen step.
A unit/CI-only walk is not enough when a FE route exists.

Do not invent credentials; use the repo's documented test auth.

`command -v agent-browser` fails on a UI PR → `BLOCKED`. Do not
reach for Playwright, Cypress, or a host browser MCP.

## Auth (gated screens)

If any plan step is behind login:

1. `eval "$(../before-and-after/scripts/ensure-session.sh)"` and restore
   the shared session with `--session-name "$SESSION"`. On the first
   session-launching command, pass `--headed false`. If the gated app route
   is already loaded in that agent-browser session, skip the helper.
2. Else find the repo helper (`package.json` `qa:otp` / `qa:login`,
   `docs/ai/qa-login.md`, `AGENTS.md`). Run it on `$SESSION`. Login
   is a precondition, not the recording. Keep
   `--session-name "$SESSION"` on session-launching commands.
3. Confirm the gated app route is loaded (not Sign in, not Check your
   email). Snapshot that page to a start text file
   (`agent-browser --session "$SESSION" snapshot` and/or `get url`).
4. Then record on that session, no `--state`:

```bash
agent-browser --session "$SESSION" --session-name "$SESSION" --headed false record start "$VIDEO"
```

   `record start` does not accept `--state`. `--session` on this
   command is load-bearing. Omitting it records a different context
   than the walk. Never pass a URL (the CLI would navigate the
   recorder away).

   **Fresh context.** `record start` opens a **new tab**. Magic-link /
   OTP SPAs often route that tab to `/login` while the previous tab
   stays authed. Stills from the authed tab + a Sign-in `.webm` is
   not a walk. After `record start`:

   1. `agent-browser --session "$SESSION" tab` — the **active** tab
      is the tape. Walk only there.
   2. Snapshot it. Sign in / Check your email / magic link → restore
      auth state with the repo's documented helper or its global state file
      **into this session**, open the gated URL, then wait for the app shell
      (URL not `/login`). Do not invent product-specific storage keys.
   3. Start/stop samples for `walk-video-gate.sh` must be this tab.
      Do not snapshot tab A and record tab B.

5. Walk PLAN.md (happy + user-break) with `--session "$SESSION"`
   on the recording tab. Then
   `agent-browser --session "$SESSION" record stop`. Snapshot stop
   (same `--session`, same tab). Run
   `../scripts/walk-video-gate.sh --start … --stop …`. Login-wall /
   Check-your-email samples **or** a login-only `.webm` → re-record
   or BLOCKED, never PASS — even if stills show the app.
6. **BLOCKED** only after the auth helper is missing or fails, or
   the walk-video gate fails and a re-record is impossible.

Never record before login. Never run `qa:login` in a different `--session`
than `record start`. They must share the same --session. Never PASS a
UI PR whose attached video is the login wall.

## Findings (along the way)

If a step **looks like** a product error (wrong UI, wrong payload,
AC miss, user-break accepted silently, unexpected 4xx/5xx from
app code):

1. Append `## F<n>` to `.ruver-qa/FINDINGS.md`
   ([templates/FINDINGS.md](../templates/FINDINGS.md)).
2. Chat one English line: finding id + step + actual.
3. **Continue** the remaining plan. Later steps are more evidence.

Stop the plan only when QA cannot run: no PR, no env, no auth,
app will not start, no agent-browser on UI → `BLOCKED`. That is
not a finding.

Clearly infra (dev server down, expired login, missing fixture)
with no product smell → `BLOCKED`, no triage.

A broken walk is **not** a verdict. It is evidence for a finding
or for `BLOCKED`.

## After the last step

GitHub UI PR whose body has no `ruver-before-and-after` block:
capture base vs HEAD stills and publish
([before-and-after](../../before-and-after/SKILL.md)). Then verdict.

After recording and still capture, run
`agent-browser --session "$SESSION" close`. Close on every terminal result,
including `PASS`, `FAIL`, and `BLOCKED`, when this execute launched the
session. `--session-name` persists auth for the next run.

| Result | Next |
|---|---|
| No findings, ACs hold, user-break steps walked | **verdict** `PASS` |
| Any `## F<n>` | **request_triage** (one envelope, all findings) |
| Unambiguous FAIL (VERDICTS.md) | **verdict** `FAIL` |
| Cannot run | **verdict** `BLOCKED` |
