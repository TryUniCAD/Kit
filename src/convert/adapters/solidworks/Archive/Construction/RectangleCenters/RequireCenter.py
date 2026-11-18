from collections.abc import MutableMapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Construction.RectangleAnchors.CheckAnchorDims import (
    CheckAnchorDims,
)
from convert.adapters.solidworks.Archive.Construction.RectangleCenters.CheckCenterContour import (
    CheckCenterContour,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.RequirePolygon import (
    RequirePolygon,
)
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
)


# construction diagonals require the same complete dimension graph and canonical frame as the proved centered family
def RequireCenter(GraphValue: ProfileGraph) -> MutableMapping[str, object]:
    Geometry = RequirePolygon(GraphValue.GeometryValue)
    SketchValue, ProfileValue = Geometry.SketchValue, GraphValue.ProfileValue
    if (
        ProfileValue.ClassValue != RuntimeClass("moProfileFeature_c", 1)
        or ProfileValue.FieldsValue.get("pd_f80") is not SketchValue
        or FieldInt(ProfileValue.FieldsValue, "f2b0") != 19000
        or GraphValue.FrameValue
        != PlaneFrame(
            (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)
        )
    ):
        raise ValueError("center anchor requires its ordinary canonical front profile")
    CheckCenterContour(Geometry)
    Dimensions = SketchValue.FieldsValue.get("dims")
    Counters = SketchValue.FieldsValue.get("f140")
    if not isinstance(Dimensions, MutableMapping) or not isinstance(
        Counters, MutableMapping
    ):
        raise ValueError(
            "center anchor requires actual mutable dimensions and creation counters"
        )
    Dimensions = CastValue(MutableMapping[str, object], Dimensions)
    Counters = CastValue(MutableMapping[str, object], Counters)
    if (
        (
            FieldInt(Dimensions, "ng2"),
            FieldInt(Dimensions, "nlog1"),
            FieldInt(Dimensions, "nlog2"),
        )
        != (2, 4, 0)
        or len(ReadRows(Dimensions.get("val_g2"))) != 2
        or len(ReadRows(Dimensions.get("log_g1"))) != 4
        or ReadRows(Dimensions.get("log_g2"))
        or FieldInt(SketchValue.FieldsValue, "f188") != 0
        or any(FieldInt(Counters, NameValue) != 5 for NameValue in ("f08", "f0c"))
        or any(
            FieldInt(SketchValue.FieldsValue, NameValue) != 5
            for NameValue in ("f130", "f56c")
        )
    ):
        raise ValueError(
            "center anchor requires the original rectangle drivers and unconsumed creation counters"
        )
    CheckAnchorDims(Geometry, Dimensions)
    return Dimensions
