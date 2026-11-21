from math import (
    acos as ArcCos,
    atan2 as ArcTan,
    hypot as Hypot,
    isfinite as IsFinite,
    sqrt as SquareRoot,
)

from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.ReadNotchSide import (
    ReadNotchSide,
)
from convert.Geometry.Extrude.Trimmed.TrimMeasures import ArcArea
from interchange.geometry.Models.GeometryCurves import ArcGeometry, LineGeometry
from interchange.geometry.Models.VectorPlane import PlaneVector


# the removed circular segment defines both the closed trim and its analytic first moment
def BuildNotchRing(
    LinesValue: tuple[LineGeometry, ...], CenterValue: PlaneVector, Radius: float
) -> tuple[tuple[LineGeometry | ArcGeometry, ...], float, PlaneVector]:
    SideValue = ReadNotchSide(LinesValue, CenterValue, Radius)
    Index = SideValue.IndexValue
    Origin, Finish = LinesValue[Index].start, LinesValue[Index].end
    Offset = SideValue.OffsetValue
    HalfLength = SquareRoot((Radius - Offset) * (Radius + Offset))
    Start, FinishStation = (
        SideValue.StationValue - HalfLength,
        SideValue.StationValue + HalfLength,
    )
    RearPoint = LinesValue[Index - 1].start
    if (
        not 0.0 < Start < FinishStation < SideValue.LengthValue
        or Radius - Offset >= Hypot(RearPoint.x - Origin.x, RearPoint.y - Origin.y)
    ):
        raise ValueError(
            "circular notch crosses a corner, touches a wall or cuts multiple stock sides"
        )
    Tangent = SideValue.TangentValue
    Enter = PlaneVector(Origin.x + Tangent.x * Start, Origin.y + Tangent.y * Start)
    Leave = PlaneVector(
        Origin.x + Tangent.x * FinishStation, Origin.y + Tangent.y * FinishStation
    )
    Angle = ArcTan(Leave.y - CenterValue.y, Leave.x - CenterValue.x)
    ArcValue = ArcGeometry(
        CenterValue, Radius, Angle, Angle + 2 * ArcCos(Offset / Radius)
    )
    AreaValue = ArcArea(ArcValue)
    if not IsFinite(AreaValue) or AreaValue <= 0.0:
        raise ValueError("circular notch has no representable removed area")
    Shift = (2.0 / 3.0) * HalfLength**3 / AreaValue
    Inward = SideValue.InwardValue
    Centroid = PlaneVector(
        CenterValue.x + Inward.x * Shift, CenterValue.y + Inward.y * Shift
    )
    return (
        (
            *LinesValue[:Index],
            LineGeometry(Origin, Enter),
            ArcValue,
            LineGeometry(Leave, Finish),
            *LinesValue[Index + 1 :],
        ),
        AreaValue,
        Centroid,
    )
