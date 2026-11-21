from math import isclose as IsClose

from convert.Geometry.Revolve.SweepVector import CrossVector, DotVector, OffsetVector
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.Saved.ReadThinPoints import (
    IsPointNear,
)
from interchange.brep.Surfaces.BrepSurfaces import (
    BrepSurface,
    CylinderSurface,
    PlaneSurface,
)
from interchange.geometry.Models.VectorSpace import SpaceVector


# native carriers can choose different origins and basis signs on the same support
def CheckThinFace(Actual: BrepSurface, Expected: BrepSurface) -> None:
    if isinstance(Actual, PlaneSurface) and isinstance(Expected, PlaneSurface):
        AxisValue = DotVector(Actual.normal, Expected.normal)
        ShiftValue = OffsetVector(Actual.origin, Expected.origin, -1.0)
        Separation = abs(DotVector(ShiftValue, Expected.normal))
        if (
            IsClose(abs(AxisValue), 1.0, rel_tol=0.0, abs_tol=1e-12)
            and Separation <= 1e-9
        ):
            return
    if isinstance(Actual, CylinderSurface) and isinstance(Expected, CylinderSurface):
        AxisValue = DotVector(Actual.axis, Expected.axis)
        ShiftValue = OffsetVector(Actual.origin, Expected.origin, -1.0)
        ShiftCross = CrossVector(ShiftValue, Expected.axis)
        if (
            IsClose(abs(AxisValue), 1.0, rel_tol=0.0, abs_tol=1e-12)
            and IsPointNear(ShiftCross, SpaceVector(0.0, 0.0, 0.0))
            and IsClose(Actual.radius, Expected.radius, rel_tol=1e-12, abs_tol=1e-9)
        ):
            return
    raise ValueError("SOLIDWORKS thin cache face has an unresolved sector support")
