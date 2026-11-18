# Direct QA reproduction

Bulma QA runs a bounded product case from a host-approved target. For a PR it
requires the exact PR URL and either a preview pinned to the current head or a
local provisioning profile for its repository. Answer plans from the current
request, thread evidence and pinned PR description, when available.

The host configures the executor's JSON registry outside git. Each entry in
`targets` has an ID, `environment` label, `kind` (`local`, `dev`, or
`preview`), a base `url` with its approved origin, and a `checkout` root.
For a preview add `pr` and `head`.
An optional `auth_state` points at an already provisioned test session state
used only by the browser. Mark `isolated_data` after verifying the target's
app, API, identity provider, and data boundaries using [LOCAL_SETUP.md](LOCAL_SETUP.md).
Set `synthetic_evidence` only after verifying that
the cropped area contains shareable synthetic data. Inspection scopes, URLs,
selectors and auth paths are host-owned.

For new reports, define `surfaces` by ID. Each surface has a `label`, a
fixed `path` on the approved origin, and an `evidence_selector`. Its optional
`controls` maps IDs to a `label` and a trusted click `selector`. Approve
only controls whose effects are safe for the test identity and whose steps
stay on the same path. The published catalog contains labels and IDs.
Answer derives the ordered control IDs (at most eight) and the two distinct
visible assertions from the conversation. It requests one missing detail
when it cannot ground a complete plan. The host passes the plan through
standard input with `--plan-stdin`. The executor resolves and rechecks it
against the private registry. It stores a plan hash in the receipt to reject
a different plan for the same request. No arbitrary navigation, forms,
shell commands, selectors, scripts, or credentials can come from the plan.

Existing targets with no `surfaces` still use their configured `steps`,
`clicks`, `evidence_selector`, `bug_text` and `success_text`.

## Provision a local environment from a PR

Register one target per approved repository group outside git. Use `kind:
local`, `checkout` for the Bulma QA lease, `isolated_data: true`,
`synthetic_evidence: true`, and the approved `surfaces`. Omit `url`, `pr`,
`head`, and host `auth_state`. Set `provision` to an object with:

- `browser` as the service name that serves the application.
- `browser_image` as the full local Docker image ID for the QA browser.
  Build [browser.Dockerfile](../scripts/browser.Dockerfile) from trusted Bulma
  code. The image needs headless agent-browser and Chromium, curl, and Tesseract.
- `payment_mode` as `stub` or `disabled`, and `synthetic_identity: true`.
- `services` keyed by DNS-safe names such as `web`, `api`, and `db`.
  Each service specifies a full local Docker `image` ID, a fixed `start`
  argv array, a `port` between 1024 and 65535, and an HTTP `ready_path`.
  An app service also has `repo` (`owner/name`), `checkout` (an approved
  root with a matching GitHub `origin`), and `base_ref` for the approved
  compatible base. Use a full commit or an exact `refs/heads/...` ref.
- Optional `dependencies` mapping primary commit IDs to objects keyed by
  companion repository. Values are exact PR URLs, commit IDs, or full
  branch refs. Use this for an explicit compatibility record.
- Optional `reuse` mapping service names to approved managed container
  names. QA verifies the complete stack, pins, shared isolated network,
  and readiness before borrowing it. If verification fails, QA provisions
  a fresh stack and preserves existing resources.

Use versioned startup and fixture setup commands inside approved images.
Bake offline runtime dependencies into those images and use `/work` for
disposable state. App images receive only a read-only export of the pinned
checkout at `/source`. Configure local data, providers, and payment stubs in
the approved images. Seed only synthetic test data and the required app
roles. Readiness should include required data and identity setup. To supply
a synthetic browser state, set `browser_test_state: true` and bake it at
`/opt/bulma/qa-state.json` in the trusted browser image. Use a disposable
test identity. Keep dev dumps, shared volumes, production config, and
real credentials outside all QA images and exports.

Bulma QA resolves the live PR SHA and follows declared dependencies in both
directions. Use `Depends on:`, `Requires:`, `QA dependencies:`, or labels
such as `API V2 PR:` and `UI PR:` with exact GitHub PR URLs. A declaration
may use `owner/repo refs/heads/...` or `owner/repo <full commit>`. The
compatible base in the profile applies only when no dependency is declared.
Conflicts, unresolved refs, or unavailable required bases block execution.
QA fetches into private Git storage, checks the fetched SHA, and stages a
detached worktree and filtered source export. A changed pin during the run
invalidates evidence.

Provisioning uses a local Docker Engine with isolated bridge gateway support.
The application and disposable browser share one internal network with
no published ports, host sockets, or shared volumes. Services run as a
non-root user with a read-only root, dropped capabilities, and scratch
tmpfs. QA waits for all services and removes the browser and all resources
it created, including on startup failure. Borrowed instances are preserved.
Use a QA fixture profile without external login, data, or billing dependencies.

## Call without Slack

Use the same bounded case and QA lease from any host or directly from a
terminal. Point at the host-approved registry and pass the case via stdin:

```bash
python3 scripts/thread-repro.py --registry "$QA_REGISTRY" \
  --target "$QA_TARGET" --pr "$PR_URL" --event "$REQUEST_ID" \
  --out "$PRIVATE_EVIDENCE_DIR" --plan-stdin < "$PRIVATE_PLAN"
```

The case JSON contains `surface`, `actions`, `bug_text`, and
`success_text`. Pass `{"inspect_pr":true}` instead to get the verified head
and redacted PR description without starting QA. Bind the execution plan to
that head with `head`. The result includes tested revisions, whether the
stack was reused, and the SHA-256 of a cleared PNG when available.
Exit 75 means the caller should retry after the active QA claim releases.

For an optional local integration check, set `BULMA_QA_BROWSER_IMAGE` to the
local browser image ID and `BULMA_QA_SERVICE_IMAGE` to the local ID of a
Python 3 Alpine image. Run `python3 -B tests/lib/test_qa_environment.py` from
the Bulma repository. The fixture creates its own repositories and services.

## Evidence and delivery

The executor claims the checkout's existing Bulma QA lease after older PR QA
work. While busy, the host keeps the request pending and retries. It records the
case plan, opens the approved origin in agent-browser, checks the asserted
outcome and captures a cropped PNG. It verifies the assertion in local OCR and
rejects recognizable sensitive content before clearing the artifact. It closes
the test browser and releases the lease on terminal outcomes.

Report `reproduced`, `not_reproduced` under those exact conditions, or
`blocked` with the concrete prerequisite. Deliver through the original thread.
Use a configured synthetic QA tenant or local app only. Authentication screens,
raw data, secrets, and uncleared images stay private. CI and automatic GitHub
publication are outside this entry point.
