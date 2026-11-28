from collections.abc import Mapping, Sequence

from convert.Geometry.Revolve.SweepInput import CheckSweepFrame
from convert.adapters.solidworks.Archive.Partition.LocalCylinder.BoreVectors import (
    MakeBoreVec,
)
from convert.adapters.solidworks.Archive.Partition.LocalCylinder.CheckBoreFit import (
    CheckBoreFit,
    KBoreRing,
)
from convert.adapters.solidworks.Archive.Partition.LocalCylinder.CheckBorePair import (
    CheckBorePair,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismVectors import (
    KMillimetersPerMeter,
    PrismVector,
)
from interchange.brep.Curves.BrepCurves import CircleCurve
from interchange.brep.Surfaces.BrepSurfaces import CylinderSurface, PlaneSurface


# the proof must hold on the same cap in both neutral and encoded units
def CheckBoreScale(
    OuterWall: CylinderSurface,
    WallValues: Sequence[CylinderSurface],
    CapPlanes: tuple[PlaneSurface, PlaneSurface],
    RimValues: Mapping[tuple[str, str], CircleCurve],
    Divisor: float,
) -> None:
    AxisValue = MakeBoreVec(PrismVector(OuterWall.axis))
    NearPlane, FarPlane = CapPlanes
    CapOrigins = PrismVector(NearPlane.origin), PrismVector(FarPlane.origin)
    CheckBorePair(
        CapOrigins, CapOrigins, PrismVector(OuterWall.origin), AxisValue, Divisor
    )
    BoreRings: list[KBoreRing] = []
    for WallValue in WallValues:
        NearRim = RimValues[(NearPlane.id, WallValue.id)]
        FarRim = RimValues[(FarPlane.id, WallValue.id)]
        Centres = PrismVector(NearRim.center), PrismVector(FarRim.center)
        CheckBorePair(
            Centres, CapOrigins, PrismVector(WallValue.origin), AxisValue, Divisor
        )
        BoreRings.append((Centres[0], WallValue.radius))
    CheckBoreFit((CapOrigins[0], OuterWall.radius), tuple(BoreRings), Divisor)


# each offset wall must carry the actual signed axis of one closed circular stock
def CheckAnnBores(
    OuterWall: CylinderSurface,
    WallValues: Sequence[CylinderSurface],
    CapPlanes: tuple[PlaneSurface, PlaneSurface],
    RimValues: Mapping[tuple[str, str], CircleCurve],
) -> None:
    AxisParts = PrismVector(OuterWall.axis)
    if (
        OuterWall.origin not in tuple(Value.origin for Value in CapPlanes)
        or not 0.0 < OuterWall.radius / KMillimetersPerMeter <= 1000000.0
    ):
        raise ValueError("local circular stock has an inconsistent carrier")
    AxesValue = (AxisParts, tuple(-Value for Value in AxisParts))
    for WallValue in WallValues:
        if PrismVector(WallValue.axis) not in AxesValue:
            raise ValueError("local circular bore axes must follow both cap stations")
        CheckSweepFrame(WallValue.origin, WallValue.axis, WallValue.reference_direction)
    for Divisor in (1.0, KMillimetersPerMeter):
        CheckBoreScale(OuterWall, WallValues, CapPlanes, RimValues, Divisor)
