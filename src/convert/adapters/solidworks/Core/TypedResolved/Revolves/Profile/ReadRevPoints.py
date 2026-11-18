from collections.abc import Mapping

from convert.adapters.solidworks.Core.TypedResolved.Lines.LinePoint import LinePoint
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineSegment import LineSegment
from convert.adapters.solidworks.Core.TypedResolved.Lines.ReadLinePoint import (
    ReadLinePoint,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Profile.ReadAxisPoint import (
    ReadAxisPoint,
)


# standalone axis points and deleted history cannot become extra live body contour vertices
def ReadRevPoints(
    RowsValue: tuple[Mapping[str, object], ...],
    AxisValue: LineSegment,
    LinesValue: tuple[LineSegment, ...],
) -> tuple[Mapping[int, LinePoint], Mapping[int, LinePoint], tuple[LinePoint, ...]]:
    Indices = (AxisValue.StartValue, AxisValue.EndValue)
    if Indices[0] == Indices[1] or any(
        not 0 <= IndexValue < len(RowsValue) for IndexValue in Indices
    ):
        raise ValueError("ordinary revolve axis endpoint indices differ")
    AxisPoints = {
        IndexValue: ReadAxisPoint(
            RowsValue[IndexValue], IndexValue, AxisValue.IndexValue
        )
        for IndexValue in Indices
    }
    ContourIds = {
        IndexValue
        for LineValue in LinesValue
        for IndexValue in (LineValue.StartValue, LineValue.EndValue)
    }
    if len(ContourIds) != 4 or ContourIds.intersection(AxisPoints):
        raise ValueError("ordinary revolve axis shares an unqualified contour endpoint")
    PointsValue: dict[int, LinePoint] = {}
    RetiredPoints: list[LinePoint] = []
    for IndexValue, RowValue in enumerate(RowsValue):
        if IndexValue in AxisPoints:
            continue
        PointValue = ReadLinePoint(RowValue, IndexValue)
        if PointValue.CreationId < 0:
            RetiredPoints.append(PointValue)
        else:
            PointsValue[IndexValue] = PointValue
    if (
        set(PointsValue) != ContourIds
        or len(
            {
                PointValue.CreationId
                for PointValue in (*PointsValue.values(), *AxisPoints.values())
            }
        )
        != 6
    ):
        raise ValueError(
            "ordinary revolve has additional or duplicate live point owners"
        )
    return PointsValue, AxisPoints, tuple(RetiredPoints)
