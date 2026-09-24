# Args

`$ARGUMENTS` plus the rest of the user message. Do not ask which kind if the text is enough.

## Parse (first, before admit)

Trim. Then, in order:

| Match | Mode |
|---|---|
| empty, and STATE exists with `status` not in `done` / `escalated` | **resume** |
| `resume` / `continue` (whole token) | **resume** |
| envelope `LSTM_REQUEST` | **urls** from `pr_url` + body |
| GitHub PR / review / discussion / issue-comment URL | **urls** |
| `owner/repo#N` or bare PR number (current repo) | **urls** |
| empty, no STATE | **stop** — ask for a PR or comment URL |

Flags: `--force` continues past red CI (does not skip conflict rebase).

Multiple URLs: same PR stay on one job. Different PRs → admit fans out.

Fragments that count:

```
.../pull/N
.../pull/N#pullrequestreview-<id>
.../pull/N#discussion_r<id>
.../pull/N#issuecomment-<id>
```

`COMMENTED` is not a skip. Medium / High / Critical in a body-only review is feedback.

## Resume

Load `$BULMA_ROOT/.bulma-lstm/STATE.md` then bus STACK + ENVELOPE.

The current message answers `waiting_user`. Do not re-verify comment
ids already in `processed_comment_ids`. Missing 👍 or reply → **reply**.
