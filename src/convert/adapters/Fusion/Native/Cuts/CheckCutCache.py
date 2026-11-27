from convert.adapters.Fusion.Native.Cuts.ReadCacheFaces import ReadCacheFaces
from convert.adapters.Fusion.Native.Cuts.PickCacheShape import PickCacheShape
from convert.adapters.Fusion.Native.Cuts.CheckCutSolid import CheckCutSolid
from convert.adapters.Fusion.Native.Cuts.PrismRings import PrismRings
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.Formats.Fusion.BrepCodec.Journal.Planar.LiveTable import LiveTable
from convert.Formats.Fusion.BrepCodec.Journal.Planar.CheckLineEdge import CheckLineEdge
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.adapters.Fusion.Native.Rectangle.RectGeometry import RectGeometry


# both tool solids and their independent sketch sheets must agree with the two source profiles
def CheckCutCache(
    Snapshot: GeometryState,
    Shapes: tuple[RectGeometry, RectGeometry],
    Heights: tuple[float, float],
) -> None:
    if Snapshot.Header.RootCount != 7:
        raise ValueError("Native cut cache has unexpected body roles")
    Slots = tuple(range(len(Snapshot.Entities)))
    Table = LiveTable(0, Snapshot.Entities, Slots, Slots, Slots)
    Rings = tuple(
        PrismRings(tuple(LineValue.start for LineValue in Shape.Lines), 0.0, Height)
        for Shape, Height in zip(Shapes, Heights, strict=True)
    )
    Points = tuple(
        tuple({Point for RingValue in Boundaries for Point in RingValue})
        for Boundaries in Rings
    )
    Sketches = tuple(
        tuple((Point[0], Point[1], 0.0) for Point in Boundaries[1])
        for Boundaries in Rings
    )
    SeenRoles: set[tuple[int, str]] = set()
    for BodyRef, BodyValue in enumerate(Snapshot.Entities):
        if not isinstance(BodyValue, BodyNode):
            continue
        Faces = ReadCacheFaces(Table, BodyRef)
        IsSheet = len(Faces) == 1
        ShapeId = PickCacheShape(Table, Faces, Sketches if IsSheet else Points)
        if IsSheet:
            FaceValue = Snapshot.Entities[Faces[0].FaceRef]
            if not isinstance(FaceValue, FaceNode) or len(Faces[0].BoundaryUses) != 4:
                raise ValueError("Native cut sketch cache has an invalid boundary")
            RoleName = "sheet" if FaceValue.DoubleSided else "region"
            for UseValue in Faces[0].BoundaryUses:
                CheckLineEdge(Table, UseValue.EdgeRef)
        else:
            CheckCutSolid(Table, BodyRef, Rings[ShapeId])
            RoleName = "solid"
        if (ShapeId, RoleName) in SeenRoles:
            raise ValueError("Native cut cache repeats an authored body role")
        SeenRoles.add((ShapeId, RoleName))
    if SeenRoles != {
        (Index, RoleName)
        for Index in range(2)
        for RoleName in ("solid", "sheet", "region")
    }:
        raise ValueError("Native cut cache omits an authored body role")
