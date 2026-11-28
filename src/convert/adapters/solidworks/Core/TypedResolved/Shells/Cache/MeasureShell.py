from math import isclose as IsClose

from convert.adapters.solidworks.Core.Partition.PartMass import PlanarMoments
from convert.adapters.solidworks.Core.TypedResolved.Shells.Cache.ShellFootprint import (
    ShellFootprint,
)
from interchange.brep.Topology.BrepModel import BrepModel


# actual outward shell moments must independently agree with removed box volume
def MeasureShell(
    ModelValue: BrepModel, Footprint: ShellFootprint
) -> tuple[float, float, tuple[float, float, float]]:
    Minimum, Maximum = Footprint.Bounds.minimum, Footprint.Bounds.maximum
    Width, Depth, Height = (
        Maximum.x - Minimum.x,
        Maximum.y - Minimum.y,
        Maximum.z - Minimum.z,
    )
    Thickness = Footprint.Thickness
    InnerWidth, InnerDepth, InnerHeight = (
        Width - 2 * Thickness,
        Depth - 2 * Thickness,
        Height - Thickness,
    )
    Cavity = InnerWidth * InnerDepth * InnerHeight
    Expected = Width * Depth * Height - Cavity
    CentreExpected = (
        Width / 2,
        Depth / 2,
        (Width * Depth * Height**2 / 2 - Cavity * (Height + Thickness) / 2) / Expected,
    )
    Signed, XMoment, YMoment, ZMoment = PlanarMoments(ModelValue, Minimum)
    if not IsClose(Signed, Expected, rel_tol=5e-7):
        raise ValueError("SOLIDWORKS shell saved volume differs from its inward offset")
    Centroid = XMoment / Signed, YMoment / Signed, ZMoment / Signed
    if not all(
        IsClose(Value, RefValue, rel_tol=5e-7)
        for Value, RefValue in zip(Centroid, CentreExpected, strict=True)
    ):
        raise ValueError(
            "SOLIDWORKS shell saved centroid differs from its inward offset"
        )
    SurfaceArea = 2 * (
        Width * Depth
        + Height * (Width + Depth)
        + InnerHeight * (InnerWidth + InnerDepth)
    )
    return (
        Signed,
        SurfaceArea,
        (Minimum.x + Centroid[0], Minimum.y + Centroid[1], Minimum.z + Centroid[2]),
    )
