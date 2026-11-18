from convert.adapters.solidworks.Archive.Construction.Dimensions.MakePoint import (
    MakePoint,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.PolygonGraph import (
    PolygonGraph,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.ReadPointPair import (
    ReadPointPair,
)


# explicit text placement must determine witness offsets and endpoint caches from actual rectangle coordinates
def ReadRectPlace(
    GraphValue: PolygonGraph,
    IndexValue: int,
    LengthValue: float,
    TextPoint: tuple[float, float],
) -> dict[str, object]:
    StartPoint = ReadPointPair(GraphValue.PointValues[IndexValue])
    EndPoint = ReadPointPair(GraphValue.PointValues[IndexValue + 1])
    AlongValue = TextPoint[IndexValue] - StartPoint[IndexValue]
    AwayValue = (
        StartPoint[1] - TextPoint[1]
        if IndexValue == 0
        else TextPoint[0] - StartPoint[0]
    )
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
    return {
        "f880": MakePoint(YValue=-1.0) if IndexValue == 0 else MakePoint(XValue=1.0),
        "f8a8": AlongValue / LengthValue,
        "f8b0": AwayValue,
        "f958": FirstValue,
        "f970": dict(FirstValue),
        "f988": SecondValue,
        "f9a0": dict(SecondValue),
        "fa38": MakePoint(XValue=1.0) if IndexValue == 0 else MakePoint(YValue=1.0),
        "fad0": LengthValue,
    }


from math import isfinite as IsFinite
