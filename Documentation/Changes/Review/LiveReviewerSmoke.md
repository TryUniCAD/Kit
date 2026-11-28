# Temporary live reviewer smoke fixture

This bounded integration fixture exercises the deployed account reviewer, native findings, score, and approval behavior.
It is temporary and must not be merged into production.

The CLI prints the `count` field from a supplied JSON document.
Its input contract accepts `.json` and `.JSON` suffixes.
Run it with:

```sh
uv run --locked --no-sync python re/automation/ReviewSmoke/ReadCount.py re/automation/ReviewSmoke/Count.JSON
```

The current implementation rejects the included uppercase fixture instead of printing `7`.
The first review should identify this contract violation.
The follow-up revision corrects the implementation and tests whether a clean review can produce an actual app approval.
Native workflow, model, reaction, and review evidence remain pending.

Scope `AccountReviewer`, owner `jdharcourt`, branch `feat/reviewer-live-smoke-20261128`.
The permanent owning register remains in the reviewer repair delivery.
No CAD support or release acceptance is claimed.
