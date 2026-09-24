# Troubleshooting

Find the symptom, then follow the steps under it. If none match, open an
[issue](https://github.com/ruverd/bulma/issues/new/choose) with the output of
`bulma status` and `/bulma doctor`.

## My agent does not show the Bulma commands

1. Restart the coding agent. Agents load skills when a session starts.
2. Run `bulma status` in your terminal. Check that your agent is in the list.
3. If it is missing, run `bulma setup --only <agent>`, where `<agent>` is
   `claude`, `grok`, `cursor`, or `codex`. `--all` installs for every agent,
   even ones Bulma did not detect.
4. In Codex, type `$bulma`, not `/bulma`. Codex rejects custom `/` commands.

## `bulma: command not found`

The installer puts `bulma` in `~/.local/bin` and adds that folder to `PATH` in
`~/.zshrc` and `~/.bashrc`. Open a new terminal. If you installed with
`--no-path`, add `~/.local/bin` to your `PATH` yourself.

## `/bulma doctor` fails

| Message | Fix |
|---|---|
| `missing: TYPESAFE_API_KEY` | Create a key at [console.typesafe.ai](https://console.typesafe.ai), add `export TYPESAFE_API_KEY="..."` to your shell profile, and restart your agent from a new terminal |
| `python3` too old or missing | Install Python 3.9 or newer |
| `Jev unreachable.` | Check your network and that the key is still valid in the TypeSafe console |
| A settings or `decisions.json` error | Run `bulma update`. If it still fails, move `~/.bulma/bulma.json` aside and run `/bulma doctor` again |

Without a key, you can still run each stage directly: `/developer`, `/qa`,
`/reviewer`, `/lstm`, and `/bulma-triage`.

## Setup fails with `agent-browser is required`

QA and the pull request screenshots use agent-browser and no other browser, so
setup does not finish without it. Setup tries Homebrew, npm, and Cargo in that
order. If none is installed, or the Chrome for Testing download fails, install
agent-browser yourself and run setup again:

```bash
npm install -g agent-browser
agent-browser install     # downloads Chrome for Testing
agent-browser doctor --offline --quick
bulma setup
```

On Linux, run `agent-browser install --with-deps` to add the system libraries
Chrome needs. Other install methods are on the
[agent-browser install page](https://agent-browser.dev/installation).

## QA opened my Google Chrome

QA must run headless in agent-browser's own Chrome for Testing. If your own
Chrome window opened, one of these happened:

- The agent used a different browser tool, such as a browser MCP server or
  another plugin's browser skill. Run `bulma update` to get the rule that forbids
  this, and tell the agent to use agent-browser only.
- An `agent-browser.json` in your repo or `~/.agent-browser/config.json` turned
  on `headed`. Bulma's QA session pins its own headless config and ignores both
  files. Run `bulma update` if your install is older.

## `bulma status` warns that the plugin and setup are both installed

You installed Bulma twice on one agent: once as a plugin and once with
`bulma setup`. Keep one. To keep setup, remove the plugin through your agent,
for example `claude plugin uninstall bulma@bulma`. To keep the plugin, run
`bulma uninstall`, which removes the setup links and the `bulma` command.

## Setup refuses to install on Windows

Bulma needs real symbolic links so that `bulma update` reaches every agent.
Git Bash on Windows copies files instead, unless Developer Mode is on and
`MSYS=winsymlinks:nativestrict` is set. Setup checks this and stops rather than
install a copy that never updates. Use WSL instead.

## Bulma stops because it cannot read the ticket

Bulma never guesses a ticket's contents. Your coding agent must be able to open
the link, usually through an MCP server for the tracker: Linear, Jira, Notion,
or another. Connect the server, then run `/bulma resume`. To skip the tracker,
describe the work in plain words: `/developer <what to build>`.

## QA does not attach the video or screenshots

Attaching files to a pull request needs `gh` 2.99 or newer. Run `gh --version`
and upgrade if it is older. `bulma setup` warns about this.

For browser QA, agent-browser and its Chrome for Testing must work. Check with
`agent-browser doctor --offline --quick`. If you set `BULMA_SKIP_DEPS=1`,
install them yourself.

## QA waits and never starts

Only one QA run happens at a time on a machine. Run `/bulma watch` to see which
pull request holds the QA slot. If that run crashed, the next QA run takes the
slot after 90 minutes and says so.

## A run says it is still working on a pull request that merged

Run `/bulma watch`. It checks each run against GitHub, drops the ones whose
pull request merged or closed, and prints the command that continues each of
the rest.

## A run stopped and asked me something

Bulma stops when a loop reaches its limit, for example after two QA fix rounds.
Read the question in chat, answer it, and run `/bulma resume`.
[How Bulma works](how-it-works.md#limits-that-stop-a-run-from-looping) lists the
limits.
