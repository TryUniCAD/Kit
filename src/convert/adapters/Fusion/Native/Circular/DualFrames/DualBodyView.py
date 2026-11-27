from dataclasses import replace as ReplaceData

from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.TransformNode import (
    TransformNode,
)
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)


# identity placement may be omitted only in a comparison object after complete validation
def DualBodyView(State: GeometryState, BodyValue: BodyNode) -> BodyNode:
    if BodyValue.TransformRef == -1:
        return BodyValue
    if not 0 <= BodyValue.TransformRef < len(State.Entities):
        raise ValueError("Native dual body placement has no target")
    Placement = State.Entities[BodyValue.TransformRef]
    if Placement != TransformNode(
        -1,
        -1,
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.0, 0.0, 1.0),
        (0.0, 0.0, 0.0),
        1.0,
        False,
        False,
        False,
    ):
        raise ValueError("Native dual body placement must be a complete identity")
    return ReplaceData(BodyValue, TransformRef=-1)
