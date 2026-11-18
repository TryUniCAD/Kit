from convert.adapters.solidworks.Archive.Construction.Origin.OriginGraph import (
    OriginGraph,
)
from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Construction.RectangleAnchors.MakeExtPoint import (
    MakeExtPoint,
)
from convert.adapters.solidworks.Archive.Construction.RectangleAnchors.MakeExternalEnt import (
    MakeExternalEnt,
)
from convert.adapters.solidworks.Archive.Construction.RectangleAnchors.MakeOriginRef import (
    MakeOriginRef,
)
from convert.adapters.solidworks.Archive.Construction.RectangleAnchors.MakeOriginWrap import (
    MakeOriginWrap,
)
from convert.adapters.solidworks.Archive.Construction.RectangleAnchors.RequireOrigin import (
    RequireOrigin,
)
from convert.adapters.solidworks.Archive.Construction.RectangleCenters.CenterGraph import (
    CenterGraph,
)
from convert.adapters.solidworks.Archive.Construction.RectangleCenters.MakeCenterDiagonal import (
    MakeCenterDiagonal,
)
from convert.adapters.solidworks.Archive.Construction.RectangleCenters.MakeCenterRelation import (
    MakeCenterRelation,
)
from convert.adapters.solidworks.Archive.Construction.RectangleCenters.RequireCenter import (
    RequireCenter,
)
from convert.adapters.solidworks.Archive.Construction.RectangleCenters.WireCenterMut import (
    WireCenterMut,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.MakeLineHandle import (
    MakeLineHandle,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.MakeRingPoint import (
    MakeRingPoint,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.RequirePolygon import (
    RequirePolygon,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakePointRef import (
    MakePointRef,
)


# centered source intent needs real diagonal construction geometry and an actual origin reference before the common boss is serialized
def MakeCenterMut(GraphValue: ProfileGraph, OriginValue: OriginGraph) -> CenterGraph:
    Dimensions = RequireCenter(GraphValue)
    RequireOrigin(GraphValue, OriginValue)
    Geometry = RequirePolygon(GraphValue.GeometryValue)
    SketchValue = Geometry.SketchValue
    CenterValue = MakeRingPoint(SketchValue, (0.0, 0.0), len(Geometry.PointValues))
    CenterValue.FieldsValue["fe4"] = 1
    LocalPoints = (*Geometry.PointValues, CenterValue)
    Diagonals = tuple(
        MakeCenterDiagonal(
            SketchValue,
            LocalPoints,
            Geometry.PointValues[IndexValue],
            Geometry.PointValues[IndexValue + 2],
            len(Geometry.LineValues) + IndexValue,
        )
        for IndexValue in range(2)
    )
    LinesValue = (*Geometry.LineValues, *Diagonals)
    Selection = MakeOriginRef(OriginValue)
    Wrapper = MakeOriginWrap(Selection, OriginValue, GraphValue.FrameValue)
    ExternalEntity = MakeExternalEnt(Wrapper, OriginValue)
    ExternalPoint = MakeExtPoint(SketchValue, ExternalEntity, len(LocalPoints))
    PointsValue = (*LocalPoints, ExternalPoint)
    Relations = tuple(
        MakeCenterRelation(
            SketchValue,
            MakePointRef(SketchValue, PointsValue, CenterValue),
            MakeLineHandle(
                SketchValue, DiagonalValue, len(Geometry.LineValues) + IndexValue
            ),
        )
        for IndexValue, DiagonalValue in enumerate(Diagonals)
    )
    Relations += (
        MakeCenterRelation(
            SketchValue,
            MakePointRef(SketchValue, PointsValue, ExternalPoint),
            MakePointRef(SketchValue, PointsValue, CenterValue),
        ),
    )
    Result = CenterGraph(
        CenterValue, ExternalPoint, Diagonals, Relations, PointsValue, LinesValue
    )
    WireCenterMut(GraphValue, OriginValue, Result, Dimensions)
    return Result
