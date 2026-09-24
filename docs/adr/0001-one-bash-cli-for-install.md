# One bash CLI for install and update

Host plugin marketplaces (Grok, Claude, Cursor) auto-update, but they
do not flatten `skills/{graphs,engines,lib}/<name>` into slash names
and they do not cover every harness with one command. Superpowers
accepts one install recipe per host. Bulma needs `/bulma-developer`
everywhere and a `bulma update` that does not require Node. Decision:
`install.sh` is the installer and the `bulma` command. Clone + symlink
flatten. Plugin install stays available and is not invoked by the CLI.

Status: accepted
