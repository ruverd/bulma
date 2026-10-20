# Node: wait_ci

**Verb:** wait
**Capability:** scheduler, chat. No GitHub artifact.

After reviewing the pinned diff and completing critic, retain analysis using
[LOOP.md](../LOOP.md). Repeated wakes do not repeat code review when its cache
still matches current inputs. No review or issue comment while CI is pending.
Prefer a host CI-completion wake; use the 5m fallback when unavailable.
