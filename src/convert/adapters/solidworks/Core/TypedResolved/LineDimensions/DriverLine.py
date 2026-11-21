from math import hypot as Hypotenuse, isclose as IsClose

from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.LineDriver import (
    LineDriver,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineLoop import LineLoop
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineSegment import LineSegment


# selected point references must resolve to one actual segment without matching a scalar to a guessed edge
def DriverLine(DriverValue: LineDriver, LoopValue: LineLoop) -> LineSegment:
    PointValues = DriverValue.PointValues
    if len(set(PointValues)) != 2 or any(
        Index not in LoopValue.PointsValue for Index in PointValues
    ):
        raise ValueError("typed rectangle distance has invalid point references")
    Matches = tuple(
        LineValue
        for LineValue in LoopValue.LinesValue
        if {LineValue.StartValue, LineValue.EndValue} == set(PointValues)
    )
    if len(Matches) != 1:
        raise ValueError("typed rectangle distance does not select one owned line")
    StartValue, EndValue = (
        LoopValue.PointsValue[Index].PositionValue for Index in PointValues
    )
    LengthValue = Hypotenuse(EndValue[0] - StartValue[0], EndValue[1] - StartValue[1])
    if not IsClose(
        LengthValue, 1000.0 * DriverValue.MetresValue, rel_tol=1e-9, abs_tol=1e-9
    ):
        raise ValueError("typed rectangle parameter disagrees with its selected points")
    return Matches[0]
