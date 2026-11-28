from math import hypot as RadiusDistance
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Construction.Circles.NeedCircle import (
    NeedCircle,
)
from convert.adapters.solidworks.Archive.Construction.Circles.MakeArcHandle import (
    MakeArcHandle,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeLengthParam import (
    MakeLengthParam,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakePoint import (
    MakePoint,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.DimBaseFields import (
    DimBaseFields,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import RequireRecord


# the radial driver must refer to the actual full circle and derive its length from the modeled centre and seam
def MakeRadialVal(GraphValue: ProfileGraph, IsDiameter: bool) -> ArchiveNode:
    if type(CastValue(object, IsDiameter)) is not bool:
        raise TypeError("radial mode requires an explicit diameter flag")
    Geometry = NeedCircle(GraphValue)
    CenterValue = RequireRecord(Geometry.CenterValue.FieldsValue["pos"])
    MarkerValue = RequireRecord(Geometry.MarkerValue.FieldsValue["pos"])
    RadiusValue = RadiusDistance(
        RequireScalar(MarkerValue["x"]) - RequireScalar(CenterValue["x"]),
        RequireScalar(MarkerValue["y"]) - RequireScalar(CenterValue["y"]),
    )
    LengthValue = RadiusValue * (2 if IsDiameter else 1)
    Parameter = MakeLengthParam(GraphValue.ProfileValue, LengthValue)
    FieldsValue = DimBaseFields()
    FieldsValue.update(
        {
            "owner": GraphValue.ProfileValue,
            "_sketch": Geometry.SketchValue,
            "f28": Parameter,
            "f80": 15 if IsDiameter else 3,
            "f90": 2,
            "f94": 0,
            "f98": 0,
            "fa0": 0,
            "g1": 0,
            "g2": 0,
            "dir": MakePoint(XValue=1.0),
            "h1": MakeArcHandle(Geometry.SketchValue, Geometry.ArcValue, 0),
            "h2": ArchiveNode(
                RuntimeClass("sgEntHandle", 1),
                {"_sketch": None, "idx": 0x777F, "f18": -2, "f1c": -1, "f08": 0},
            ),
        }
    )
    return ArchiveNode(RuntimeClass("sgCircleDim", 1), FieldsValue)
