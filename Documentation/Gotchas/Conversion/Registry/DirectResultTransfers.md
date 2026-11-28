# Direct writer results can precede transfer normalization

A raw direct writer result can have an empty `transfers` tuple even when the same operation through the registry reports all native capabilities. `WriteResult.NativeCaps` reflects that tuple. An empty raw tuple is not itself evidence that the published archive lost its geometry or history.

The bounded SOLIDWORKS part writer reports explicit transfers for readback inputs, while an authored input can leave that field for registry policy to populate. Apply the existing `CheckTransfers` policy against the writer metadata when validating this lower-level contract. Verify native modes for every source capability, actual output bytes, source-bound native acceptance and decoded feature ownership separately. Capability declarations alone do not establish semantic coverage.

The saved thin-revolve suite checks both routes. Its matching stock-zlib worker reproduces the measured complete archive and its ten logical streams. Its zlib-ng worker refuses unmeasured bytes without changing streams or files. [Coverage evidence](../../../Changes/Solidworks/Inspection/Parts/SavedThinGuardSuite.md) records the actual process results; [capability scope](../CapabilityPresenceIsNotSemanticCoverage.md) explains the wider acceptance boundary.
