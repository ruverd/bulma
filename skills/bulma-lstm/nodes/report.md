# Node: report

**Verb:** summarize

Chat in English. Two to four sentences, then a table.
Do not paste GitHub reply bodies.

```
# LSTM: <repo>#<pr>

| | |
|---|---|
| Head | <sha7> |
| Conflict | n/a \| rebased \| still dirty |
| Reviews | ids … (new / already processed) |
| Dispositions | N fix · N skip · N unclear |
| Patched | yes \| no |
| Ack | 👍 + reply on comment ids … (none missing) |
| Dismissed | CHANGES_REQUESTED ids … \| none \| 403 |
| Resolved | N threads |
| Re-request | yes \| no |
```

Stacked (`LSTM_REQUEST` inbound): write `LSTM_RESULT` envelope and pop.

Invoked alone: chat only. Never merge. Never `gh pr ready`.
