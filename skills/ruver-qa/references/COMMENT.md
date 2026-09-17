# QA PR comment (mandatory)

After a **final** verdict (`PASS` / `FAIL` / `BLOCKED`), post **one**
GitHub comment on the PR. This is not optional.

Never comment `PENDING_TRIAGE`.

## Collect evidence first

QA execute must have recorded:

- UI: agent-browser **per-surface clips** (`record start` / `record restart` /
  `record stop`), concatenated to a reel when possible
  ([VIDEO.md](VIDEO.md))
- UI: annotated `pass_if` stills of the AC paths
- API/backend: HTTP still PNGs of the changed endpoints (happy and
  user-break), or FE stills/clips of the screens that call them
- command + exit + failing names if any
- console / errors / network sample per UI surface

Paths live under `$CAPTURE_DIR` or `.ruver-qa/artifacts`.

Stills before/after belong on the **PR body**
([before-and-after](../../before-and-after/SKILL.md)), not in this
comment.

## Post (evidence on the comment)

GitHub comments play `user-attachments` video. They do not play
gist `.webm`. **Never** `gh gist create` on media.

Write `$BODY`. Replace `VIDEO_PATH` with the recorded `.webm` so
`gh --attach` can rewrite it. Then:

```bash
../scripts/publish-evidence.sh \
  --repo "$REPO" --pr "$PR" --sha "$SHA" \
  --body-file "$BODY" \
  --video "$VIDEO" --artifacts .ruver-qa/artifacts
```

The script runs `gh pr comment --attach`. Use the printed
`COMMENT_URL`. `gh` ≥ 2.99.

If the script exits 2, still get a comment up with the printed
`LOCAL_VIDEO` path — do **not** skip the comment.

## Body

`$BODY` template (English — it is GitHub):

```markdown
## QA: PASS

| | |
|---|---|
| PR | <url> |
| SHA | `<sha>` |
| Surface | <routes / endpoints from PLAN.md> |
| Plan | <step count> steps |
| Findings | <n or none> |
| Triage | <class or n/a> |
| Tracker | <NEW_BUG ids or n/a> |

<summary of the plan + what passed>

### AC coverage

| Criterion | Step | Runtime | Evidence | Proof |
|---|---|---|---|---|
| <AC text or n/a> | S<n> | holds / fails / unproven | clip S<n> / still / HTTP still | app |

Proof `app` means the running app or the running API was driven and
`pass_if` was observed (UI walk, or HTTP still of status + body).
A Must criterion with proof below app is not PASS. Unit/CI is not
`app`.

### Evidence
[Walk video](VIDEO_PATH)

HTTP stills attached when `kind: endpoint` (omit the video line on
endpoint-only).

exploratory: <no extra finding on <surfaces> | N findings, see F*>

<!-- ruver-qa: v=1 verdict=PASS sha=<sha> -->
```

Headers: `## QA: PASS` · `## QA: FAIL` · `## QA: BLOCKED`.

`FAIL` includes expected vs actual + triage class.
`BLOCKED` includes what was missing (env/auth/app/agent-browser).

One comment per SHA. If a comment with the same
`ruver-qa: v=1 … sha=<sha>` already exists, do not post another.

## Hard rules

- No verdict without this comment.
- No comment without attempting `--attach` when a `.webm` or HTTP
  still PNG exists.
- **PASS requires evidence.** A `.webm` on disk is not enough. UI
  PASS needs per-surface clips of the happy walk plus `pass_if`
  stills. That is the walk evidence. User-break that holds: annotated
  still of the refuse/recover state. User-break that fails: a repro
  clip. A login wall / `Check your email` tape is not walk evidence
  and is never PASS (re-record or BLOCKED). Execute must run
  `walk-video-gate.sh` on start/stop snapshot text taken with the
  same `--session` as `record start` (sampling the walk session
  while the recorder sat on default/`qa:login` is the incident).
  API-only: attach an HTTP still (PNG of status + body) of the
  changed endpoints (happy and user-break), or FE stills of the
  callers. `publish-evidence.sh --screenshot` or artifacts `*.png`.
  A `.webm` is not required when every planned step is `kind:
  endpoint`. Notes or `git show` are not enough. If capture failed
  on a UI run, including wrong-content capture, say so in the
  comment and do **not** treat the run as a complete PASS. Every
  Must AC in the coverage table must be `app`.
- Do not commit videos to the PR branch.
- Do not paste credentials or raw `.env`.
