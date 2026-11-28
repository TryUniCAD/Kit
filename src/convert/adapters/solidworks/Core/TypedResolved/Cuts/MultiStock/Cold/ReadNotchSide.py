from math import hypot as Hypot

from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.NotchSide import (
    NotchSide,
)
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.VectorPlane import PlaneVector


# a proper exterior notch can cross a single validated side of the rectangle
def ReadNotchSide(
    LinesValue: tuple[LineGeometry, ...], CenterValue: PlaneVector, Radius: float
) -> NotchSide:
    SidesValue: list[NotchSide] = []
    for Index, LineValue in enumerate(LinesValue):
        Origin, Finish = LineValue.start, LineValue.end
        Length = Hypot(Finish.x - Origin.x, Finish.y - Origin.y)
        if Length == 0.0:
            raise ValueError("cold rectangle contains an empty side")
        Tangent = PlaneVector(
            (Finish.x - Origin.x) / Length, (Finish.y - Origin.y) / Length
        )
        Inward = PlaneVector(-Tangent.y, Tangent.x)
        ShiftX, ShiftY = CenterValue.x - Origin.x, CenterValue.y - Origin.y
        Offset = -(ShiftX * Inward.x + ShiftY * Inward.y)
        if Offset > 0.0:
            Station = ShiftX * Tangent.x + ShiftY * Tangent.y
            SidesValue.append(
                NotchSide(Index, Offset, Station, Length, Tangent, Inward)
            )
    if len(SidesValue) != 1 or SidesValue[0].OffsetValue >= Radius:
        raise ValueError(
            "circular through cut requires one enclosed hole or one proper exterior side notch"
        )
    return SidesValue[0]
