from convert.adapters.Fusion.Native.Graph.GraphValues import CheckIdentity
from convert.Formats.Fusion.EntityCodec.Model.MatrixValue import MatrixValue
from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from interchange.geometry.Models.Transform import (
    KAxisX,
    KAxisY,
    KAxisZ,
    KOriginZero,
    KTransformIdentity,
    Transform,
)
from interchange.geometry.Models.VectorSpace import SpaceVector


# source matrix copies must match the independently qualified principal sketch frame
def CheckFrameValue(Value: KEntityValue, FrameValue: Transform) -> None:
    if (
        FrameValue.origin != KOriginZero
        or FrameValue.x_axis != KAxisX
        or (FrameValue.y_axis, FrameValue.z_axis)
        not in ((KAxisY, KAxisZ), (SpaceVector(0.0, 0.0, -1.0), KAxisY))
    ):
        raise ValueError("Native circular source frame is outside qualified XY or XZ")
    if FrameValue == KTransformIdentity:
        CheckIdentity(Value)
        return
    Expected = (
        FrameValue.x_axis.x,
        FrameValue.y_axis.x,
        FrameValue.z_axis.x,
        FrameValue.origin.x / 10,
        FrameValue.x_axis.y,
        FrameValue.y_axis.y,
        FrameValue.z_axis.y,
        FrameValue.origin.y / 10,
        FrameValue.x_axis.z,
        FrameValue.y_axis.z,
        FrameValue.z_axis.z,
        FrameValue.origin.z / 10,
        0.0,
        0.0,
        0.0,
        1.0,
    )
    if not isinstance(Value, MatrixValue) or Value.Entries != Expected:
        raise ValueError(
            "Native sketch matrix disagrees with its qualified source frame"
        )
