from convert.adapters.Fusion.Native.SignedPrism.ReadSignedBody import SolidSlots
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.SketchAttrib import (
    SketchAttrib,
)
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Planar.LiveTable import LiveTable
from convert.Formats.Fusion.BrepCodec.Journal.Planar.PlanarShell import PlanarShell
from convert.Formats.Fusion.BrepCodec.Journal.Planar.ReadBodyFaces import ReadBodyFaces
from convert.Formats.Fusion.BrepCodec.Journal.Planar.StableRef import StableRef
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)


# solid geometry and attached attributes must be owned before auxiliary sheet records are assigned
def DraftSheetSlots(
    Snapshot: GeometryState, Table: LiveTable, Solid: PlanarShell
) -> set[int]:
    Edges = {
        EdgeUse.EdgeRef
        for Surface in ReadBodyFaces(Table, Solid.BodyRef)
        for EdgeUse in Surface.BoundaryUses
    }
    if len(Edges) != 12:
        raise ValueError("Native drafted snapshot must have twelve solid edges")
    Owned = SolidSlots(Table, Solid, Edges)
    return (
        Owned
        | set(range(Snapshot.Header.RootCount))
        | {
            Index
            for Index, Value in enumerate(Snapshot.Entities)
            if isinstance(Value, (SketchAttrib, TagAttrib))
            and StableRef(Table, Value.Links.OwnerRef) in Owned
        }
    )
