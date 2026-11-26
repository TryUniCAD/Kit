from collections import Counter as CountTypes
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody


# geometry quotas exclude extra bodies carriers or attributes outside the circular profile
def CheckSpanCount(State: GeometryState, Snapshot: bool, Solid: FrustumBody) -> None:
    Bodies = 3 if Snapshot else 1
    Edges = 4 if Snapshot else 2
    PlaneCount = 4 if Snapshot else 2
    Expected = {
        "AsmRoot": 1,
        "BodyNode": Bodies,
        "LumpNode": Bodies,
        "ShellNode": Bodies,
        "FaceNode": 5 if Snapshot else 3,
        "LoopNode": 6 if Snapshot else 4,
        "CoedgeNode": 6 if Snapshot else 4,
        "EdgeNode": Edges,
        "VertexNode": Edges,
        "PointNode": Edges,
        "PlaneNode": PlaneCount,
        "EllipseNode": Edges,
        "ConeNode": 1,
        "TagAttrib": 5 if Snapshot else 6,
    }
    Counts = CountTypes(type(Value).__name__ for Value in State.Entities)
    SketchCount = (4 if Snapshot else 0) + (
        2 if Solid.BasePoint[2] == 0 or Solid.BasePoint[2] + Solid.Height == 0 else 0
    )
    if SketchCount:
        Expected["SketchAttrib"] = SketchCount
    if not Snapshot:
        Expected["TimeAttrib"] = 1
    if Counts != Expected:
        raise ValueError(
            "Native circular span contains unaccounted geometry or attributes"
        )
