from math import isclose as IsClose

from convert.adapters.Fusion.Native.Graph.GraphChecks import SameNumbers
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode


# physical cap stations must select distinct bottom and top roles without trusting their labels
def ReadRimPlane(Surface: PlaneNode, Height: float) -> str:
    RoleName = "bottom" if IsClose(Surface.OriginCm[2], 0.0, abs_tol=1e-9) else "top"
    SameNumbers(Surface.OriginCm, (0.0, 0.0, 0.0 if RoleName == "bottom" else Height))
    SameNumbers(Surface.Normal, (0.0, 0.0, 1.0))
    SameNumbers(Surface.ReferenceAxis, (1.0, 0.0, 0.0))
    if Surface.ReversedV or any(
        Value is not None
        for Value in (Surface.ULower, Surface.UUpper, Surface.VLower, Surface.VUpper)
    ):
        raise ValueError("Native rim cap has unsupported orientation or bounds")
    return RoleName
