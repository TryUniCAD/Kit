from collections import Counter

from convert.adapters.solidworks.Core.Partition.PartMassRings import ReadMassRings
from convert.adapters.solidworks.Core.TypedResolved.Shells.Cache.CheckShellEdge import (
    CheckShellEdge,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.Cache.CheckShellSurf import (
    CheckShellSurf,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.Cache.ShellFootprint import (
    ShellFootprint,
)
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.geometry.Models.VectorSpace import SpaceVector


# a rim face owns two loops while every wall and floor owns exactly one
def ShellRingSet() -> tuple[frozenset[int], ...]:
    return tuple(
        frozenset(range(Start, Start + 4)) for Start in range(0, 16, 4)
    ) + tuple(
        frozenset(
            (
                Layer + EdgeValue,
                Layer + NextCorner,
                Layer + 4 + EdgeValue,
                Layer + 4 + NextCorner,
            )
        )
        for Layer in (0, 8)
        for EdgeValue in range(4)
        for NextCorner in ((EdgeValue + 1) % 4,)
    )


# source and expected shell corners must admit one unambiguous coordinate correspondence
def ShellCorner(
    PointValue: SpaceVector, Corners: tuple[SpaceVector, ...], Tolerance: float
) -> int:
    Matches = tuple(
        IndexValue
        for IndexValue, Expected in enumerate(Corners)
        if all(
            abs(Value) <= Tolerance
            for Value in (
                PointValue.x - Expected.x,
                PointValue.y - Expected.y,
                PointValue.z - Expected.z,
            )
        )
    )
    if len(Matches) != 1:
        raise ValueError(
            "SOLIDWORKS shell corner does not have one matching footprint position"
        )
    return Matches[0]


# the complete solid shell must match the expected individual rim floor and wall boundaries
def CheckShellRings(ModelValue: BrepModel, Footprint: ShellFootprint) -> None:
    Corners = Footprint.CornerPoints()
    BoundValue = Footprint.CornerTolerance()
    Vertices = tuple(
        ShellCorner(Value.point, Corners, BoundValue) for Value in ModelValue.vertices
    )
    if set(Vertices) != set(range(16)) or len(Vertices) != 16:
        raise ValueError("SOLIDWORKS shell saved vertices differ from its inset")
    RingsValue = ReadMassRings(ModelValue)
    RingSets = tuple(
        frozenset(
            ShellCorner(PointValue, Corners, BoundValue) for PointValue in RingValue
        )
        for RingValue in RingsValue
    )
    if Counter(RingSets) != Counter(ShellRingSet()) or any(
        len(Value) != 4 for Value in RingsValue
    ):
        raise ValueError("SOLIDWORKS shell saved loops differ from its inset")
    Faces = {Value.id: Value for Value in ModelValue.faces}
    LoopIds = tuple(
        LoopId
        for UseValue in ModelValue.face_uses
        for LoopId in Faces[UseValue.face_id].loop_ids
    )
    FacesWithRim = tuple(
        Value for Value in ModelValue.faces if len(Value.loop_ids) != 1
    )
    (RimValue,) = FacesWithRim
    Loops = {Value.id: Value for Value in ModelValue.loops}
    RingLookup = dict(zip(LoopIds, RingSets, strict=True))
    if {RingLookup[LoopId]: Loops[LoopId].outer for LoopId in RimValue.loop_ids} != {
        frozenset(range(4, 8)): True,
        frozenset(range(12, 16)): False,
    }:
        raise ValueError(
            "SOLIDWORKS shell saved opening does not occupy its historical terminal cap"
        )
    CheckShellSurf(ModelValue, dict(zip(LoopIds, RingsValue, strict=True)), BoundValue)
    CheckShellEdge(ModelValue, BoundValue)
