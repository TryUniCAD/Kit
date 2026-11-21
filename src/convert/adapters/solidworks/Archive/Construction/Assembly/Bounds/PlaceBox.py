from itertools import product as ProductValues
from math import isfinite as IsFinite
from convert.adapters.solidworks.Archive.Construction.Assembly.Bounds.PlacePoint import (
    PlacePoint,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)


# transformed occurrence bounds preserve the local sphere radius and independently transform every box corner before collecting parent extrema
def PlaceBox(BoxValue: dict[str, float], FrameValue: PlaneFrame) -> dict[str, float]:
    CornersValue = ProductValues(
        *(
            (BoxValue[f"b{IndexValue + 6}"], BoxValue[f"b{IndexValue + 3}"])
            for IndexValue in range(3)
        )
    )
    PointsValue = tuple(
        PlacePoint(FrameValue, (CornerValue[0], CornerValue[1], CornerValue[2]))
        for CornerValue in CornersValue
    )
    CenterValue = PlacePoint(
        FrameValue, (BoxValue["b0"], BoxValue["b1"], BoxValue["b2"])
    )
    NumbersValue = (
        *CenterValue,
        *(
            max(PointValue[IndexValue] for PointValue in PointsValue)
            for IndexValue in range(3)
        ),
        *(
            min(PointValue[IndexValue] for PointValue in PointsValue)
            for IndexValue in range(3)
        ),
        BoxValue["b9"],
    )
    if not all(IsFinite(NumberValue) for NumberValue in NumbersValue):
        raise ValueError("placed occurrence bounds exceed the finite native domain")
    return {
        f"b{IndexValue}": NumberValue
        for IndexValue, NumberValue in enumerate(NumbersValue)
    }
