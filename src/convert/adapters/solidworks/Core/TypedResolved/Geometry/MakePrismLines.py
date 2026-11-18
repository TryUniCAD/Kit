from math import isclose as IsClose
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineLoop import LineLoop
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.VectorPlane import PlaneVector


# actual typed line endpoints and traversal must define the rectangle without changing coordinates or sweeping the external origin point
def MakePrismLines(LoopValue: LineLoop) -> tuple[LineGeometry, ...]:
    LinesValue = tuple(
        LineGeometry(
            PlaneVector(*LoopValue.PointsValue[LineValue.StartValue].PositionValue),
            PlaneVector(*LoopValue.PointsValue[LineValue.EndValue].PositionValue),
        )
        for LineValue in LoopValue.LinesValue
    )
    OrderedValue = tuple(LinesValue[Index] for Index in LoopValue.OrderValue)
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
