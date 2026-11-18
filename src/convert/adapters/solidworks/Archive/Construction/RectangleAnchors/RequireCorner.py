from collections.abc import MutableMapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.PolygonGraph import (
    PolygonGraph,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.ReadPointPair import (
    ReadPointPair,
)
from convert.adapters.solidworks.Archive.Construction.RectangleAnchors.CheckCornerGeom import (
    CheckCornerGeom,
)
from convert.adapters.solidworks.Archive.Construction.RectangleAnchors.CheckAnchorDims import (
    CheckAnchorDims,
)
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
)


# adding an origin relation must not overwrite another anchor or accept off origin or unrelated geometry
def RequireCorner(GraphValue: ProfileGraph) -> MutableMapping[str, object]:
    if (
        type(GraphValue) is not ProfileGraph
        or type(GraphValue.GeometryValue) is not PolygonGraph
    ):
        raise TypeError("corner anchor requires a constructed polygon profile")
    GeometryValue, ProfileValue = GraphValue.GeometryValue, GraphValue.ProfileValue
    SketchValue = GeometryValue.SketchValue
    if (
        ProfileValue.ClassValue != RuntimeClass("moProfileFeature_c", 1)
        or ProfileValue.FieldsValue.get("pd_f80") is not SketchValue
        or FieldInt(ProfileValue.FieldsValue, "f2b0") != 19000
        or GraphValue.FrameValue
        != PlaneFrame(
            (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)
        )
    ):
        raise ValueError(
            "corner anchor requires the current origin front plane profile"
        )
    if (
        len(GeometryValue.PointValues) != 4
        or len(GeometryValue.LineValues) != 4
        or ReadPointPair(GeometryValue.PointValues[0]) != (0.0, 0.0)
    ):
        raise ValueError(
            "corner anchor requires four rectangle vertices with the first at origin"
        )
    RowsValue = ReadRows(SketchValue.FieldsValue.get("points"))
    if len(RowsValue) != 4 or any(
        RowValue.get("kind") != 0 or RowValue.get("point") is not PointValue.FieldsValue
        for RowValue, PointValue in zip(
            RowsValue, GeometryValue.PointValues, strict=True
        )
    ):
        raise ValueError("corner anchor requires actual fresh owned contour point rows")
    Dimensions = SketchValue.FieldsValue.get("dims")
    if not isinstance(Dimensions, MutableMapping):
        raise ValueError("corner anchor requires the actual dimension manager")
    Dimensions = CastValue(MutableMapping[str, object], Dimensions)
    if (
        FieldInt(Dimensions, "ng2") != 2
        or len(ReadRows(Dimensions.get("val_g2"))) != 2
        or FieldInt(Dimensions, "nlog1") != 4
        or len(ReadRows(Dimensions.get("log_g1"))) != 4
        or FieldInt(Dimensions, "nlog2") != 0
        or ReadRows(Dimensions.get("log_g2"))
        or FieldInt(SketchValue.FieldsValue, "f188") != 0
    ):
        raise ValueError(
            "corner anchor requires existing rectangle drivers and no prior coincidence"
        )
    CheckCornerGeom(GeometryValue)
    CheckAnchorDims(GeometryValue, Dimensions)
    Counters = SketchValue.FieldsValue.get("f140")
    if not isinstance(Counters, MutableMapping):
        raise ValueError("corner anchor requires mutable point creation counters")
    if CastValue(MutableMapping[str, object], Counters).get("f08") != 5:
        raise ValueError(
            "corner anchor requires the actual next point creation counter"
        )
    return Dimensions
