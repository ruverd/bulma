# Changelog

Notable changes per release. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html), pre-1.0.

## [Unreleased]

### Added

- `/qa` plans a blast-radius table (callers → user flows; zero callers
  is UNKNOWN, not skip) before any browser step, records per-surface
  agent-browser clips instead of one whole-plan tape, and posts an AC
  coverage table. After the scripted walk, a scoped dogfood pass
  explores those surfaces off-script. `scripts/concat-clips.sh`
  concatenates clips into the comment reel.
- `/ruver-code-review` writes the ticket/PR acceptance checklist before
  reading product files, drops findings whose `path:line` is not in the
  patch (`scripts/bind-findings.py`), and spawns one fresh critic on
  high-risk diffs only (`scripts/classify-risk.py`). `/ruver-reviewer`
  uses that path; it does not spawn a second critic.
- The critic walks contracts, integration/state, and security/data-loss
  on that one spawn and does not vote unique findings off. Tests run
  before correctness. The GitHub body includes an Acceptance table.
  Accessibility and lockfile review run only when the diff touches those
  files. Risk also trips on public contract, concurrency, and wide diffs.

### Fixed

- Tracker checkout is always `feature/<id-lowercase>` (`DEV-4525` →
  `feature/dev-4525`). Host `{login}/<id>` worktrees and tracker
  `gitBranchName` no longer win.
- SkillSpector static scan of `ruver-feature-delivery` no longer flags
  E4/TM1/AS3/EA1 keyword hits. The quality node, CI ban, adapters, and
  STATE template were rephrased; graph behavior is unchanged.

## [0.9.1] - 2026-09-11

### Fixed

- Codex standalone installs now copy skills instead of symlinking them, keeping
  public ids such as `$ruver-developer` instead of plugin-namespaced ids.
- Command templates no longer use features rejected by Codex command-to-skill
  migration.
- Setup output and docs no longer claim Codex accepts direct `/ruver-*`
  commands. Codex users invoke the same standalone skills with `$ruver-*` or
  `/skills`.
- Added `$ruver-fd` as a standalone alias for `ruver-feature-delivery`.

## [0.9.0] - 2026-09-03

### Added

- `ruver report` prints host token totals (prompt, uncached, cache%)
  by workspace class when a Grok transcript exists. Graphs still do
  not write token counts into the run ledger.

### Changed

- `spawn_worker` passes the node file, the ticket/finding/PR, and a
  path whitelist. It does not pass GRAPH.md, `why`, or the parent
  tool catalog.
- `code_graph_explore` is required for discovery when `.codegraph/`
  or `.tokensave/` exists. Grep/Read of whole files is the fallback.
- `why` is no longer on the default grill / diagnose / review path.
  Load it only when a last-resort design fork remains after `how`.

## [0.8.1] - 2026-09-03

### Changed

- `/qa` plan is no longer a happy-path walk of the diff. Every
  changed process (`screen`, `state`, `endpoint`, widget host) needs
  `intent: user-break` steps derived from that flow (wrong use,
  interrupted transition, around the gate). A happy-only plan cannot
  execute. A happy-only walk is not `PASS`.

## [0.8.0] - 2026-09-03

### Added

- `before-and-after` lib: GitHub PR body stills (desktop, mobile only
  when layout/CSS changes). Shipper attaches merge-base vs HEAD with
  `gh pr edit --attach`. `/qa` fills the block when it is missing.
- `ruver setup` installs `agent-browser` and Chrome, and warns when
  `gh` is older than 2.99 (`--attach`).
- Shared login state under `~/.ruver/agent-browser/ruver-<owner>-<repo>/`.

### Changed

- **Breaking:** `/qa` UI execute is agent-browser only. The app's
  Playwright/Cypress suite stays in CI (`e2e_cmd`). Missing
  `agent-browser` on a UI PR is `BLOCKED`.
- QA video and PR stills use `gh --attach`. Gist upload is gone.
- `qa_tool` is `agent-browser | http | none`.
- The `evidence` node captures local PNGs with agent-browser. Shipper
  publishes them; it does not gist them.

### Removed

- Playwright/Cypress/host-MCP as the agent's QA hands.

## [0.7.0] - 2026-09-03

### Added

- Branch and worktree rules in `ruver-bus` `JOBS.md`. Every task, foreground
  included, gets its own worktree and branch from `origin/main` after
  `git fetch`. Never commit to main. `--force-with-lease` only on the task
  branch, never on main. Shipper rebases onto `origin/<base>` and re-runs
  the hard gate before push. `ruver status` lists worktrees.
