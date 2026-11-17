# Typed planar mates in public SOLIDWORKS assembly reads

The normal assembly reader now resolves one ordinary aligned coincident,
parallel or positive-distance mate through its complete typed archive graph.
Both selected entities bind to real occurrences and actual planes in the
loaded child documents. Generated files no longer need optional saved
selection strings to produce valid neutral mate rules. The live distance
parameter supplies the neutral value in millimetres.

The profile requires archive version 19000, one configuration, one mate,
two resolved direct part occurrences and principal-plane endpoints.
Read `metadata["solidworks.typed_mates_semantics"]` for the admitted scope
and grammar coverage. Actual native file/configuration identity, stamps,
endpoint ordinals and plane geometry must agree. Unsupported or incomplete
typed graphs receive no typed success claim. A missing legacy endpoint
reports the exact typed rejection cause.

Other profiles retain the existing reader. Component resolution options,
payloads, groups, public IDs and document validation remain in place.
`ReadOptions.values["resolve_components"]=False` keeps the legacy path.
The adapter remains read-only and this change makes no new native writer
or held-out family acceptance claim.

A frozen 42-process comparison passes all six disclosed assembly reads,
preserves three previous successes and repairs three empty-entity failures.
All six projections match the independent graph path. Deferred component
behavior and all six child document JSON results match the baseline.
Fresh generated process checks cover valid identities, driving length,
disabled component resolution and fourteen independent malformed copies.
[Receipt](../../../../re/solidworks/measurements/2026/PublicTypedPlanarMates01.json)
[Scope and native rule ledger](../../../../re/solidworks/records/PublicTypedPlanarMates2026.md)
[Selection-string boundary](../../../Gotchas/Conversion/Solidworks/Archive/Assembly/SelectionStringsDoNotDefineMateEndpoints.md)
