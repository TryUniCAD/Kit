from interchange.geometry.Models.GeometryCurves import LineGeometry


# scoped native rectangles may carry roundoff while their original sketch coordinates remain untouched
def ReadRectBounds(
    Geometry: tuple[LineGeometry, ...], Scoped: bool = False
) -> tuple[float, float, float, float]:
    XValues = tuple(
        Point.x for LineValue in Geometry for Point in (LineValue.start, LineValue.end)
    )
    YValues = tuple(
        Point.y for LineValue in Geometry for Point in (LineValue.start, LineValue.end)
    )
    LowerX, UpperX, LowerY, UpperY = (
        min(XValues),
        max(XValues),
        min(YValues),
        max(YValues),
    )
    Tolerance = 1e-9 if Scoped else 0.0
    if UpperX - LowerX <= 2 * Tolerance or UpperY - LowerY <= 2 * Tolerance:
        raise ValueError("Native rectangle has degenerate planar bounds")
    if any(
        min(abs(Value - LowerX), abs(Value - UpperX)) > Tolerance for Value in XValues
    ) or any(
        min(abs(Value - LowerY), abs(Value - UpperY)) > Tolerance for Value in YValues
    ):
        raise ValueError("Native rectangle corners leave their axis aligned bounds")
    Corners = {
        (
            abs(LineValue.start.x - LowerX) <= Tolerance,
            abs(LineValue.start.y - LowerY) <= Tolerance,
        )
        for LineValue in Geometry
    }
    if len(Corners) != 4 or any(
        abs(LineValue.start.x - LineValue.end.x) > Tolerance
        and abs(LineValue.start.y - LineValue.end.y) > Tolerance
        for LineValue in Geometry
    ):
        raise ValueError("Native rectangle requires axis aligned rectangular geometry")
    return LowerX, UpperX, LowerY, UpperY
