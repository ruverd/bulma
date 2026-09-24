# QA video clips

Source of truth for *how* to record. Execute walks PLAN.md; this
file is the tape recipe. A login-wall / Check-your-email tape is
never PASS.

UI evidence is **per-surface clips**, not one `.webm` of the whole
plan. Load `agent-browser skills get core` before clicking.

## Before any record

Auth as [EXECUTION.md](EXECUTION.md). Never record before login.

`record start` opens a **new tab**. Hydrate that tab: restore auth
into this session, open the gated route, wait for the app shell.
Snapshot it. Sign in / Check your email / magic link → restore
auth with the repo helper or its state file **into this session**,
open the gated URL, wait until the URL is not `/login`.

Then start recording on that tab, no URL, no `--state`. If the
first take still begins on Sign in, `record stop`, discard the
file, `record start` again on the hydrated tab. The tape must
never contain the login wall.

Desktop UI, before the first clip:

```bash
agent-browser --session "$SESSION" set viewport 1440 900 2
```

Same CSS size, 2x retina stills.

## Per surface

One clip per distinct UI **surface** (one inventory row), happy
path. Path: `.bulma-qa/artifacts/S<n>-<slug>.webm`.

Between surfaces, cut a new file:

```bash
agent-browser --session "$SESSION" --session-name "$SESSION" \
  --headed false record restart "$CLIP"
```

`kind: visual` with no operable control: annotated still only.
No clip.

User-break that holds: annotated still of the refuse/recover
state. No clip. User-break that fails: short clip of that repro
only.

A clip that would run past ~45s means the plan step packed too
much. Split the step in PLAN.md, then re-record.

## On tape

1. On tape, type, not fill. `fill` is for setup off-tape.
2. After each click or type: `agent-browser wait 1000`. After the
   `pass_if` state is visible: `wait 2000`. Do not `wait 8000`
   hoping the page loads. Wait for `networkidle`, then the
   `pass_if` text.
3. Annotated still of `pass_if`:

```bash
agent-browser --session "$SESSION" screenshot --annotate "$STILL"
```

   `$STILL` is `.bulma-qa/artifacts/S<n>-pass.png`. Primary control
   clipped, blank, or a loading skeleton that never resolves is a
   finding. A functional pass does not prove the visual.

## Reel

After the last UI clip:

```bash
../scripts/concat-clips.sh --out .bulma-qa/artifacts/reel.webm \
  .bulma-qa/artifacts/S*.webm
```

Exit 2 (no ffmpeg): attach the first clip and say so in the
comment. Publish with `publish-evidence.sh --video` on the reel
or that fallback. Raw clips stay in artifacts. Do not commit them.

## Gate

`walk-video-gate.sh --start` on a snapshot of the **recording tab**
taken after hydration, at first clip start. Login-wall start →
re-record or BLOCKED, never PASS.
