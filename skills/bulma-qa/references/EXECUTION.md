# QA execution

Walk [PLAN.md](PLAN.md) (`.bulma-qa/PLAN.md`). That file is the
surface. Do not skip steps. Do not add ad-hoc screens unless a step
is impossible without them (record the extra step in PLAN.md first).
Clip recipe: [VIDEO.md](VIDEO.md).

UI execute is **agent-browser** only. Do not run the app's Playwright
or Cypress suite (`e2e_cmd` is CI). Load
[before-and-after](../../before-and-after/SKILL.md) for session,
stills, and attach. Load `agent-browser skills get core` before
clicking.

Run agent-browser headless. It launches bundled Chrome for Testing as its
rendering engine; that process is expected. It must include `--headless=new`
and must not open a visible browser window or the user's Google Chrome.app.
Never use `--headed`, `--auto-connect`, `--cdp`, `--profile`,
`--executable-path`, the OS `open` command, a browser MCP server, a browser
extension, another plugin's browser skill, or computer use. That holds even
when another skill in the session says to prefer its browser.

Before the first UI step, in the same shell as every agent-browser command:

```bash
eval "$(../before-and-after/scripts/ensure-session.sh)"
agent-browser doctor --offline --quick
```

`ensure-session.sh` pins agent-browser to the Bulma config (headless, no
profile, no attach), so a user or project `agent-browser.json` cannot
switch QA to a visible browser. If the doctor fails, or agent-browser fails
on a UI step, report `BLOCKED` with the fix (`bulma setup`).
Do not switch tools.

## Per step

1. If `kind` is `endpoint` and no FE caller is resolved: HTTP the
   changed path against the repo's documented origin. Save the
   transcript, then render an HTTP still:

   ```bash
   curl -sS -i -X METHOD "$ORIGIN$path" ... \
     | tee .bulma-qa/artifacts/S<n>.http
   ../scripts/http-proof.sh --out .bulma-qa/artifacts/S<n>-http.png \
     --from .bulma-qa/artifacts/S<n>.http --title "S<n> METHOD /path"
   ```

   `pass_if` is status + body. Notes without that PNG are not enough.
   If a FE caller is resolved, walk that screen instead (step 2). The
   screen is the proof. Do not invent a host.
2. If `kind` is a screen / widget / visual / state: agent-browser.
   Restore the shared session, then follow that step's `how`
   (happy or user-break).
3. Check `pass_if`. Do not skip `intent: user-break` because a
   happy step passed.
4. Record: command + exit, failing names, artifact paths, a short
   excerpt, not the full log.
5. **Evidence is mandatory.** UI: per-surface clips plus the
   `pass_if` still ([VIDEO.md](VIDEO.md)). After `pass_if` on a
   screen step, sample the browser:

   ```bash
   agent-browser --session "$SESSION" errors
   agent-browser --session "$SESSION" console
   agent-browser --session "$SESSION" network requests
   ```

   App 4xx/5xx and JS exceptions → FINDINGS. Analytics noise does
   not. API-only: HTTP stills of happy and user-break (or FE stills
   of the callers). Notes without that PNG are not enough for PASS.

One screenshot is not enough for a screen step.
A unit/CI-only walk is not enough when a FE route exists.
An HTTP still is enough for an endpoint step.

Do not invent credentials; use the repo's documented test auth.

`command -v agent-browser` fails on a UI PR → `BLOCKED`. Do not
reach for Playwright, Cypress, or a host browser MCP.
Missing agent-browser on endpoint-only is not BLOCKED.

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
   on the recording tab. One clip per UI surface, `record restart`
   between them ([VIDEO.md](VIDEO.md)). Then
   `agent-browser --session "$SESSION" record stop`. Snapshot stop
   (same `--session`, same tab). Run
   `../scripts/walk-video-gate.sh --start … --stop …`. Login-wall /
   Check-your-email samples **or** a login-only `.webm` → re-record
   or BLOCKED, never PASS, even if stills show the app. Concatenate
   clips with `../scripts/concat-clips.sh`.
6. **BLOCKED** only after the auth helper is missing or fails, or
   the walk-video gate fails and a re-record is impossible.

Never record before login. Never run `qa:login` in a different `--session`
than `record start`. They must share the same --session. Never PASS a
UI PR whose attached video is the login wall.

## Findings (along the way)

If a step **looks like** a product error (wrong UI, wrong payload,
AC miss, user-break accepted silently, unexpected 4xx/5xx from
app code):

1. Append `## F<n>` to `.bulma-qa/FINDINGS.md`
   ([templates/FINDINGS.md](../templates/FINDINGS.md)).
2. Chat one English line: finding id + step + actual.
3. **Continue** the remaining plan. Later steps are more evidence.

Stop the plan only when QA cannot run: no PR, no env, no auth,
app will not start, no agent-browser on UI → `BLOCKED`. That is
not a finding. Missing agent-browser on endpoint-only is not
BLOCKED. A backend PR with no screen still executes.

Clearly infra (dev server down, expired login, missing fixture)
with no product smell → `BLOCKED`, no triage.

A broken walk is **not** a verdict. It is evidence for a finding
or for `BLOCKED`.

## Exploratory (after the scripted walk)

Exploratory is UI surfaces only. If every planned step is
`kind: endpoint`, skip the browser dogfood. The HTTP stills from
the scripted walk are the proof.

After the last PLAN.md UI step, before close. Same `$SESSION`.

Load `agent-browser skills get dogfood`. Charter: explore the
surfaces listed in the PLAN.md inventory with this session to
discover unexpected regressions around the change.

Do not follow the scripted `how`. One off-script pass per planned
UI surface, then stop. Do not open the rest of the app.

Interactive suspicion: clip the repro ([VIDEO.md](VIDEO.md)), append
FINDINGS, continue. Static: annotated still only.

No extra finding: one line in the comment, `exploratory: no extra
finding on <surfaces>`.

## After the last step

GitHub UI PR whose body has no `bulma-before-and-after` block:
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
