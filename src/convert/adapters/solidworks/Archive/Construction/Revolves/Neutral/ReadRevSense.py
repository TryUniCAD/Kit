from convert.adapters.solidworks.Archive.Construction.Assembly.Bounds.PlacePoint import (
    PlacePoint,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.RevolveShape import (
    RevolveShape,
)
from interchange.Features.FeatureAngleRev import AngularRevolve


# reversal changes the normalized effective axis while preserving the ordered source construction line and positive angle
def IsRevReverse(
    DefinitionValue: AngularRevolve, ShapeValue: RevolveShape, FrameValue: PlaneFrame
) -> bool:
    OriginValue = DefinitionValue.AxisOrigin
    Direction = DefinitionValue.AxisDirection
    Upward = FrameValue.AxisV
    Downward = tuple(-NumberValue for NumberValue in Upward)
    ActualAxis = (Direction.x, Direction.y, Direction.z)
    ExpectedStart = PlacePoint(FrameValue, (*ShapeValue.AxisStart, 0.0))
    if (
        OriginValue.x * 0.001,
        OriginValue.y * 0.001,
        OriginValue.z * 0.001,
    ) != ExpectedStart or ActualAxis not in (Upward, Downward):
        raise ValueError(
            "normalized revolve definition differs from its actual selected axis"
        )
    return ActualAxis == Downward
