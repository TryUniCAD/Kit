from math import isfinite as IsFinite

from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.CheckRectRoles import (
    CheckRectRoles,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.ReadPointPair import (
    ReadPointPair,
)
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# the qualified rectangle rule requires its exact current local frame and positive ordered axis lengths before construction
def ReadRectLengths(GraphValue: ProfileGraph) -> tuple[float, float]:
    if type(GraphValue) is not ProfileGraph:
        raise TypeError("rectangle dimensions require a typed generated profile graph")
    ProfileValue, SketchValue = (
        GraphValue.ProfileValue,
        GraphValue.GeometryValue.SketchValue,
    )
    FrameValue = GraphValue.FrameValue
    if (
        ProfileValue.ClassValue != RuntimeClass("moProfileFeature_c", 1)
        or SketchValue.ClassValue != RuntimeClass("sgSketch", 1)
        or ProfileValue.FieldsValue.get("pd_f80") is not SketchValue
        or FieldInt(ProfileValue.FieldsValue, "f2b0") != 19000
        or (FrameValue.OriginValue, FrameValue.AxisU, FrameValue.AxisV)
        != ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
    ):
        raise ValueError(
            "rectangle dimensions require an ordinary current origin front plane profile"
        )
    CheckRectRoles(GraphValue)
    Positions = tuple(
        ReadPointPair(PointValue) for PointValue in GraphValue.GeometryValue.PointValues
    )
    LeftValue, BottomValue = Positions[0]
    RightValue, TopValue = Positions[2]
    LengthValues = RightValue - LeftValue, TopValue - BottomValue
    if (
        Positions[1] != (RightValue, BottomValue)
        or Positions[3] != (LeftValue, TopValue)
        or not all(
            IsFinite(LengthValue) and LengthValue > 1e-8 for LengthValue in LengthValues
        )
    ):
        raise ValueError(
            "rectangle dimensions require counterclockwise positive axes from the lower left corner"
        )
    return LengthValues
