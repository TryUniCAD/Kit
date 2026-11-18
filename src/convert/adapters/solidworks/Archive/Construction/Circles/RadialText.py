from convert.adapters.solidworks.Archive.Construction.Dimensions.MakePoint import (
    MakePoint,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.ReadRingPoint import (
    ReadRingPoint,
)
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar


# the native text node locates the authored local text in the feature world frame
def RadialText(
    FrameValue: PlaneFrame, TextPoint: tuple[float, float]
) -> dict[str, float]:
    FirstValue, SecondValue = ReadRingPoint(TextPoint)
    WorldValue = tuple(
        RequireScalar(OriginValue + UnitU * FirstValue + UnitV * SecondValue)
        for OriginValue, UnitU, UnitV in zip(
            FrameValue.OriginValue, FrameValue.AxisU, FrameValue.AxisV, strict=True
        )
    )
    return MakePoint(XValue=WorldValue[0], YValue=WorldValue[1], ZValue=WorldValue[2])