- `templates/PR_BODY.md` and an `evidence` node. Before and After belong in
  the PR description. Screenshots publish as a secret gist.
- Developer `bot_review` between `mergeable` and `request_qa`. Detected
  review bots wait on the head SHA. Unresolved bot threads go to LSTM. A
  score gate holds QA until `N/5` meets `review_bot_min_score`.

### Fixed

- Stale `skills/graphs`, `skills/engines`, and `skills/lib` paths in inline
  code. `check_links.py` now validates backtick skill paths.

## [0.6.0] - 2026-08-28

### Added

- The QA slot is a lease. `qa_active` was cleared only by `ruver-qa`'s
  `verdict` node, so any other exit — `handed_off` on a context limit,
  `escalated`, a killed session — left the claim set for good. Every later
  `QA_REQUEST` then parked in `qa_waiting` and never ran, while the graph kept
  answering with a queue position. `qa_claimed_at` plus `qa_lease_minutes`
  makes an old claim free, and every terminal exit now releases.
- `qa_fix_loops` (default 2) bounds the `apply_qa` → `fix` → QA ring. fd bounds
  its own rings, but mode `fix` never re-enters the fd graph, so the most
  expensive loop in the system — a full QA plus a triage plus a fix — was the
  only unbounded one. `apply_qa` also escalates immediately when a finding id
  repeats across laps, which is the failure that actually happens.
- `qa_verdict_log` in the developer STATE: one row per QA lap. `qa_verdict` is a
  single overwritten field, so lap 6 used to leave a STATE identical to lap 1.
- STACK.md depth is capped at 3, and a push of a graph already on the stack is
  refused. `developer → qa → triage` is the deepest real chain; a fourth frame
  is a cycle.
- `tests/repo.sh` fails when a graph declares the same enum with different
  values in different files. It found four, each losing information: `scope`
  had `mono` in the schema and not in `ROUTING.md` or `HANDOFF.md`, `mcp_gate`
  was `passed | failed` in `HANDOFF.md` so a handoff could not express
  `passed_partial`, `ci.status` was missing `skipped_no_pr`, and the blocker
  rollup was called `status`, colliding with the graph's own.
- `$RUVER_ROOT/.ruver-bus/RUN_LOG.tsv`, a run ledger the graphs append to on
  every transition, and `ruver report` to read it: wall time and lap count per
  `graph/node`, plus the age of the QA claim. Observation only — nothing gates
  on it. See `skills/ruver-bus/LEDGER.md`.
- `version` in `.codex-plugin/marketplace.json` and
  `.cursor-plugin/marketplace.json`.

- `tests/repo.sh` gates the discovery block: the sum of every skill's name and
  description, which every host pastes into the system prompt on every turn.
  Codex caps that block at 8,000 characters and silently shortens or drops
  skills past it. The repo was at 8,934; it is now 7,587.
- `tests/repo.sh` holds reference files one directory below `SKILL.md`, so a
  partial read of a skill shows an agent everything it can load.
- `tests/repo.sh` reads the version out of `.codex-plugin/marketplace.json` and
  `.cursor-plugin/marketplace.json`, and checks the marketplace and plugin names
  across all four marketplaces. Those two files carried no version at all.
- `version` in `.codex-plugin/marketplace.json` and
  `.cursor-plugin/marketplace.json`.

### Changed

- Twenty-two skill descriptions are shorter. Process detail moved into the
  bodies; the trigger phrases stayed, because that is what routing reads.
- `skills/why/references/sources/*.md` are now `references/source-*.md`.
- README brought back in line with the product: the layer table pointed at the
  pre-flatten `skills/*/*/GRAPH.md`, `/goal` was missing from the command table
  and the alias list even though `commands/goal.md` ships, `ruver-host` appeared
  nowhere in the reference section despite being one of the 34 skills, the
  runtime-state block showed three of the nine directories and none of the
  ledger, and "add a skill" named one of the three manifests the gate checks.
  New sections cover what bounds a run and how to measure one.
- 107 places across 47 skill files, 6 agent contracts and one command named
  Linear as *the* tracker. The field rename in 0.5.0 covered `linear_*` but not
  prose, so `DECISION_POLICY.md` alone pointed at it eleven times and an agent
  reading it would reach for Linear with `tracker: github_issues` in STATE.
  `tests/repo.sh` now fails on the bare name outside the files whose job is
  vendor mapping.

