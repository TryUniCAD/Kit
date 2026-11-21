from math import dist as Distance, isfinite as IsFinite

from convert.Geometry.Revolve.SweepInput import CheckSweepFrame
from convert.Geometry.Revolve.SweepVector import OffsetVector
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismVectors import (
    KPrismVector,
)
from interchange.geometry.Models.VectorSpace import SpaceVector


# both intake and construction must resolve the same positive axial span in wire units
def CheckCylSpan(
    StartValue: KPrismVector,
    EndValue: KPrismVector,
    AxisValue: KPrismVector,
    RadialValue: KPrismVector,
) -> None:
    StartPoint, AxisVector, Radial = (
        SpaceVector(*VectorValue)
        for VectorValue in (StartValue, AxisValue, RadialValue)
    )
    CheckSweepFrame(StartPoint, AxisVector, Radial)
    HeightValue = Distance(StartValue, EndValue)
    Projected = OffsetVector(StartPoint, AxisVector, HeightValue)
    if (
        not IsFinite(HeightValue)
        or HeightValue <= 0.0
        or Distance((Projected.x, Projected.y, Projected.z), EndValue)
        > 1e-14 * HeightValue
    ):
        raise ValueError("local cylinder has inconsistent radius or signed frame")
