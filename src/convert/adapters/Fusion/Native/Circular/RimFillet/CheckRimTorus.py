from convert.adapters.Fusion.Native.Graph.GraphChecks import SameNumbers
from convert.Formats.Fusion.BrepCodec.Journal.Round.TorusNode import TorusNode


# the round is the exact outer quarter of a dimension derived torus rather than a fitted surface
def CheckRimTorus(
    Surface: TorusNode, Radius: float, Height: float, Fillet: float
) -> None:
    SameNumbers(Surface.CenterCm, (0.0, 0.0, Height - Fillet))
    SameNumbers(Surface.AxisVector, (0.0, 0.0, 1.0))
    SameNumbers(Surface.ReferenceAxis, (1.0, 0.0, 0.0))
    SameNumbers(
        (Surface.MajorRadiusCm, Surface.MinorRadiusCm), (Radius - Fillet, Fillet)
    )
    if Surface.ReversedV or any(
        Value is not None
        for Value in (Surface.ULower, Surface.UUpper, Surface.VLower, Surface.VUpper)
    ):
        raise ValueError("Native rim torus has unsupported orientation or bounds")
