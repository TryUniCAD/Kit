from itertools import product as GridPoints

from convert.adapters.Fusion.Native.Rectangle.RectGeometry import RectGeometry
from convert.adapters.Fusion.Native.SignedPrism.CheckSignedTags import (
    CheckRegionTags,
    SelectedCurves,
)
from convert.adapters.Fusion.Native.SignedPrism.ReadSignedBody import (
    CheckSectionOwn,
    SolidSlots,
)
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.SketchAttrib import (
    SketchAttrib,
)
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Planar.LiveTable import LiveTable
from convert.Formats.Fusion.BrepCodec.Journal.Planar.PlanarShell import PlanarShell
from convert.Formats.Fusion.BrepCodec.Journal.Planar.ReadBodyFaces import ReadBodyFaces
from convert.Formats.Fusion.BrepCodec.Journal.Planar.StableRef import StableRef
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.EmitGeometry import EmitGeometry
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.RegionFrame import (
    RegionFrame,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Reading.MapRegion import (
    MapRegion,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Reading.ReadRegion import (
    ReadRegion,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Validation.CheckRegion import (
    CheckRegion,
)
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import ReadAsmTable


# every current and retired sheet keeps complete disjoint topology and its original selected sketch labels
def ReadDraftSheets(
    Snapshot: GeometryState, Table: LiveTable, Solid: PlanarShell, Shape: RectGeometry
) -> tuple[tuple[RegionFrame, RegionFrame], frozenset[int]]:
    Edges = {
        Use.EdgeRef
        for Face in ReadBodyFaces(Table, Solid.BodyRef)
        for Use in Face.BoundaryUses
    }
    if len(Edges) != 12:
        raise ValueError("Native drafted snapshot must have twelve solid edges")
    Owned = SolidSlots(Table, Solid, Edges)
    Occupied = (
        Owned
        | set(range(Snapshot.Header.RootCount))
        | {
            Index
            for Index, Value in enumerate(Snapshot.Entities)
            if isinstance(Value, (SketchAttrib, TagAttrib))
            and StableRef(Table, Value.Links.OwnerRef) in Owned
        }
    )
    Wire = ReadAsmTable(EmitGeometry(Snapshot))
    Corners = tuple(Point for Point in Solid.PointsCm if Point[2] == 0)
    Regions = []
    Retired = frozenset()
    Curves = SelectedCurves(Shape)
    for Root in range(2, Snapshot.Header.RootCount):
        Start = 88 + (Root - 2) * 25
        Attribute = 152 + (Root - 2) * 8
        Mapping = MapRegion(Wire, Root, Start, Attribute)
        Slots = frozenset(Mapping.values())
        if Occupied.intersection(Slots):
            raise ValueError("Native drafted snapshot sheets share physical ownership")
        Occupied.update(Slots)
        Region = ReadRegion(Wire, Mapping, Start, Attribute)
        CheckSectionOwn(Snapshot, Mapping, Start, Attribute)
        if Root < 4:
            CheckRegion(Region, Corners)
            Regions.append(Region)
            continue
        CheckRegion(Region, Region.CornersCm)
        Width = max(Point[0] for Point in Region.CornersCm)
        Depth = max(Point[1] for Point in Region.CornersCm)
        if min(Width, Depth) <= 0 or set(Region.CornersCm) != set(
            GridPoints((0.0, Width), (0.0, Depth), (0.0,))
        ):
            raise ValueError(
                "Native retired sketch sheet is not an anchored XY rectangle"
            )
        CheckRegionTags(
            Region,
            {
                Tag: frozenset(
                    (Width if XValue > 0 else 0.0, Depth if YValue > 0 else 0.0)
                    for XValue, YValue in Points
                )
                for Tag, Points in Curves.items()
            },
        )
        Retired = Slots
    if Occupied != set(range(len(Snapshot.Entities))):
        raise ValueError(
            "Native drafted snapshot has records outside its qualified solid and sheet roles"
        )
    if len(Regions) != 2:
        raise ValueError(
            "Native drafted snapshot does not retain both current profile sheets"
        )
    return (Regions[0], Regions[1]), Retired
