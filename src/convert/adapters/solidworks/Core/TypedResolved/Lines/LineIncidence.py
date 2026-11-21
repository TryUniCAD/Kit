from collections.abc import Mapping

from convert.adapters.solidworks.Core.TypedResolved.Lines.LinePoint import LinePoint
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineSegment import LineSegment


# owned segment endpoints must establish exact incidence without guessing a polygon from coordinates
def LineIncidence(
    PointsValue: Mapping[int, LinePoint], LinesValue: tuple[LineSegment, ...]
) -> dict[int, set[int]]:
    SizeValue = len(PointsValue)
    if SizeValue < 3 or len(LinesValue) != SizeValue:
        raise ValueError("typed line ring has unowned or missing vertices")
    if (
        len({Point.CreationId for Point in PointsValue.values()}) != SizeValue
        or len({LineValue.CreationId for LineValue in LinesValue}) != SizeValue
        or len({LineValue.PermanentId for LineValue in LinesValue}) != SizeValue
    ):
        raise ValueError("typed line ring has duplicate native identities")
    Incident: dict[int, set[int]] = {Index: set() for Index in PointsValue}
    for LineValue in LinesValue:
        if (
            LineValue.StartValue not in PointsValue
            or LineValue.EndValue not in PointsValue
            or LineValue.StartValue == LineValue.EndValue
        ):
            raise ValueError("typed line ring endpoint is not an owned point")
        if (
            PointsValue[LineValue.StartValue].PositionValue
            == PointsValue[LineValue.EndValue].PositionValue
        ):
            raise ValueError("typed line ring has a degenerate segment")
        Incident[LineValue.StartValue].add(LineValue.IndexValue)
        Incident[LineValue.EndValue].add(LineValue.IndexValue)
    return Incident
