from collections.abc import Mapping
from math import isclose as IsClose

from convert.adapters.solidworks.Archive.Partition.ReadXmtVector import ReadXmtVector
from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# selected edge geometry comes from the two typed previous stock vertices
def ReadStockPoint(
    NodesValue: Mapping[int, XmtNode], VertexId: int
) -> tuple[float, float, float]:
    Vertex = RequireXmt(NodesValue, VertexId, 18)
    Point = RequireXmt(NodesValue, Vertex.Integer("point"), 29)
    return ReadXmtVector(Point, "pvec")


# endpoint only supports must select different ends of the actual historical edge
def ReadFilletEnds(
    NodesValue: Mapping[int, XmtNode],
    Faces: tuple[int, ...],
    FirstValue: XmtNode,
    LastValue: XmtNode,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    First = ReadStockPoint(NodesValue, FirstValue.Integer("vertex"))
    Final = ReadStockPoint(NodesValue, LastValue.Integer("vertex"))
    PlaneHits: list[tuple[int, ...]] = []
    for FaceId in Faces:
        FaceValue = RequireXmt(NodesValue, FaceId, 14)
        Surface = RequireXmt(NodesValue, FaceValue.Integer("surface"), 50)
        Normal = ReadXmtVector(Surface, "normal")
        Origin = ReadXmtVector(Surface, "pvec")
        PlaneHits.append(
            tuple(
                Index
                for Index, PointValue in enumerate((First, Final))
                if IsClose(
                    sum(
                        (Value - OriginValue) * AxisValue
                        for Value, OriginValue, AxisValue in zip(
                            PointValue, Origin, Normal, strict=True
                        )
                    ),
                    0.0,
                    rel_tol=0.0,
                    abs_tol=1e-11,
                )
            )
        )
    if (
        First == Final
        or PlaneHits[:2] != [(0, 1), (0, 1)]
        or sorted(PlaneHits[2:]) != [(0,), (1,)]
    ):
        raise ValueError("saved fillet face roles differ from actual stock endpoints")
    return First, Final
