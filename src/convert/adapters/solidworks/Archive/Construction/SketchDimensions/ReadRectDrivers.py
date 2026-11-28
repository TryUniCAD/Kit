from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.CheckRectRoles import (
    CheckRectRoles,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.ReadRectEdges import (
    ReadRectEdges,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.ReadPointPair import (
    ReadPointPair,
)
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import (
    PrincipalFrame,
)
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# dimensions on either admitted principal frame retain their actual signed endpoint roles before allocation
def ReadRectDrivers(
    GraphValue: ProfileGraph,
) -> tuple[tuple[int, int, float], tuple[int, int, float]]:
    if type(GraphValue) is not ProfileGraph:
        raise TypeError("rectangle dimensions require a typed generated profile graph")
    ProfileValue, SketchValue = (
        GraphValue.ProfileValue,
        GraphValue.GeometryValue.SketchValue,
    )
    NegativeV = GraphValue.FrameValue == PrincipalFrame("y")
    if (
        ProfileValue.ClassValue != RuntimeClass("moProfileFeature_c", 1)
        or SketchValue.ClassValue != RuntimeClass("sgSketch", 1)
        or ProfileValue.FieldsValue.get("pd_f80") is not SketchValue
        or FieldInt(ProfileValue.FieldsValue, "f2b0") != 19000
        or (not NegativeV and GraphValue.FrameValue != PrincipalFrame("z"))
    ):
        raise ValueError(
            "rectangle dimensions require a current origin front or top plane profile"
        )
    CheckRectRoles(GraphValue)
    GeometryValue = GraphValue.GeometryValue
    Drivers = ReadRectEdges(GeometryValue, NegativeV)
    if NegativeV and ReadPointPair(GeometryValue.PointValues[0]) != (0.0, 0.0):
        raise ValueError("signed top plane rectangle must start at the model origin")
    return Drivers
