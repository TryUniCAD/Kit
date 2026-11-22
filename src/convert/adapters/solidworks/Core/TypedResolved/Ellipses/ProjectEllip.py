from collections.abc import Mapping
from math import dist as Distance, hypot as HypotValue, isclose as IsClose

from convert.adapters.solidworks.Archive.Construction.Ellipse.ReadEllipAxes import (
    ReadEllipAxes,
)
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from interchange.geometry.Models.GeometryConics import EllipseGeometry
from interchange.geometry.Models.VectorPlane import PlaneVector


# each finite point coordinate reads from its own classified physical sketch row
def ReadEllipXY(PointValue: Mapping[str, object]) -> tuple[float, float]:
    Values = NativeRecord(PointValue.get("pos"))
    return RequireScalar(Values.get("x")), RequireScalar(Values.get("y"))


# a free full ellipse preserves the authored center major direction and the actual distinct minor radius
def ProjectEllip(
    PointValues: tuple[Mapping[str, object], ...],
    DepthValue: float,
) -> EllipseGeometry:
    Center, SeamValue, Major, Minor, OppMajor, OppMinor = tuple(
        ReadEllipXY(Value) for Value in PointValues
    )
    MajorX, MajorY = Major[0] - Center[0], Major[1] - Center[1]
    MinorX, MinorY = Minor[0] - Center[0], Minor[1] - Center[1]
    RadiusA, RadiusB = HypotValue(MajorX, MajorY), HypotValue(MinorX, MinorY)
    if (
        SeamValue != Major
        or not 0 < RadiusB < RadiusA
        or MajorX * MinorY - MajorY * MinorX <= 0.0
        or not IsClose(
            MajorX * MinorX + MajorY * MinorY, 0.0, rel_tol=0.0, abs_tol=1e-19
        )
        or Distance(OppMajor, (Center[0] - MajorX, Center[1] - MajorY)) > 1e-15
        or Distance(OppMinor, (Center[0] - MinorX, Center[1] - MinorY)) > 1e-15
    ):
        raise ValueError(
            "full ellipse lacks its actual signed axes and distinct major station seam"
        )
    Geometry = EllipseGeometry(
        PlaneVector(Center[0] * 1000.0, Center[1] * 1000.0),
        PlaneVector(MajorX / RadiusA, MajorY / RadiusA),
        RadiusA * 1000.0,
        RadiusB * 1000.0,
    )
    _ = ReadEllipAxes(Geometry, DepthValue)
    return Geometry
