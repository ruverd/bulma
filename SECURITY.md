# Security

## Reporting

Open a [security advisory](https://github.com/ruverd/bulma/security/advisories/new)
or email ruverd@gmail.com. Please do not open a public issue for anything
exploitable. Expect a first reply within a week.

## What this project actually does

Two things worth understanding before you install.

**The installer symlinks into your home directory.** `install.sh` creates
symlinks under `~/.agents`, and under the agent homes that already exist
(`~/.claude`, `~/.grok`, `~/.cursor`, `~/.codex`). It puts `bulma` in
`~/.local/bin` and, unless you pass `--no-path`, appends a `PATH` line to
`~/.zshrc` and `~/.bashrc`. It names each file as it goes. Anything it would
overwrite is moved to `~/.skills-backups/<timestamp>/` first. `--dry-run`
prints every action and writes nothing.

The documented install is `curl | bash`, which runs code from `main` without
pinning. If that is not acceptable in your environment, clone the repo, read
`install.sh`, and run `./install.sh setup` from the checkout.

**The skills tell an agent to run commands.** These graphs instruct a coding
agent to read your repository, run your test suite, create branches, push, and
open draft pull requests via `gh` or `glab` using credentials already on your
machine. They are written never to merge and to stay on draft pull requests, but
they are instructions to a model, not enforced permissions. Your agent's own
permission settings are the real boundary. Review them before pointing any of
this at a repository you care about.

Runtime state lives outside your repositories in `~/.bulma/`, and nothing in it
is committed.

## Scope

In scope: the installer, the CI workflows, and any skill that instructs an agent
to exfiltrate data, escalate its own permissions, disable a safety gate, or run
something the documentation does not describe.

Out of scope: a model choosing to do something unhelpful that the skill did not
ask for, and vulnerabilities in the agent harnesses themselves.
