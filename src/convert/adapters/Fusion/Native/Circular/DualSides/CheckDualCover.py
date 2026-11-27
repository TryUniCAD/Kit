from convert.adapters.Fusion.Native.Circular.DualFrames.DualBodyView import DualBodyView
from collections import Counter as CountTypes

from convert.adapters.Fusion.Native.Circular.Snapshots.CheckCoverage import (
    CheckCoverage,
)
from convert.adapters.Fusion.Native.Circular.Snapshots.SnapFaces import (
    BodyFaces,
    FaceCoedges,
)
from convert.adapters.Fusion.Native.Circular.Spans.ReadSpanBody import ReadSpanBody
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.LoopNode import LoopNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)


# exact closed topology quotas prevent unrelated live geometry or attributes from disappearing
def CheckDualCover(State: GeometryState) -> None:
    Expected = {
        "AsmRoot": 1,
        "BodyNode": 1,
        "LumpNode": 1,
        "ShellNode": 1,
        "FaceNode": 4,
        "LoopNode": 6,
        "CoedgeNode": 6,
        "EdgeNode": 3,
        "VertexNode": 3,
        "PointNode": 3,
        "PlaneNode": 2,
        "ConeNode": 2,
        "EllipseNode": 3,
        "TagAttrib": 8,
        "SketchAttrib": 2,
        "TimeAttrib": 1,
    }
    BodyValue, _ = ReadSpanBody(State)
    if BodyValue.TransformRef != -1:
        Expected["TransformNode"] = 1
    if CountTypes(type(Entity).__name__ for Entity in State.Entities) != Expected:
        raise ValueError("Native dual side live state contains unaccounted entities")
    CheckCoverage(State)
    Faces = BodyFaces(State, DualBodyView(State, BodyValue))
    if {State.Entities.index(FaceValue) for FaceValue in Faces} != {
        Index
        for Index, Entity in enumerate(State.Entities)
        if isinstance(Entity, FaceNode)
    }:
        raise ValueError("Native dual side body omits live faces")
    SeenSlots: set[int] = set()
    for FaceValue in Faces:
        for Coedge in FaceCoedges(State, FaceValue):
            Index = State.Entities.index(Coedge)
            LoopValue = State.Entities[Coedge.OwnerLoop]
            if (
                Index in SeenSlots
                or not isinstance(LoopValue, LoopNode)
                or LoopValue.FirstCoedge != Index
                or LoopValue.OwnerFace != State.Entities.index(FaceValue)
            ):
                raise ValueError("Native dual side loop ownership is not reciprocal")
            SeenSlots.add(Index)
    if SeenSlots != {
        Index
        for Index, Entity in enumerate(State.Entities)
        if isinstance(Entity, CoedgeNode)
    }:
        raise ValueError("Native dual side faces omit live boundary uses")