### Fixed

- Two Portuguese strings in English skill bodies: `route_confidence: alta |
  media | baixa` in `ROUTING.md` and `"fecha o spec?"` in `nodes/spec.md`.
- `docs/GRAPH_ENGINEER.md` step 2 still taught the pre-flatten link layout
  (`../../engines/<name>/...`). A contributor following it wrote links that
  leave the skills root.
- The README layout tree still showed `skills/graphs`, `skills/engines` and
  `skills/lib`, contradicting the paragraph under it.
- Prose across the docs and four skills still called the host contract
  `HOST.md`, a file that no longer exists. `tests/repo.sh` now fails on the name.
- `ruver-developer` described itself as delivering a *Linear* ticket, which the
  tracker genericization missed because the description is not a state field.
- `how` and `diagnose` carried `\"` inside a folded YAML scalar, so literal
  backslashes reached the skill picker.

## [0.5.0] - 2026-08-28

### Added

- `ruver --version` / `-V`.
- `--only <hosts>` and `--all` to choose which agent homes `setup` writes to.
- `--no-path` to leave `~/.zshrc` and `~/.bashrc` alone.
- A symlink capability check. `setup` refuses on a filesystem where `ln -s`
  silently copies, because `ruver update` would then never propagate.
- `tests/repo.sh`: link, frontmatter, manifest and structure gates.
- `shellcheck` in CI.
- `category: graph | engine | lib` in every `SKILL.md`.
- `commands/goal.md`, so `/goal` exists next to `/developer`, `/qa`,
  `/reviewer`, `/lstm` and `/memory`.
- `CONTRIBUTING.md`, `SECURITY.md`, `CODEOWNERS`, issue and PR templates.
- `skills/ruver-host`: the host contract, previously `HOST.md` at the repo root.
- `ruver-goal` gained `GRAPH.md`, `STATE.schema.md` and four nodes.
- `ruver-code-review` gained the `STATE.schema.md` it never had.

### Changed

- `setup` links only into agent homes that already exist. It used to create
  `~/.codex/skills` and `~/.cursor/skills` on machines without those tools.
- `setup` names each shell rc file before appending to it.
- The Grok plugin index is derived from frontmatter instead of hand-maintained.
- All four manifests are checked to agree on the version.
- README no longer promises Windows Git Bash support. WSL is the supported path.
- **Breaking:** one flat directory per skill. `skills/{graphs,engines,lib}/<name>`
  is now `skills/<name>`, and `category` in the frontmatter carries what the
  directory used to. No link may leave the skills root, which is what makes
  `../other-skill/FILE.md` resolve the same in git and after install.
- `ruver-code-review/SKILL.md` split from 668 lines into eight nodes and three
  references.
- `ruver-bus` is `category: lib`. It has no nodes and walks no edges, so it is
  documented as the shared protocol rather than as a graph.
- State fields are vendor-neutral: `linear_id` and friends are `tracker_id` and
  friends, selected by `tracker:`. Linear works exactly as before through
  `LINEAR.md`, now explicitly the Linear adapter.
- Optional MCP tools are named as capabilities and mapped in `ruver-host`.

### Fixed

- `.claude-plugin/plugin.json` omitted `ruver-memory`, so `/memory` did not
  exist for Claude Code plugin users.
- Version drift: two manifests said 0.4.2 while two said 0.4.3.
- `architect` referenced an `arena` skill that is not bundled here.
- Four `shellcheck` findings in `install.sh` and `tests/`.
- Links that reached outside their own skill resolved only on hosts that walk
  symlinks with the kernel. On a host that normalises the path string first,
  every graph silently lost its host contract.
- `setup` left dead symlinks behind when a skill or command was renamed or
  deleted, and the host kept offering them in the picker.

### Removed

- The seven `commands/ruver_*.md` underscore aliases. They doubled the command
  picker on every host and were never documented. The role names `ruver_*`
  remain in `agents/`.
- `docs/superpowers/`: internal working notes that shipped to every user.

## [0.4.3] and earlier

Not tracked in this file.

[0.9.0]: https://github.com/ruverd/skills/compare/v0.8.1...v0.9.0
[0.8.1]: https://github.com/ruverd/skills/compare/v0.8.0...v0.8.1
[0.8.0]: https://github.com/ruverd/skills/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/ruverd/skills/compare/v0.6.0...v0.7.0
[0.5.0]: https://github.com/ruverd/skills/releases/tag/v0.5.0
