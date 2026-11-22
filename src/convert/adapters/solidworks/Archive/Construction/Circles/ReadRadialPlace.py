from math import isfinite as IsFinite, sqrt as SquareRoot

from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Construction.Circles.NeedCircle import (
    NeedCircle,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakePoint import (
    MakePoint,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.ReadRingPoint import (
    ReadRingPoint,
)
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import RequireRecord


# radial leader placement derives its direction scale and offsets from explicit text and the actual circle centre
def ReadRadialPlace(
    GraphValue: ProfileGraph,
    TextPoint: tuple[float, float],
    LengthValue: float,
    IsDiameter: bool,
) -> dict[str, object]:
    TextValue = ReadRingPoint(TextPoint)
    Center = RequireRecord(NeedCircle(GraphValue).CenterValue.FieldsValue["pos"])
    CenterValue = RequireScalar(Center["x"]), RequireScalar(Center["y"])
    FirstValue, SecondValue = (
        TextValue[0] - CenterValue[0],
        TextValue[1] - CenterValue[1],
    )
    SquaredValue = FirstValue * FirstValue + SecondValue * SecondValue
    Origin = GraphValue.FrameValue.OriginValue
    NormPoint = CenterValue if Origin == (0.0, 0.0, 0.0) else Origin
    CenterSquare = sum(Value * Value for Value in NormPoint)
    if not IsFinite(SquaredValue) or not IsFinite(CenterSquare):
        raise ValueError("radial placement must retain finite distances")
    DistanceValue = SquareRoot(SquaredValue)
    FieldsValue: dict[str, object] = {
        "f958": MakePoint(XValue=CenterValue[0], YValue=CenterValue[1]),
        "f988": MakePoint(XValue=CenterValue[0], YValue=CenterValue[1]),
        "fad0": (
            SquareRoot(CenterSquare)
            if max(map(abs, NormPoint)) >= 1e-8
            else LengthValue
        ),
    }
    if max(abs(FirstValue), abs(SecondValue)) >= 1e-8:
        if SquaredValue < 1e-17:
            raise ValueError("radial leader direction is outside the native domain")
        FieldsValue["f880"] = MakePoint(
            XValue=FirstValue / DistanceValue, YValue=SecondValue / DistanceValue
        )
    if LengthValue > 1e-8:
        RadiusValue = LengthValue / 2 if IsDiameter else LengthValue
        FieldsValue["f8a8"] = RequireScalar(DistanceValue * (1 / RadiusValue))
        FieldsValue["f8b0"] = RequireScalar(DistanceValue - RadiusValue)
    return FieldsValue
