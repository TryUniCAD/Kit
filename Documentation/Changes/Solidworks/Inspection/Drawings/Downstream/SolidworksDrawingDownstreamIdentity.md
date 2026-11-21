# Drawing downstream edge identity source trace

PR #121 now records the source-owned distinction between a drawing edge map key, its four geometric surface references, the kernel node ID and ordinary feature identities. Native creation consumes a shared model counter, while `DOWNSTREAM_EDGE_ID` carries six words including update time and a UUID-derived model-owner key. The trace also binds the typed per-configuration cache and edge reuse after rebuild.

Use the [source ledger](../../../../../../re/solidworks/records/DrawingDownstreamIdentity2026.md) and its metadata verifier before extending drawing edge construction. The verifier requires an external licensed exact-build installation and checks original module/range/import identities without executing native software or loading a CAD file.

[Verification](../../../../../../re/solidworks/measurements/2026/DrawingDownstreamIdentitySource01.json) checked five modules, 35 ranges, three literals, eleven exports, eight imports and one delayed kernel import. No native run, new held-out credit, output file generation, complete downstream codec or public writer/projection activation is claimed. Fresh kernel enumeration and native qualification remain open.
