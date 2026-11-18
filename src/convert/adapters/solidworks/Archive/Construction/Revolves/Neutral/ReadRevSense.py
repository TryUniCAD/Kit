from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.RevolveShape import (
    RevolveShape,
)
from interchange.Features.FeatureAngleRev import AngularRevolve


# reversal changes the normalized effective axis while preserving the ordered source construction line and positive angle
def IsRevReverse(DefinitionValue: AngularRevolve, ShapeValue: RevolveShape) -> bool:
    OriginValue = DefinitionValue.AxisOrigin
    Direction = DefinitionValue.AxisDirection
    if (
        (OriginValue.x * 0.001, OriginValue.y * 0.001, OriginValue.z)
        != (*ShapeValue.AxisStart, 0.0)
        or Direction.x != 0.0
        or Direction.z != 0.0
        or Direction.y not in (-1.0, 1.0)
    ):
        raise ValueError(
            "normalized revolve definition differs from its actual selected axis"
        )
    return Direction.y < 0.0
