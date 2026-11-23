# Dynamic matrices need explicit aggregation fixtures

The aggregation process fixture originally found matrix groups only in literal YAML rows.
The dynamic native matrix introduced by PR 276 has its four‑shard fallback inside a JSON expression instead.
The old fixture emitted no native shard checks.

A selected native check then dereferenced an absent check suite.
Other scenarios waited for required native checks until their unchanged twenty‑second process deadline expired.
These failures occurred in both [candidate attempts](https://github.com/TryUniCAD/Kit/actions/runs/45213399753) and [the rebuilt candidate](https://github.com/TryUniCAD/Kit/actions/runs/45218193169).
The workflow cancellation label did not erase the earlier failed shard jobs.

Expand the recognized dynamic fallback into four or five explicit native reports before running the actual aggregator.
Reject unknown matrix syntax and absent fixture targets immediately.
Retain failure, neutral, skipped, cancelled and timed‑out outcomes, including fifth‑shard behavior.
The fifth check may be skipped in the check‑level fixture, while a skipped complete workflow remains a failure.
Do not increase the process deadline to hide missing reports.

PR jobs that skip before matrix expansion retain their literal matrix expressions in GitHub check names.
Preserve those names in PR fixtures and expand groups only for jobs that execute in the selected phase.
Process scenarios verify that these literal skipped checks pass while failed checks still block.
