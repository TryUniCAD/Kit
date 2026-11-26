from collections.abc import Mapping, Sequence

from convert.adapters.solidworks.Archive.Partition.ReadXmtVector import ReadXmtVector
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyLoop import (
    ReadBodyLoop,
)


# every face loop must be geometrically contained in its actual owned plane
def CheckFacePlanes(Nodes: Mapping[int, XmtNode], FaceIds: Sequence[int]) -> None:
    for IndexValue in FaceIds:
        FaceValue = Nodes[IndexValue]
        _, FinIds = ReadBodyLoop(Nodes, FaceValue)
        Plane = Nodes[FaceValue.Integer("surface")]
        Origin = ReadXmtVector(Plane, "pvec")
        Normal = ReadXmtVector(Plane, "normal")
        AxisVector = ReadXmtVector(Plane, "x_axis")
        if (
            FaceValue.String("sense") not in {"+", "-"}
            or Plane.String("sense") not in {"+", "-"}
            or sum(Value * Value for Value in Normal) != 1.0
            or sum(Value * Value for Value in AxisVector) != 1.0
            or sum(
                NormalComponent * AxisComponent
                for NormalComponent, AxisComponent in zip(
                    Normal, AxisVector, strict=True
                )
            )
            != 0.0
        ):
            raise ValueError("attributed active face has an unsupported plane")
        for FinId in FinIds:
            Vertex = Nodes[Nodes[FinId].Integer("vertex")]
            Point = ReadXmtVector(Nodes[Vertex.Integer("point")], "pvec")
            Distance = sum(
                (Value - Start) * AxisValue
                for Value, Start, AxisValue in zip(Point, Origin, Normal, strict=True)
            )
            if Distance != 0.0:
                raise ValueError("attributed active face loop is outside its plane")
