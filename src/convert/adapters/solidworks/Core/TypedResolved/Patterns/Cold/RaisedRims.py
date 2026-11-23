from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismPlan import PrismPlan
from convert.adapters.solidworks.Core.TypedResolved.Patterns.PatternOwner import (
    PatternOwner,
)
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.VectorPlane import PlaneVector


# contained footprints define distinct upper openings and cannot add solid faces at the outside stock wall
def RaisedRims(
    PlateValue: PrismPlan, SeedValue: PrismPlan, OwnerValue: PatternOwner
) -> tuple[tuple[LineGeometry, ...], ...]:
    StockPoints = tuple(EdgeValue.start for EdgeValue in PlateValue.LinesValue)
    StockMinX = min(PointValue.x for PointValue in StockPoints)
    StockMinY = min(PointValue.y for PointValue in StockPoints)
    StockMaxX = max(PointValue.x for PointValue in StockPoints)
    StockMaxY = max(PointValue.y for PointValue in StockPoints)
    if not 0 < PlateValue.DepthValue < SeedValue.DepthValue:
        raise ValueError("cache free pattern needs a positive plate and taller seed")
    if OwnerValue.DatumValue.TiltValue is not None and (
        StockMinX != 0.0 or StockMinY != 0.0
    ):
        raise ValueError("cache free oblique pattern needs its measured origin plate")
    CountValue, PitchValue, *_ = OwnerValue.DriversValue
    Count = CountValue.LiveValue
    if type(Count) is not int:
        raise ValueError("cache free pattern count must be integral")
    Direction = OwnerValue.DatumValue.FrameValue.NormalValue
    SignedPitch = PitchValue.LiveValue * 1000.0
    if OwnerValue.DatumValue.ReversedValue:
        SignedPitch = -SignedPitch
    if Direction[2] != 0.0:
        raise ValueError("pattern direction must lie in the stock sketch plane")
    Velocity = PlaneVector(Direction[0] * SignedPitch, Direction[1] * SignedPitch)
    Profile = SeedValue.LinesValue
    SeedLowX = min(EdgeValue.start.x for EdgeValue in Profile)
    SeedHighX = max(EdgeValue.start.x for EdgeValue in Profile)
    SeedLowY = min(EdgeValue.start.y for EdgeValue in Profile)
    SeedHighY = max(EdgeValue.start.y for EdgeValue in Profile)
    Shifts = tuple(
        PlaneVector(Index * Velocity.x, Index * Velocity.y) for Index in range(Count)
    )
    BoxesValue = tuple(
        (
            SeedLowX + ShiftValue.x,
            SeedLowY + ShiftValue.y,
            SeedHighX + ShiftValue.x,
            SeedHighY + ShiftValue.y,
        )
        for ShiftValue in Shifts
    )
    if any(
        not (
            StockMinX < LowerX < UpperX < StockMaxX
            and StockMinY < LowerY < UpperY < StockMaxY
        )
        for LowerX, LowerY, UpperX, UpperY in BoxesValue
    ) or any(
        not (
            LeftBox[2] < RightBox[0]
            or RightBox[2] < LeftBox[0]
            or LeftBox[3] < RightBox[1]
            or RightBox[3] < LeftBox[1]
        )
        for Index, LeftBox in enumerate(BoxesValue)
        for RightBox in BoxesValue[:Index]
    ):
        raise ValueError(
            "cache free pattern needs wholly contained disjoint raised footprints"
        )
    return tuple(
        tuple(
            LineGeometry(
                PlaneVector(
                    EdgeValue.start.x + ShiftValue.x, EdgeValue.start.y + ShiftValue.y
                ),
                PlaneVector(
                    EdgeValue.end.x + ShiftValue.x, EdgeValue.end.y + ShiftValue.y
                ),
            )
            for EdgeValue in Profile
        )
        for ShiftValue in Shifts
    )
