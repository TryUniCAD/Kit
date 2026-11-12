from dataclasses import dataclass as MakeDataClass
from itertools import accumulate as Accumulate

from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.NurbsBody import (
    NurbsBody,
)


@MakeDataClass(frozen=True, slots=True)
class NurbsLayout:
    FaceBase: int
    LoopBase: int
    SurfaceBase: int
    CoedgeBase: int
    EdgeBase: int
    VertexBase: int
    PointBase: int
    PcurveBase: int
    CurveBase: int
    UseStarts: tuple[int, ...]
    EntityCount: int


def MakeNurbsLayout(Model: NurbsBody) -> NurbsLayout:
    FaceCount = len(Model.Faces)
    UseStarts = (0, *Accumulate(len(FaceSpec.Uses) for FaceSpec in Model.Faces))
    UseCount = UseStarts[-1]
    CoedgeBase = 4 + 3 * FaceCount
    EdgeBase = CoedgeBase + UseCount
    VertexBase = EdgeBase + len(Model.Edges)
    PointBase = VertexBase + len(Model.PointsCm)
    PcurveBase = PointBase + len(Model.PointsCm)
    CurveBase = PcurveBase + UseCount
    return NurbsLayout(
        4,
        4 + FaceCount,
        4 + 2 * FaceCount,
        CoedgeBase,
        EdgeBase,
        VertexBase,
        PointBase,
        PcurveBase,
        CurveBase,
        UseStarts,
        CurveBase + len(Model.Edges),
    )
