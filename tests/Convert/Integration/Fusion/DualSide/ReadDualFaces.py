from dataclasses import replace as ReplaceData

from convert.adapters.Fusion.Native.Circular.Snapshots.SnapFaces import BodyFaces
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.TransformNode import (
    TransformNode,
)
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)


# identity placement nodes must be proved before creating an unplaced comparison view
def ReadDualFaces(State: GeometryState, BodyValue: BodyNode) -> tuple[FaceNode, ...]:
    if BodyValue.TransformRef == -1:
        return BodyFaces(State, BodyValue)
    Placement = State.Entities[BodyValue.TransformRef]
    assert isinstance(Placement, TransformNode)
    assert Placement.ColumnX == (1.0, 0.0, 0.0)
    assert Placement.ColumnY == (0.0, 1.0, 0.0)
    assert Placement.ColumnZ == (0.0, 0.0, 1.0)
    assert Placement.TranslationCm == (0.0, 0.0, 0.0)
    assert Placement.ScaleFactor == 1.0
    assert not (Placement.HasRotation or Placement.HasReflection or Placement.HasShear)
    return BodyFaces(State, ReplaceData(BodyValue, TransformRef=-1))
