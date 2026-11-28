from math import isfinite as IsFinite

from convert.adapters.solidworks.Archive.Construction.Dimensions.MakePoint import (
    MakePoint,
)


# explicit text placement must determine witness offsets and endpoint caches from actual rectangle coordinates
def ReadRectPlace(
    PointsValue: tuple[tuple[float, float], ...],
    IndexValue: int,
    PointIndices: tuple[int, int],
    LengthValue: float,
    TextPoint: tuple[float, float],
) -> dict[str, object]:
    FirstIndex, LastIndex = PointIndices
    StartPoint = PointsValue[FirstIndex]
    EndPoint = PointsValue[LastIndex]
    AcrossIndex = 1 - IndexValue
    InteriorPoint = PointsValue[(FirstIndex + 2) % 4]
    AlongDirection = 1.0 if EndPoint[IndexValue] > StartPoint[IndexValue] else -1.0
    AwayDirection = (
        -1.0 if InteriorPoint[AcrossIndex] > StartPoint[AcrossIndex] else 1.0
    )
    AlongValue = (TextPoint[IndexValue] - StartPoint[IndexValue]) * AlongDirection
    AwayValue = (TextPoint[AcrossIndex] - StartPoint[AcrossIndex]) * AwayDirection
    if (
        not 0.0 <= AlongValue <= LengthValue
        or not IsFinite(AwayValue)
        or AwayValue <= 0.0
    ):
        raise ValueError(
            "rectangle dimension text must lie outside beside its dimensioned edge"
        )
    FirstValue = MakePoint(XValue=StartPoint[0], YValue=StartPoint[1])
    SecondValue = MakePoint(XValue=EndPoint[0], YValue=EndPoint[1])
    AlongVector = MakePoint(
        XValue=AlongDirection if IndexValue == 0 else 0.0,
        YValue=AlongDirection if IndexValue == 1 else 0.0,
    )
    AwayVector = MakePoint(
        XValue=AwayDirection if AcrossIndex == 0 else 0.0,
        YValue=AwayDirection if AcrossIndex == 1 else 0.0,
    )
    return {
        "f880": AwayVector,
        "f8a8": AlongValue / LengthValue,
        "f8b0": AwayValue,
        "f958": FirstValue,
        "f970": dict(FirstValue),
        "f988": SecondValue,
        "f9a0": dict(SecondValue),
        "fa38": AlongVector,
        "fad0": LengthValue,
    }
