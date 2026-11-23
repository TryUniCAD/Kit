from collections.abc import Mapping, Sequence

from convert.Geometry.Revolve.SweepInput import CheckSweepFrame
from convert.adapters.solidworks.Archive.Partition.LocalCylinder.CheckBoreFit import (
    CheckBoreFit,
    KBoreRing,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismVectors import (
    KMillimetersPerMeter,
    KPrismVector,
    PrismVector,
)
from interchange.brep.Curves.BrepCurves import CircleCurve
from interchange.brep.Surfaces.BrepSurfaces import CylinderSurface, PlaneSurface


# a principal frame selects two exact transverse coordinates without projection drift
def CrossSection(PointValue: KPrismVector, AxisIndex: int, Radius: float) -> KBoreRing:
    First, Second = (
        Value for Index, Value in enumerate(PointValue) if Index != AxisIndex
    )
    return First, Second, Radius


# both rims must be on the owned cap planes at the same transverse position
def CheckBorePair(
    CentresValue: tuple[KPrismVector, KPrismVector],
    CapOrigins: tuple[KPrismVector, KPrismVector],
    WallOrigin: KPrismVector,
    WallRadius: float,
    AxisIndex: int,
) -> KBoreRing:
    NearPoint, FarPoint = CentresValue
    NearCap, FarCap = CapOrigins
    NearRing = CrossSection(NearPoint, AxisIndex, WallRadius)
    if (
        NearPoint[AxisIndex] != NearCap[AxisIndex]
        or FarPoint[AxisIndex] != FarCap[AxisIndex]
        or CrossSection(FarPoint, AxisIndex, WallRadius) != NearRing
        or WallOrigin not in CentresValue
    ):
        raise ValueError("local circular bore does not join its two exact cap stations")
    return NearRing


# placement needs an exact signed coordinate axis to avoid an ambiguous projection
def BoreAxisIndex(AxisParts: KPrismVector) -> int:
    AxisIndices = tuple(Index for Index, Value in enumerate(AxisParts) if Value != 0.0)
    if len(AxisIndices) != 1 or abs(AxisParts[AxisIndices[0]]) != 1.0:
        raise ValueError("local offset bores require one signed principal axis")
    return AxisIndices[0]


# multiple offset walls are qualified for one outward stock on a signed principal frame
def CheckAnnBores(
    OuterWall: CylinderSurface,
    WallValues: Sequence[CylinderSurface],
    CapPlanes: tuple[PlaneSurface, PlaneSurface],
    RimValues: Mapping[tuple[str, str], CircleCurve],
) -> None:
    AxisParts = PrismVector(OuterWall.axis)
    AxisIndex = BoreAxisIndex(AxisParts)
    if (
        OuterWall.origin not in tuple(Value.origin for Value in CapPlanes)
        or not 0.0 < OuterWall.radius / KMillimetersPerMeter <= 1000000.0
    ):
        raise ValueError("local circular stock has an inconsistent carrier")
    AxesValue = (AxisParts, tuple(-Value for Value in AxisParts))
    NearPlane, FarPlane = CapPlanes
    CapOrigins = PrismVector(NearPlane.origin), PrismVector(FarPlane.origin)
    BoreRings: list[KBoreRing] = []
    for WallValue in WallValues:
        if PrismVector(WallValue.axis) not in AxesValue:
            raise ValueError("local circular bore axes must follow both cap stations")
        CheckSweepFrame(WallValue.origin, WallValue.axis, WallValue.reference_direction)
        NearRim = RimValues[(NearPlane.id, WallValue.id)]
        FarRim = RimValues[(FarPlane.id, WallValue.id)]
        BoreRings.append(
            CheckBorePair(
                (PrismVector(NearRim.center), PrismVector(FarRim.center)),
                CapOrigins,
                PrismVector(WallValue.origin),
                WallValue.radius,
                AxisIndex,
            )
        )
    StockRing = CrossSection(CapOrigins[0], AxisIndex, OuterWall.radius)
    for Divisor in (1.0, KMillimetersPerMeter):
        CheckBoreFit(StockRing, tuple(BoreRings), Divisor)
