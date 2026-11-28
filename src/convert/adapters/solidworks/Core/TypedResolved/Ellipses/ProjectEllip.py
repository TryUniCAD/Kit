from collections.abc import Mapping
from math import dist as Distance, hypot as HypotValue, isclose as IsClose

from convert.adapters.solidworks.Archive.Construction.Ellipse.EllipsePlan import (
    KEllipStations,
)
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


# the signed stations recover the ordinary analytic conic independently from its seam aliases
def EvalEllipGeo(Stations: KEllipStations, DepthValue: float) -> EllipseGeometry:
    Center, Major, Minor = Stations
    MajorX, MajorY = Major[0] - Center[0], Major[1] - Center[1]
    MinorX, MinorY = Minor[0] - Center[0], Minor[1] - Center[1]
    RadiusA, RadiusB = HypotValue(MajorX, MajorY), HypotValue(MinorX, MinorY)
    if (
        not 0 < RadiusB < RadiusA
        or MajorX * MinorY - MajorY * MinorX <= 0.0
        or not IsClose(
            MajorX * MinorX + MajorY * MinorY, 0.0, rel_tol=0.0, abs_tol=1e-19
        )
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


# the full conic keeps independent signed stations and checks the actual seam and reflected owners
def ProjectEllip(
    PointValues: tuple[Mapping[str, object], ...],
    DepthValue: float,
) -> tuple[EllipseGeometry, KEllipStations]:
    Center, SeamValue, Major, Minor, OppMajor, OppMinor = tuple(
        ReadEllipXY(Value) for Value in PointValues
    )
    if SeamValue != Major or any(
        Distance(
            Opposite,
            tuple(
                Origin - (Value - Origin)
                for Origin, Value in zip(Center, AxisValue, strict=True)
            ),
        )
        > 1e-15
        for AxisValue, Opposite in ((Major, OppMajor), (Minor, OppMinor))
    ):
        raise ValueError(
            "full ellipse lacks its actual signed axes and distinct major station seam"
        )
    Stations = (Center, Major, Minor)
    return EvalEllipGeo(Stations, DepthValue), Stations
