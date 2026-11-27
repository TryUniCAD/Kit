from collections import Counter as CountTypes

from convert.adapters.Fusion.Native.Circular.DualSnapshots.BodyClosure import (
    BodyClosure,
)
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.CheckGeometry import (
    CheckGeometry,
)
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)


# complete entity quotas and rooted closure prevent unaccounted records from disappearing in projection
def CheckRimCover(State: GeometryState, IsFinal: bool) -> int:
    CheckGeometry(State)
    Expected = {
        "AsmRoot": 1,
        "BodyNode": 1,
        "LumpNode": 1,
        "ShellNode": 1,
        "FaceNode": 4 if IsFinal else 3,
        "LoopNode": 6 if IsFinal else 4,
        "CoedgeNode": 6 if IsFinal else 4,
        "EdgeNode": 3 if IsFinal else 2,
        "VertexNode": 3 if IsFinal else 2,
        "PointNode": 3 if IsFinal else 2,
        "PlaneNode": 2,
        "ConeNode": 1,
        "EllipseNode": 3 if IsFinal else 2,
        "TagAttrib": 6,
        "SketchAttrib": 2,
        "TimeAttrib": 1,
    }
    Expected["TorusNode" if IsFinal else "TrackAttrib"] = 1
    if CountTypes(type(Entity).__name__ for Entity in State.Entities) != Expected:
        raise ValueError("Native rim solid contains unaccounted entities")
    RootIndex = next(
        Index
        for Index, Entity in enumerate(State.Entities)
        if isinstance(Entity, BodyNode)
    )
    if set(BodyClosure(State, RootIndex)) != set(range(1, len(State.Entities))):
        raise ValueError("Native rim solid omits owned records")
    return RootIndex
