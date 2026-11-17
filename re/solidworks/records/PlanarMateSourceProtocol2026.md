# Planar mate source protocol for SOLIDWORKS 2026

The first planar mate cohort measures coincident, parallel and distance
edges between principal planes of separate part occurrences. Each source uses
one independently authored native rectangle part and a fixed anchor. The
placements start in a valid solution. The native motion solver still provides
the stored mate state.

Use [the five authored requests](../../tooling/sw2026/AssemblyMateSourceSpecs01.json)
with the committed [assembly author](../../tooling/sw2026/AuthorAssemblySources.py)
and [mate measurement helper](../../tooling/sw2026/AssemblyMateEvidence.py).
Build the private job with the proven `kit.sw2026.ordinary-assembly-job.v1`
protocol. Pin the source and request hashes, the 34.5.2.0604 oracle and the
rectangle control. Put the authored child and parent in their own directory.

The author creates a real native mate through `AddMate5`, with normal plane
selections and success status 1. For a fixed distance without a limit range it supplies
the same distance to its upper and lower limits. The observer enumerates
`IMate2` and checks both `IMateEntity2` participants. Each reported point and
normal are checked in assembly coordinates against that occurrence's placed
principal plane. It reads the actual driving distance from the mate feature.
[Mate authoring API](https://help.solidworks.com/2025/English/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IAssemblyDoc~AddMate5.html)
and [SOLIDWORKS 2026 mate entity parameters](https://help.solidworks.com/2026/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IMateEntity2~EntityParams.html).

The initial cohort reached native mate creation for all three disclosed cases.
The observer then incorrectly applied the geometry enum to `ReferenceType2`.
The COM method reports `swSelectType_e.swSelDATUMPLANES` (4) for the three
principal plane references. The recorder observed eight finite parameters
and the correct Top, Right and Front normals. Both controls passed. The
verified correction changes only the observation gate. The authored
placements, mate requests and private hold-out observations remain fixed.
[First native reference observation](../measurements/2026/PlanarMateReferenceType01.json)
and [reference type gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Oracle/PlanarMateReferenceUsesSelectionEnum.md).

Use fresh processes to create and reopen each of the five reference pairs.
Require the analytical placements and mass properties, synchronized child
and parent save, zero warnings and an isolated reopen. Bracket the batch
with two measurements of the unchanged native rectangle control.

The two cases with combined mates are held-out from the writer construction.
Publish their archive and observation digests only. Pass the authored
placements and semantics to the writer after freezing its source. Open the
locked native comparisons after committing the candidate hashes. Qualify
driving distance edits and both exact dependency trees in that later
native comparison.
