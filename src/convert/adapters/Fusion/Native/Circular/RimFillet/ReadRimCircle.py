from math import isclose as IsClose

from convert.adapters.Fusion.Native.Graph.GraphChecks import SameNumbers
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EllipseNode import EllipseNode


# each complete circular boundary must retain its exact plane radius and parameter direction
def ReadRimCircle(
    CurveValue: EllipseNode, Radius: float, Height: float, Fillet: float
) -> str:
    Level = CurveValue.OriginCm[2]
    RoleName = (
        "bottom"
        if IsClose(Level, 0.0, abs_tol=1e-9)
        else "top" if IsClose(Level, Height, abs_tol=1e-9) else "side"
    )
    Station = (
        0.0
        if RoleName == "bottom"
        else Height if RoleName == "top" else Height - Fillet
    )
    Boundary = Radius - Fillet if RoleName == "top" else Radius
    SameNumbers(CurveValue.OriginCm, (0.0, 0.0, Station))
    SameNumbers(CurveValue.MajorAxisCm, (Boundary, 0.0, 0.0))
    SameNumbers(
        CurveValue.Normal, (0.0, 0.0, -1.0 if Fillet > 0 and RoleName == "top" else 1.0)
    )
    SameNumbers((CurveValue.EllipseRatio,), (1.0,))
    if CurveValue.LowerBound is not None or CurveValue.UpperBound is not None:
        raise ValueError("Native rim circle has unsupported carrier bounds")
    return RoleName
