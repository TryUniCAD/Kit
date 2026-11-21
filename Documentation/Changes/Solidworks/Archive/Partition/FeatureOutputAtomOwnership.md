# Feature output atom ownership

Adds a bounded research rule for ordinary SOLIDWORKS 2026 extrusion output ownership. It distinguishes actual created/modified atom objects, retained atom IDs, manager allocation and live body publication, and pins the current loader's repair direction and modern zero-output gate.

Use the [field and caller ledger](../../../../../re/solidworks/records/FeatureOutputAtomOwnership2026.md) with the existing SDK typed archive graph and shared object maps. The [gotcha](../../../../Gotchas/Conversion/Solidworks/Archive/Partition/FeatureOutputIdsDoNotPublishAtoms.md) explains why an integer output-ID list cannot replace created-object aliases. This entry does not enable a writer or change public read behavior.

The [source-only verification receipt](../../../../../re/solidworks/measurements/2026/FeatureOutputAtomOwnershipSource01.json) records successful independent replay of 3 original module hashes, 33 complete functions, 36 instruction windows, 7 RTTI/data spans, 22 imports and 6 concrete vtable cells. No SDK/schema/codec, tests, vendor code, CAD, COM, VM or held-out inputs were executed or opened. Native initial-body acceptance and held-out generalization remain pending.
