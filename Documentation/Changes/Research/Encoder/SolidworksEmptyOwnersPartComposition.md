# SOLIDWORKS empty owners in a generated part

The [research composition command](../../../../re/solidworks/records/EmptyOwnersPartComposition.md) combines the exact-sketch presentation request, the empty appearance-state request and the empty cut-list property-owner request. It generates an archive with a present appearance allocator and a concrete empty cut-list owner while retaining the already checked sketch, D1 and Top view.

Two fresh runs produced the same 14-stream archive. Compared with the fresh exact-sketch base, only Definition changed among existing streams. The command added the binary property owner and three independently generated empty XML members. Three owner controls isolated each stream change, and four invalid requests refused before output. [Offline evidence](../../../../re/solidworks/measurements/2026/EmptyOwnersPartComposition.json)

The pinned readers have distinct outcomes. The ordinary Definition guard rejects the allocator profile. Public reader options and revisions also change the returned diagnostics and boss operation. Native application acceptance and full source fidelity remain unverified. [Reader roster gotcha](../../../Gotchas/Research/Writers/SolidworksStrictGeometryDependsOnPropertyStreamRoster.md)
