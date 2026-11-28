from convert.adapters.solidworks.Archive.Construction.Origin.OriginGraph import (
    OriginGraph,
)
from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Construction.RectangleAnchors.CornerGraph import (
    CornerGraph,
)
from convert.adapters.solidworks.Archive.Construction.RectangleAnchors.MakeCornerRel import (
    MakeCornerRel,
)
from convert.adapters.solidworks.Archive.Construction.RectangleAnchors.MakeExternalEnt import (
    MakeExternalEnt,
)
from convert.adapters.solidworks.Archive.Construction.RectangleAnchors.MakeExtPoint import (
    MakeExtPoint,
)
from convert.adapters.solidworks.Archive.Construction.RectangleAnchors.MakeOriginRef import (
    MakeOriginRef,
)
from convert.adapters.solidworks.Archive.Construction.RectangleAnchors.MakeOriginWrap import (
    MakeOriginWrap,
)
from convert.adapters.solidworks.Archive.Construction.RectangleAnchors.WireCornerMut import (
    WireCornerMut,
)
from convert.adapters.solidworks.Archive.Construction.RectangleAnchors.RequireCorner import (
    RequireCorner,
)
from convert.adapters.solidworks.Archive.Construction.RectangleAnchors.RequireOrigin import (
    RequireOrigin,
)


# anchored primitives require a real native origin coincidence rather than merely matching an initial rectangle
def MakeCornerMut(GraphValue: ProfileGraph, OriginValue: OriginGraph) -> CornerGraph:
    Dimensions = RequireCorner(GraphValue)
    RequireOrigin(GraphValue, OriginValue)
    SelectionValue = MakeOriginRef(OriginValue)
    WrapperValue = MakeOriginWrap(SelectionValue, OriginValue, GraphValue.FrameValue)
    ExternalEntity = MakeExternalEnt(WrapperValue, OriginValue)
    ExternalPoint = MakeExtPoint(
        GraphValue.GeometryValue.SketchValue,
        ExternalEntity,
        len(GraphValue.GeometryValue.PointValues),
    )
    PointValues = (*GraphValue.GeometryValue.PointValues, ExternalPoint)
    RelationValue = MakeCornerRel(GraphValue.GeometryValue.SketchValue, PointValues)
    ResultValue = CornerGraph(
        ExternalPoint,
        ExternalEntity,
        WrapperValue,
        SelectionValue,
        RelationValue,
        PointValues,
    )
    WireCornerMut(GraphValue, OriginValue, ResultValue, Dimensions)
    return ResultValue
