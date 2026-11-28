from convert.Geometry.Revolve.SweepInput import CheckSweepFrame
from convert.Geometry.Revolve.SweepVector import DotVector, OffsetVector
from convert.adapters.solidworks.Archive.Partition.LocalCylinder.CheckCylSpan import (
    CheckCylSpan,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismVectors import (
    KMillimetersPerMeter,
    PrismMeters,
    PrismVector,
)
from interchange.brep.Surfaces.BrepSurfaces import CylinderSurface, PlaneSurface


# both end planes must bound the exterior cylindrical carrier on the same axis
def ReadAnnPlanes(
    OuterValue: CylinderSurface,
    PlanesValue: tuple[PlaneSurface, ...],
) -> tuple[PlaneSurface, PlaneSurface]:
    First, Second = PlanesValue
    AxisValue = OuterValue.axis
    DeltaValue = OffsetVector(Second.origin, First.origin, -1.0)
    NearPlane, FarPlane = (
        (First, Second) if DotVector(DeltaValue, AxisValue) > 0.0 else (Second, First)
    )
    CheckCylSpan(
        PrismMeters(NearPlane.origin),
        PrismMeters(FarPlane.origin),
        PrismVector(AxisValue),
        PrismVector(OuterValue.reference_direction),
    )
    return NearPlane, FarPlane


# the concentric profile preserves its exact coaxial and frame requirements
def CheckAnnFrame(
    OuterValue: CylinderSurface,
    InnerValue: CylinderSurface,
    PlanesValue: tuple[PlaneSurface, ...],
) -> tuple[PlaneSurface, PlaneSurface]:
    NearPlane, FarPlane = ReadAnnPlanes(OuterValue, PlanesValue)
    AxisValue = OuterValue.axis
    AxisParts = PrismVector(AxisValue)
    AxesValue = (AxisParts, tuple(-Value for Value in AxisParts))
    if (
        not 0.0
        < InnerValue.radius / KMillimetersPerMeter
        < OuterValue.radius / KMillimetersPerMeter
        <= 1000000.0
        or PrismVector(InnerValue.axis) not in AxesValue
        or any(
            Value.origin not in (NearPlane.origin, FarPlane.origin)
            for Value in (OuterValue, InnerValue)
        )
    ):
        raise ValueError("local annulus requires distinct coaxial cylindrical walls")
    CheckSweepFrame(InnerValue.origin, InnerValue.axis, InnerValue.reference_direction)
    return NearPlane, FarPlane
