from collections.abc import Mapping, Sequence
from math import isfinite as IsFinite

from convert.Geometry.Revolve.SweepVector import CrossVector, DotVector, OffsetVector
from convert.adapters.solidworks.Archive.Partition.ReadXmtVector import ReadXmtVector
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyLoop import (
    ReadBodyLoop,
)
from interchange.geometry.Models.VectorSpace import SpaceVector


# containment and winding must agree with the plane and face orientation before projection
def CheckFacePlanes(Nodes: Mapping[int, XmtNode], FaceIds: Sequence[int]) -> None:
    for IndexValue in FaceIds:
        FaceValue = Nodes[IndexValue]
        _, FinIds = ReadBodyLoop(Nodes, FaceValue)
        Plane = Nodes[FaceValue.Integer("surface")]
        Origin = ReadXmtVector(Plane, "pvec")
        Normal = ReadXmtVector(Plane, "normal")
        AxisVector = ReadXmtVector(Plane, "x_axis")
        SenseValue = FaceValue.String("sense")
        if (
            SenseValue not in {"+", "-"}
            or Plane.String("sense") != "+"
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
        Points: list[SpaceVector] = []
        for FinId in FinIds:
            Vertex = Nodes[Nodes[FinId].Integer("vertex")]
            Point = ReadXmtVector(Nodes[Vertex.Integer("point")], "pvec")
            Distance = sum(
                (Value - Start) * AxisValue
                for Value, Start, AxisValue in zip(Point, Origin, Normal, strict=True)
            )
            if Distance != 0.0:
                raise ValueError("attributed active face loop is outside its plane")
            Points.append(SpaceVector(*Point))
        First, Second, Third, Fourth = Points
        DiagonalNormal = CrossVector(
            OffsetVector(Third, First, -1.0), OffsetVector(Fourth, Second, -1.0)
        )
        TwiceArea = DotVector(DiagonalNormal, SpaceVector(*Normal))
        if not IsFinite(TwiceArea) or not (
            TwiceArea > 0.0 if SenseValue == "+" else TwiceArea < 0.0
        ):
            raise ValueError("attributed active face sense contradicts its fin cycle")
