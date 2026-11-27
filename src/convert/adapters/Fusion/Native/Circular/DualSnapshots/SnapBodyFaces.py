from convert.adapters.Fusion.Native.Circular.DualFrames.DualBodyView import DualBodyView
from convert.adapters.Fusion.Native.Circular.Snapshots.SnapFaces import BodyFaces
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)


# explicit identity bookkeeping must remain owned and covered while the existing shell walker inspects world geometry
def SnapBodyFaces(State: GeometryState, BodyValue: BodyNode) -> tuple[FaceNode, ...]:
    return BodyFaces(State, DualBodyView(State, BodyValue))
