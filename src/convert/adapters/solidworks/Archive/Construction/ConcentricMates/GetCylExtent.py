from math import (
    copysign as CopySign,
    fsum as SumValues,
    isfinite as IsFinite,
    sqrt as SquareRoot,
)

from convert.adapters.solidworks.Archive.Construction.Assembly.Bounds.PlacePoint import (
    PlacePoint,
)
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.CylFaceBuild import (
    CylFaceBuild,
)
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.CylPlace import (
    CylPlace,
)


# occurrence specific bounds follow the actual physical rims and the selected wrapper sign
def GetCylExtent(
    FaceValue: CylFaceBuild, PlaceValue: CylPlace, SignedValue: bool
) -> tuple[float, float]:
    Distances: list[float] = []
    for RimValue in FaceValue.RimCentres:
        DeltaValue = tuple(
            Value - Start
            for Value, Start in zip(
                PlacePoint(PlaceValue.FrameValue, RimValue),
                PlaceValue.OriginValue,
                strict=True,
            )
        )
        Offset = SumValues(
            Value * Direction
            for Value, Direction in zip(DeltaValue, PlaceValue.WorldAxis, strict=True)
        )
        ShiftValue = tuple(Offset * Direction for Direction in PlaceValue.WorldAxis)
        Distances.append(
            CopySign(
                SquareRoot(SumValues(Value * Value for Value in ShiftValue)), Offset
            )
        )
    Lower, Upper = Distances
    if (
        Lower != 0.0
        or not IsFinite(Upper)
        or Upper == 0.0
        or (Upper < 0.0 and not SignedValue)
    ):
        raise ValueError(
            "selected circular rims do not bound the ordinary rooted axial interval"
        )
    return Lower, Upper
