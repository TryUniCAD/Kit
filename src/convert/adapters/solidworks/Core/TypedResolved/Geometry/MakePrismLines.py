from math import isclose as IsClose
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineLoop import LineLoop
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.VectorPlane import PlaneVector


# actual typed line endpoints and traversal define the contour and retain the required rectangle check
def MakePrismLines(
    LoopValue: LineLoop, *, RequireRectangle: bool = True
) -> tuple[LineGeometry, ...]:
    LinesValue = tuple(
        LineGeometry(
            PlaneVector(*LoopValue.PointsValue[LineValue.StartValue].PositionValue),
            PlaneVector(*LoopValue.PointsValue[LineValue.EndValue].PositionValue),
        )
        for LineValue in LoopValue.LinesValue
    )
    OrderedValue = tuple(LinesValue[Index] for Index in LoopValue.OrderValue)
    if not RequireRectangle:
        return OrderedValue
    AxisValues = tuple(
        (
            IsClose(LineValue.start.x, LineValue.end.x, rel_tol=0.0, abs_tol=1e-9),
            IsClose(LineValue.start.y, LineValue.end.y, rel_tol=0.0, abs_tol=1e-9),
        )
        for LineValue in OrderedValue
    )
    if (
        any(Vertical == Horizontal for Vertical, Horizontal in AxisValues)
        or sum(Vertical for Vertical, _ in AxisValues) != 2
    ):
        raise ValueError("cache free prism requires axis aligned rectangular sides")
    return OrderedValue
