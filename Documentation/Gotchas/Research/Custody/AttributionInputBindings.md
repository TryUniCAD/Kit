# Attribution changes alter sealed input identities

## Expectation

Changing attribution and recorded host-path labels might appear independent of research provenance.

## Actual behavior

The capture lineage seals complete Git blobs and modes, including source notices and corpus metadata.
The Fusion outcome baseline also identifies the raw manifest bytes.
The PR #253 attribution migration changed four input blobs and 201 recorded path labels without changing native assets.
Unmodified validators rejected these bytes before evaluating the original research outcomes.

## Workaround

Preserve the original contracts and observations.
Review the complete metadata diff and record exact old/current blob and manifest identities.
Expose both identities and the migration in reports.
Accept only those reviewed pairs while continuing to reject unknown bytes, changed modes, changed rosters, and changed native outcomes.
Never resolve this mismatch by blindly refreshing a baseline or ignoring metadata fields.

See [the repair and remote evidence](../../../Changes/Ci/AttributionQueueRepair.md).
