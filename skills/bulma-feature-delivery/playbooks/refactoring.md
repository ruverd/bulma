# Refactoring

Pin the behavior contract before moving structure. Capture the existing output,
including quirks the task requires preserving. A characterization probe must
exercise the actual code and its relevant boundary inputs. Keep the probe and
fixtures fixed. If a probe must change, recapture both revisions and say why.

Use [runtime evidence](../../bulma-bus/PERFORMANCE.md) to capture successful,
stable baseline and candidate runs with the exact same argv and complete
environment fingerprint. The probe must print its observable results; empty
output proves nothing. Evidence stays outside the checkout. Record the baseline
receipt as the `baseline` proof before implementation.

After the structural change, compare the two receipts:

```bash
python3 scripts/equivalence.py --repo <worktree> --environment <fingerprint> \
  --baseline <before-result.json> --candidate <after-result.json> \
  --out <BULMA_ROOT>/equivalence.json
```

The helper compares exact combined command output, verifies receipt integrity,
and binds the candidate to the current tree and environment. It refuses failed,
mutating, stale or mismatched runs. Put its report path in the `equivalence` row.
The playbook check revalidates that report. Never compare the baseline receipt
to itself or treat equal output as proof for inputs the probe did not exercise.

Keep review and regression checks. Split any newly desired behavior or bug fix
into another ticket. No compatibility layer solely to keep a transitional shape.
Report the changed structure, preserved contract and scope of the comparison.
