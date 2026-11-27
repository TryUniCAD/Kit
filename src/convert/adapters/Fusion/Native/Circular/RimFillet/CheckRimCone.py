from convert.adapters.Fusion.Native.Graph.GraphChecks import SameNumbers
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.ConeNode import ConeNode


# cylinder carriers must preserve the complete unbounded source parameterization
def CheckRimCone(Surface: ConeNode, Radius: float) -> None:
    SameNumbers(Surface.OriginCm, (0.0, 0.0, 0.0))
    SameNumbers(Surface.AxisVector, (0.0, 0.0, 1.0))
    SameNumbers(Surface.MajorAxisCm, (Radius, 0.0, 0.0))
    SameNumbers(
        (
            Surface.EllipseRatio,
            Surface.SineAngle,
            Surface.CosineAngle,
            Surface.UScaleCm,
        ),
        (1.0, 0.0, 1.0, Radius),
    )
    if Surface.Reversed or any(
        Value is not None
        for Value in (
            Surface.EllipseLower,
            Surface.EllipseUpper,
            Surface.ULower,
            Surface.UUpper,
            Surface.VLower,
            Surface.VUpper,
        )
    ):
        raise ValueError("Native rim cylinder has unsupported orientation or bounds")
