# Saved SOLIDWORKS trimmed curve research

The saved P03 derivative contains a current-schema Parasolid
`TRIMMED_CURVE` record that the SDK's typed active reader cannot traverse.
The research command takes the exact saved derivative, a pinned kernel
descriptor receipt and an unused output location. It decodes the observed
trim record with the existing typed cursor and records the next refusal.
[Reproduction and field layout](../../../../re/solidworks/records/SavedTrimmedCarrierBoundary.md)

The exact run decoded 84 records and reached unmapped kind 141 at body
offset 3692. The trim's two endpoints agreed exactly with both its line
basis and one independently measured native edge. Five previously measured
vendor controls fully traversed the current schema and used direct line
carriers. They included an independent 12 mm edit. The known prefix does
not establish which edge consumes the trim in the saved derivative.

The general reader independently requires three vertex uses that its
scanner does not supply. The typed walk did not reach a complete graph,
so this result does not resolve those vertices or restore public geometry.
Both documented research commands reproduced their results in fresh
processes. Another process refused a different loader receipt before
publishing output. Verification used the retained files without a new
native session or public SDK decode.
[Endpoint and carrier ownership gotcha](../../../Gotchas/Research/Readers/SolidWorksVendor/MatchingEndpointsLeaveCarrierOwnershipOpen.md)
