# Getting started

In this guide, we install Bulma, check the setup, and deliver one small ticket
to a draft pull request. It takes about 15 minutes plus the time your CI needs.

We use Claude Code in the examples. In Codex, type `$` where the examples show
a leading `/`. For example, `/bulma doctor` becomes `$bulma doctor`.

## Before you start

Check that these commands work in your terminal:

```bash
git --version
python3 --version     # 3.9 or newer
gh --version          # 2.99 or newer
gh auth status        # signed in to GitHub
```

If `gh auth status` says you are not signed in, run `gh auth login`. If your
repo is on GitLab, install and sign in to `glab` instead.

The installer adds [agent-browser](https://agent-browser.dev/), which QA uses
to test your app in a headless browser. You do not need to install it first.

You also need a TypeSafe API key. Create one at
[console.typesafe.ai](https://console.typesafe.ai). TypeSafe runs Jev, the
model `/bulma` asks when it has to pick between options. The
[glossary](glossary.md#jev) explains Jev.

Pick a practice repo with a working test command and CI. A small ticket works
best for a first run: a copy change, a missing validation, or a small bug.

## 1. Install Bulma

```bash
curl -fsSL https://raw.githubusercontent.com/ruverd/bulma/main/install.sh | bash
```

The installer prints each file it creates. It ends with `done. restart the
agent session`. If it ends with an agent-browser error instead, see
[Troubleshooting](troubleshooting.md#setup-fails-with-agent-browser-is-required).
Then check the install:

```bash
bulma status
```

You see the Bulma version, the agent-browser path, and the coding agents it
found. Each agent you use
should appear in the list. If one is missing, see
[Troubleshooting](troubleshooting.md#my-agent-does-not-show-the-bulma-commands).

## 2. Add your API key

Add this line to your shell profile, for example `~/.zshrc` or `~/.bashrc`:

```bash
export TYPESAFE_API_KEY="..."
```

Open a new terminal so the variable loads.

## 3. Check the setup

Start your coding agent in the practice repo, then type:

```text
/bulma doctor
```

Doctor checks Python, your API key, your settings file, and whether Jev
answers. If every check passes, go on. If a check fails, doctor names it.
The fixes are in [Troubleshooting](troubleshooting.md#bulma-doctor-fails).

## 4. Turn on shadow mode

```text
/bulma power shadow
```

In shadow mode, Jev still answers every question, and Bulma writes each answer
to a log. The built-in rules make every decision, and when Bulma must choose
what to do next, it shows you the top three options and asks. Nothing runs on
Jev's word alone. Stay in shadow mode until you trust what you see.

## 5. Tell Bulma about you (optional)

Bulma writes every GitHub comment in English. It can talk to you in chat in
another language:

```text
/memory reply in Brazilian Portuguese
```

To set the reviewers Bulma requests on this repo:

```text
/memory --project reviewers: alice, bob
```

Bulma saves these notes in `~/.bulma/`, never inside your repo.

## 6. Deliver a ticket

Type the ticket ID or paste its link:

```text
/bulma ABC-123
```

Your agent must be able to open the link, for example through a Linear, Jira,
or GitHub MCP server. If it cannot, Bulma stops and tells you. You can also
describe the work in plain words instead of a ticket:

```text
/developer the signup form accepts an empty email
```

Bulma now works through these steps:

1. It asks a few questions about the ticket. Answer them in chat. It asks only
   what the code and docs cannot tell it.
2. It writes a spec and a list of small tickets, then works through them. Each
   ticket gets a fresh worker agent that writes a failing test, then the code.
3. It runs your tests and checks, opens a **draft** pull request, and waits for
   CI. If CI fails, it fixes the cause and pushes again.
4. It runs QA against the pull request and posts a comment with a video, or with
   HTTP evidence for an API change.

When QA passes, Bulma marks the pull request ready for review. It does not
merge. Open the pull request, read the diff and the QA comment, and merge it
yourself when you are satisfied.

## 7. Pick up where you left off

If a run stops for a question, or you close the session, type:

```text
/bulma resume
```

To see every unfinished run on this machine:

```text
/bulma watch
```

`watch` lists what needs you, what stalled, and the command that continues each
run.

## Next steps

- After about 20 decisions, run `/bulma report`. It shows how often Jev agreed
  with the built-in rules. [Configuration](configuration.md#power-levels)
  explains how to give Jev more say, one decision at a time.
- Read [How Bulma works](how-it-works.md) to understand the stages and the
  safety limits.
- Run `/bulma` with no arguments at the start of your day. It picks the most
  useful next item across your open pull requests.
