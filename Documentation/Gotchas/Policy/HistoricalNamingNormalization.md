# Historical standards retain archived project names

## Expected behavior

A repository naming cleanup updates readable standards while preserving their historical provenance.

## Observed behavior

The synchronization gate compares readable standards with byte-verified source blobs from a pinned historical commit.
Editing only the readable copies makes that comparison fail.

## Workaround

Apply the same explicit naming and fork-path normalization in the comparison workflow.
Derive the retired name from the pinned source instead of repeating it in current files.
Keep original hashes, byte counts, source inventory, and all remaining content checks intact.

See the [workflow](../../../.github/workflows/SteeringSync.yml) and [change entry](../../Changes/Policy/ProjectNamingCleanup.md).
