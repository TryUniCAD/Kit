from math import fsum as SumValues

from convert.adapters.solidworks.Archive.Construction.Assembly.Bounds.PlacePoint import (
    PlacePoint,
)
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.CylPlace import (
    CylPlace,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# rigid projection preserves the ordered signed component directions and native arithmetic order
def MakeCylPlaces(
    References: tuple[ArchiveNode, ArchiveNode],
    FramesValue: tuple[PlaneFrame, PlaneFrame],
    LocalAxes: tuple[tuple[float, float, float], tuple[float, float, float]],
    OriginValue: tuple[float, float, float],
) -> tuple[CylPlace, CylPlace]:
    Places: list[CylPlace] = []
    for Reference, FrameValue, AxisValue in zip(
        References, FramesValue, LocalAxes, strict=True
    ):
        WorldAxis = tuple(
            SumValues(
                Value * Other for Value, Other in zip(AxisValue, Column, strict=True)
            )
            for Column in zip(
                FrameValue.AxisU, FrameValue.AxisV, FrameValue.NormalValue, strict=True
            )
        )
        Places.append(
            CylPlace(
                Reference,
                FrameValue,
                AxisValue,
                PlacePoint(FrameValue, OriginValue),
                (WorldAxis[0], WorldAxis[1], WorldAxis[2]),
            )
        )
    return Places[0], Places[1]
