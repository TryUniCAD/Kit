from collections.abc import Mapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyLoop import (
    ReadBodyLoop,
)
from interchange.geometry.Models.VectorSpace import SpaceVector


# restored stock trim vertices must come from the actual reciprocal fin graph
def ReadStockRing(
    NodesValue: Mapping[int, XmtNode], FaceValue: XmtNode
) -> tuple[SpaceVector, ...]:
    _, FinIds = ReadBodyLoop(NodesValue, FaceValue)
    Points: list[SpaceVector] = []
    for IndexValue in FinIds:
        FinValue = RequireXmt(NodesValue, IndexValue, 17)
        Vertex = RequireXmt(NodesValue, FinValue.Integer("vertex"), 18)
        PointValue = RequireXmt(NodesValue, Vertex.Integer("point"), 29)
        Point = CastValue(tuple[float, float, float], PointValue.FieldsValue["pvec"])
        Points.append(SpaceVector(*(Value * 1000 for Value in Point)))
    return tuple(Points)
