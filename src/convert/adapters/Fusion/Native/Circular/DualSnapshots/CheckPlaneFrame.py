from convert.adapters.Fusion.Native.Graph.GraphChecks import SameNumbers
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from interchange.geometry.Models.Transform import Transform


# profile planes must retain world placement while sketch sheets retain their local identity frame
def CheckPlaneFrame(Surface: PlaneNode, Frame: Transform) -> None:
    SameNumbers(
        Surface.OriginCm,
        (Frame.origin.x / 10, Frame.origin.y / 10, Frame.origin.z / 10),
    )
    SameNumbers(Surface.Normal, (Frame.z_axis.x, Frame.z_axis.y, Frame.z_axis.z))
    SameNumbers(Surface.ReferenceAxis, (Frame.x_axis.x, Frame.x_axis.y, Frame.x_axis.z))
    if Surface.ReversedV or any(
        Value is not None
        for Value in (Surface.ULower, Surface.UUpper, Surface.VLower, Surface.VUpper)
    ):
        raise ValueError(
            "Dual snapshot sheet plane has unsupported orientation or bounds"
        )
