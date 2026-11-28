# SOLIDWORKS planar mate source cohort

The native assembly authoring tool accepts three initial planar mate types. It creates coincident, parallel and distance mates between the principal planes of two component occurrences. It records the fixed occurrence, each participant, the assembled plane geometry and the driving distance.

Use the [five-case specification](../../../../../../re/tooling/sw2026/AssemblyMateSourceSpecs01.json) with [the pinned assembly author](../../../../../../re/tooling/sw2026/AuthorAssemblySources.py). The three discovery cases exercise single mate types. Two reserved cases use independent placements and combine mate types. Lock the original archives and COM records before implementing their generated mate graph. [Source protocol](../../../../../../re/solidworks/records/PlanarMateSourceProtocol2026.md)

Preflight checks verified the authored placement equations. A guarded run created and reopened all five native source assemblies with their mate identities, placements and driving distances intact. Both controls passed across 12 processes. The two held-out archives and their observations are sealed. Generated writer acceptance remains pending. [Source lock](../../../../../../re/solidworks/v2026/heldout/AssemblyPlanarMateSourceLock01.json)
