# Retire the serial Linux research CLI job

## Behavior

`Workflow quality` no longer has the `Research CLI compatibility` job (`research-cli`).
That job ran `pytest tests/CliResearch` serially for about eleven minutes on every merge-group candidate on the shared `Kit-linux-2` lane.
The merge queue's complete test suite already collects, plans and runs the same cases in parallel shards.
`Test suite / Report` still requires every collected case to run exactly once.

The shards already provided the job's research-specific setup whenever a shard selects a `tests/CliResearch` case:

| Former job step | Shard equivalent in `MergeQueue.yml` |
| --- | --- |
| Separate `ResearchCheckout` at the candidate revision | `Checkout candidate tools separately for research CLI cases` |
| `KIT_RESEARCH_CHECKOUT` | `Run this shard's tests` environment |
| `CaptureHistory.py fetch --root ResearchCheckout` | `Hydrate candidate CLI fixture inputs` |
| `uv run --with 'numpy<2.5'` | `Synchronize locked dependencies for inference and research CLI shards` |

Before this change, research CLI shards received numpy only when they also held inference cases.
The dependency sync now also runs when a shard selects any research CLI case.
It installs the `dev` group's `numpy<2.5`, pinned in `uv.lock`, instead of resolving an unlocked overlay at run time.
See [the gotcha](../../Gotchas/Ci/Dependencies/ResearchCliShardNumpy.md).

The `Research CLI compatibility` entries are removed from `.github/CiPhases.json`, the allowlist's `RetiringJobs` list and the aggregation process cases.
The Windows research CLI jobs are unchanged.

## Ordering

This change depends on the [report retirement transition](ResearchCliReportRetirement.md).
That change must be in `main` before this PR's merge-group candidate, because `CI Agg` loads the allowlist from the candidate's base.

## Verification

Evidence comes from the merge-group candidate for `main` at `4d98fcc` (PR #294).
In its `Merge queue` run 45722431861, the plan collected 102 `tests/CliResearch` cases and scheduled all 102 across seven shards, reusing none.
Their shard report logs record 101 passes and one skip (`InterruptTests.py::CheckInterrupt`, Windows only), each case exactly once.
The retired job in `Workflow quality` run 45722431871 on the same commit reported `101 passed, 1 skipped in 607.89s` and occupied 11.3 minutes.
Each of those shards also held inference cases, so every research CLI case ran with the locked numpy.
The aggregation and queue-gate process cases pass locally after the job and phase entries are removed.
