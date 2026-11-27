from collections.abc import Mapping, Sequence

from convert.adapters.solidworks.Archive.Partition.ReadXmtVector import ReadXmtVector
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.Partition.Current.Attributed.ReadEdgePoints import (
    ReadEdgePoints,
)


# only fully witnessed line boundaries can use the typed planar recovery
def CheckOwnedLines(Nodes: Mapping[int, XmtNode], EdgeIds: Sequence[int]) -> None:
    for IndexValue in EdgeIds:
        EdgeValue = Nodes[IndexValue]
        LineValue = Nodes[EdgeValue.Integer("curve")]
        Origin = ReadXmtVector(LineValue, "pvec")
        Direction = ReadXmtVector(LineValue, "direction")
        First, LastValue = ReadEdgePoints(Nodes, EdgeValue)
        if (
            First == LastValue
            or LineValue.String("sense") not in {"+", "-"}
            or sum(Value * Value for Value in Direction) != 1.0
        ):
            raise ValueError("attributed active edge has an unsupported line")
        for EndValue in (First, LastValue):
            DeltaX, DeltaY, DeltaZ = (
                Value - Start for Value, Start in zip(EndValue, Origin, strict=True)
            )
            DirXValue, DirYValue, DirZValue = Direction
            if (DeltaY * DirZValue, DeltaX * DirZValue, DeltaX * DirYValue) != (
                DeltaZ * DirYValue,
                DeltaZ * DirXValue,
                DeltaY * DirXValue,
            ):
                raise ValueError(
                    "attributed active edge endpoints are outside their line"
                )
