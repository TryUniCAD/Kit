from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.RequirePolygon import (
    RequirePolygon,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeAxisDim import (
    MakeAxisDim,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.PublishRectMut import (
    PublishRectMut,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# a native rectangle can carry four logical line relations without inventing width height or anchor drivers
def MakeAxisOnlyMut(GraphValue: ProfileGraph, Allocator: PersistentIds) -> None:
    GeometryValue = RequirePolygon(GraphValue.GeometryValue)
    LogicalValues = tuple(
        MakeAxisDim(GeometryValue, IndexValue) for IndexValue in range(4)
    )
    OwnerValue = ArchiveNode.RequireNode(GraphValue.ProfileValue.FieldsValue["owner"])
    PublishRectMut(
        GraphValue,
        (),
        LogicalValues,
        Allocator,
        FieldInt(OwnerValue.FieldsValue, "fd44"),
    )
