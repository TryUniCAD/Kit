from collections.abc import Mapping
from math import dist as Distance

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.ReadXmtVector import ReadXmtVector
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.BodyTree import BodyTree
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ChmfPartRead import (
    ChmfEdgeRead,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.JoinChmfEdge import (
    CoordsChmf,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfRows import (
    KChmfRoleKey,
)


# every selected face role must come from a reciprocal fin
def OppositeWarmFin(NodesValue: Mapping[int, XmtNode], FinValue: XmtNode) -> XmtNode:
    Opposite = RequireXmt(NodesValue, FinValue.Integer("other"), 17)
    if (
        Opposite.Integer("other") != FinValue.IndexValue
        or Opposite.Integer("edge") != FinValue.Integer("edge")
        or {FinValue.String("sense"), Opposite.String("sense")} != {"+", "-"}
    ):
        raise ValueError("saved chamfer predecessor has inconsistent paired fins")
    return Opposite


# the end and neighboring face roles follow the actual positive fin
def ReadWarmPick(
    NodesValue: Mapping[int, XmtNode], EdgeIndex: int
) -> tuple[tuple[XmtNode, XmtNode], tuple[int, ...]]:
    EdgeValue = RequireXmt(NodesValue, EdgeIndex, 16)
    First = RequireXmt(NodesValue, EdgeValue.Integer("halfedge"), 17)
    Second = OppositeWarmFin(NodesValue, First)
    if First.Integer("edge") != EdgeIndex:
        raise ValueError("saved chamfer fin belongs to a different edge")
    Positive, Negative = (
        (First, Second) if First.String("sense") == "+" else (Second, First)
    )
    Neighbors = tuple(
        OppositeWarmFin(
            NodesValue, RequireXmt(NodesValue, Positive.Integer(FieldName), 17)
        )
        for FieldName in ("backward", "forward")
    )
    FaceIds = tuple(
        RequireXmt(NodesValue, FinValue.Integer("loop"), 15).Integer("face")
        for FinValue in (Positive, Negative, *Neighbors)
    )
    return (Positive, Negative), FaceIds


# selected endpoints are read from the restoring edge and independently checked against the typed profile
def PickWarmEdge(
    NodesValue: Mapping[int, XmtNode],
    TreeValue: BodyTree,
    Roles: Mapping[int, KChmfRoleKey],
    KeysValue: tuple[KChmfRoleKey, ...],
    Expected: ChmfEdgeRead,
) -> int:
    Matches: list[int] = []
    Lower, Upper = (
        CoordsChmf(Value)
        for Value in (Expected.BoundsValue.minimum, Expected.BoundsValue.maximum)
    )
    Center = CoordsChmf(Expected.EdgePoint)
    ExpectedEnds = tuple(
        tuple(
            Extent[Index] if Index == Expected.EdgeAxis else Value
            for Index, Value in enumerate(Center)
        )
        for Extent in (Lower, Upper)
    )
    for EdgeIndex in TreeValue.EdgeIds:
        FinValues, FaceIds = ReadWarmPick(NodesValue, EdgeIndex)
        if tuple(Roles[IndexValue] for IndexValue in FaceIds) != KeysValue:
            continue
        Points = tuple(
            tuple(
                Value * 1000
                for Value in ReadWarmPoint(NodesValue, FinValue.Integer("vertex"))
            )
            for FinValue in FinValues
        )
        if all(
            sum(Distance(Point, Endpoint) <= 1e-8 for Point in Points) == 1
            for Endpoint in ExpectedEnds
        ):
            Matches.append(EdgeIndex)
    if len(Matches) != 1:
        raise ValueError("saved chamfer ordered roles do not bind its restored edge")
    return Matches[0]


# vertex coordinates must resolve through the actual typed point owner
def ReadWarmPoint(
    NodesValue: Mapping[int, XmtNode], VertexIndex: int
) -> tuple[float, float, float]:
    Vertex = RequireXmt(NodesValue, VertexIndex, 18)
    return ReadXmtVector(RequireXmt(NodesValue, Vertex.Integer("point"), 29), "pvec")
