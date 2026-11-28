# Driving dimensions appear in sketch relations

SOLIDWORKS 2026 can return a driving radius or diameter from
`ISketchRelationManager.GetRelations(swAll)` alongside fixed, horizontal
and vertical relations. The relation enum reports `swConstraintType_RADIUS`
as 3 and `swConstraintType_DIAMETER` as 15. For the disclosed circle and
arcs, each dimension row has one arc participant. The fixed relation has
its own point participant.

For a fully constrained one-arc sketch, account for the correct dimension
row and verify its returned participant against the actual segment ID.
Also check the separate display parameter's type, writable driving state
and value. [2026 relation API example](https://help.solidworks.com/2026/english/api/sldworksapi/get_all_sketch_relations_and_their_types_example_vb.htm) ·
[Native failure and exact observed owners](../../../../../../re/solidworks/records/OrdinarySweptBossSource2026.md#first-packet-and-observer-correction)
