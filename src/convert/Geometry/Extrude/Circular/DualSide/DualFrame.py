from math import dist as Distance, isfinite as IsFinite

from convert.Geometry.Revolve.SweepInput import CheckSweepFrame
from convert.Geometry.Revolve.SweepVector import CrossVector, OffsetVector
from interchange.geometry.Models.GeometryCurves import CircleGeometry
from interchange.geometry.Models.Transform import Transform


# profile placement must preserve the captured right handed sketch basis
def DualFrame(FrameValue: Transform, Profile: CircleGeometry) -> Transform:
    if any(
        type(Value) not in (float, int) or not IsFinite(Value)
        for Value in (Profile.center.x, Profile.center.y)
    ):
        raise ValueError("Circular profile center must be finite")
    CheckSweepFrame(FrameValue.origin, FrameValue.z_axis, FrameValue.x_axis)
    Cross = CrossVector(FrameValue.z_axis, FrameValue.x_axis)
    if (
        not Distance(
            (Cross.x, Cross.y, Cross.z),
            (FrameValue.y_axis.x, FrameValue.y_axis.y, FrameValue.y_axis.z),
        )
        <= 1e-9
    ):
        raise ValueError("Circular profile frame must be right handed")
    Center = OffsetVector(
        OffsetVector(FrameValue.origin, FrameValue.x_axis, Profile.center.x),
        FrameValue.y_axis,
        Profile.center.y,
    )
    if not all(IsFinite(Value) for Value in (Center.x, Center.y, Center.z)):
        raise ValueError("Circular profile center exceeds finite placement")
    return Transform(
        Center,
        FrameValue.x_axis,
        FrameValue.y_axis,
        FrameValue.z_axis,
    )
