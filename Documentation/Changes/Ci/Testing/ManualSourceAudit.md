# Run a full source audit manually

The existing merge-queue workflow accepts `workflow_dispatch` with a required `audit_sha` input.
Supply the full lowercase 40-character commit SHA from the repository.
Every checkout job rejects a malformed requested SHA before checkout or repository execution.
The planner also checks the requested value against its actual checkout before collecting tests.
Every source checkout, candidate security scan, and process witness uses the selected revision.
Test subprocesses receive that same source SHA for their provenance checks.

```sh
gh workflow run MergeQueue.yml --ref WORKFLOW_BRANCH -f audit_sha=FULL_SOURCE_SHA
```

The workflow branch selects the audit harness; `audit_sha` selects the code under verification.
Keep those two revisions distinct in reports.
The audit runs the complete suite, Linux/Windows/macOS process checks, and every existing heavy security job.
It neither downloads accepted test results nor publishes a reusable test-result cache.
The final gate requires every acceptance and security job to pass.
PR and native merge-group gates retain their original conditions, pins, permissions, and timeouts.
Manual audit concurrency uses a separate namespace from native queue candidates.
Its TruffleHog history walk starts at the selected source SHA; existing trigger scopes remain unchanged.

This is remote audit evidence, separate from native queue acceptance and vendor-application acceptance.
No local tests ran.
The [initial remote planner](https://github.com/TryUniCAD/Kit/actions/runs/44908607006/job/136859391345)
verified main `b46259ae0f847339d8a043799e8b8539a2b909d6` and scheduled all 7,052 tests across six shards with zero reused results.
Full execution remains pending until its complete report is available.
