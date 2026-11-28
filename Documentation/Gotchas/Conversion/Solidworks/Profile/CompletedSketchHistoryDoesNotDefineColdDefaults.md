# Completed sketch history does not define cold defaults

## Expected

A saved sketch can supply construction defaults from its live geometry counts and final point positions.

## Observed

The discovery corpus retains deletion records, separate allocation counters and update history.
Two saved sketches have update stamps that differ from one plus their live segment count.
All 24 saved full-circle markers retain one adjacency handle.
The [native registration rule](../../../../../re/solidworks/records/CircleAdjacencyRegistration2026.md) explains this with equivalent-handle checks despite two endpoint-use increments.
These observations describe completed source history.
They neither establish universal defaults nor reject a coherent cold construction policy.

Array positions, entity creation IDs, permanent markers, dimension indices and archive indices also have separate owners.
Different geometry kinds can share the same public ID pair.
Equal coordinates do not prove point identity.
The [field correlation ledger](../../../../../re/solidworks/records/CurveDiscoveryFieldCorrelation2026.md) records the exact cases, identities and native evidence limits.

## Workaround

Derive bookkeeping from the selected construction operations and preserve concrete object identities.
Trace later mutation separately from constructor assignments and conditional registration.
Justify each cold policy from native behavior before measuring generated held-out output between healthy controls.
Keep source observations in research records and out of writer defaults.
