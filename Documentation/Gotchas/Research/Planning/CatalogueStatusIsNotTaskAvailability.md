# Catalogue status is not task availability

## Expectation

An unverified catalogue row or a forecast date appears to identify work an agent can
start immediately.

## Actual behavior

The SOLIDWORKS and Fusion planning catalogues retain unverified qualification fields
even when related research or implementation has an open PR. Their inventory is not
a live ownership service. Historical task registers also retain active descriptions
for some merged deliveries. API feature declarations do not establish native grammar.

## Workaround

Use the [planning procedure](../../../Planning/README.md), owning register, live project
claim and current PR head/base before starting. Link a bounded child explicitly to
its catalogue scopes. Keep forecast windows, resource leases, task ownership and
native acceptance as separate records. Never dispatch from a stale local snapshot.

## Evidence

The initial planning snapshot retains the catalogue status policy, current open
deliveries and source hashes in `Documentation/Planning/Generated/Manifest.json`.
