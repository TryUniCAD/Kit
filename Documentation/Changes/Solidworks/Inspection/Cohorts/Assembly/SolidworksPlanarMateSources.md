# SOLIDWORKS planar mate source cohort

The native assembly authoring tool accepts three initial planar mate types. It creates coincident, parallel and distance mates between the principal planes of two component occurrences. It records the fixed occurrence, each participant, the assembled plane geometry and the driving distance.

Use the [five-case specification](../../../../../../re/tooling/sw2026/AssemblyMateSourceSpecs01.json) with [the pinned assembly author](../../../../../../re/tooling/sw2026/AuthorAssemblySources.py). The three discovery cases exercise single mate types. Two reserved cases use independent placements and combine mate types. Lock the original archives and COM records before implementing their generated mate graph. [Source protocol](../../../../../../re/solidworks/records/PlanarMateSourceProtocol2026.md)

Preflight checks verified the authored placement equations. The first native run created the three disclosed mates between healthy controls. The reference observer required the documented selection enum after creation. Clean saved native sources and held-out output acceptance require further verification. [Reference observation](../../../../../../re/solidworks/measurements/2026/PlanarMateReferenceType01.json)
