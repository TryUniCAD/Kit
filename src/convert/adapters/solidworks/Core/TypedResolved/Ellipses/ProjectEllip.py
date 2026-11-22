from collections.abc import Mapping


from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.TypedResolved.Ellipses.EllipAxisGeom import (
    EllipAxisGeom,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from interchange.geometry.Models.GeometryConics import EllipseGeometry


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
    if (
        SeamValue != Major
        or OppMajor
        != tuple(
            First - (OtherValue - First)
            for First, OtherValue in zip(Center, Major, strict=True)
        )
        or OppMinor
        != tuple(
            First - (OtherValue - First)
            for First, OtherValue in zip(Center, Minor, strict=True)
        )
    ):
        raise ValueError(
            "full ellipse lacks its actual signed axes and distinct major station seam"
        )
    return EllipAxisGeom(Center, Major, Minor, DepthValue)
