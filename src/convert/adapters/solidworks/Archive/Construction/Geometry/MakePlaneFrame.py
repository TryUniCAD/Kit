from math import isclose as IsClose

from convert.adapters.solidworks.Archive.Construction.Geometry.CrossVector import (
    CrossVector,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.DotVector import (
    DotVector,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.UnitVector import (
    UnitVector,
)
from convert.adapters.solidworks.Assembly.PlanarMates.ReadPlane import ReadVector


# native frame construction normalizes the ordered tangents before deriving its orthogonal plane basis
def MakePlaneFrame(
    OriginValue: tuple[float, float, float],
    AxisU: tuple[float, float, float],
    AxisV: tuple[float, float, float],
) -> PlaneFrame:
    Origin = ReadVector(dict(zip(("x", "y", "z"), OriginValue, strict=True)))
    First, Second = UnitVector(AxisU), UnitVector(AxisV)
    if not IsClose(DotVector(First, Second), 0.0, abs_tol=1e-12):
        raise ValueError("native frame tangents must be perpendicular")
    Normal = UnitVector(CrossVector(First, Second))
    return PlaneFrame(Origin, First, CrossVector(Normal, First), Normal)
