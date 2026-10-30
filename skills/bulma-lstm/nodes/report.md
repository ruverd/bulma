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
| Sign-off | not requested \| pending \| evidence ready, human approval pending |
| QA evidence | tested SHA + attached QA comment URL, or blocker |
| Ack | 👍 + reply on comment ids … (none missing) |
| Dismissed | fully addressed review ids … \| none |
| Summary | COMMENT URL |
| Pending actions | reviewer requests / API failures … \| none |
| Resolved | N threads |
| Re-request | yes \| no |
```

Stacked (`LSTM_REQUEST` inbound): write `LSTM_RESULT` envelope and pop.

Invoked alone: chat only. Never merge. Never `gh pr ready`.

Before closing, run [learn.md](learn.md) if feedback is still unassessed,
including on escalation. Do not repeat an attempted write that remains pending
without new evidence. Include prevention saved, task draft path or issue URL,
no-action reason and pending feedback failures. Keep product and feedback
outcomes separate.
