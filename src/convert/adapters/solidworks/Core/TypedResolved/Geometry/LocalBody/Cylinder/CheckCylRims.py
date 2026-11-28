from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyFaces import (
    ReadBodyFaces,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.Cylinder.CheckCylFrame import (
    CheckCylFrame,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.Cylinder.CheckCylRing import (
    CheckCylRing,
)


# mixed analytic carrier chains must agree with the boundary owners in both directions
def CheckCylChain(HeadValue: int, ChainValue: tuple[XmtNode, ...]) -> None:
    Indices = tuple(NodeValue.IndexValue for NodeValue in ChainValue)
    if HeadValue != Indices[0] or any(
        NodeValue.Integer("previous") != PriorIndex
        or NodeValue.Integer("next") != NextIndex
        for NodeValue, PriorIndex, NextIndex in zip(
            ChainValue, (0, *Indices[:-1]), (*Indices[1:], 0), strict=True
        )
    ):
        raise ValueError("local cylinder boundary carrier chain differs")


# the witnessed solid boundary has two separate cap rings paired with one mantle
def CheckCylRims(NodesValue: Mapping[int, XmtNode], BodyValue: XmtNode) -> None:
    FarCap, NearCap, SideValue = (
        NodesValue[IndexValue] for IndexValue in ReadBodyFaces(NodesValue, BodyValue, 3)
    )
    MantleValue = RequireXmt(NodesValue, SideValue.Integer("surface"), 51)
    FarLoop = RequireXmt(NodesValue, SideValue.Integer("loop"), 15)
    NearLoop = RequireXmt(NodesValue, FarLoop.Integer("next"), 15)
    if (
        MantleValue.Integer("owner") != SideValue.IndexValue
        or not MantleValue.String("sense") == SideValue.String("sense") == "+"
        or NearLoop.Integer("next")
        or FarLoop.Integer("face") != SideValue.IndexValue
        or NearLoop.Integer("face") != SideValue.IndexValue
    ):
        raise ValueError("local cylinder has an unqualified mantle boundary")
    EdgeIds = WalkXmtChain(
        NodesValue, BodyValue.Integer("edge"), 16, OwnerField="owner", OwnerValue=1
    )
    if len(EdgeIds) != 2:
        raise ValueError("local cylinder does not own two boundary edges")
    FarPlane, FarCircle = CheckCylRing(
        NodesValue, FarCap, FarLoop, NodesValue[EdgeIds[0]]
    )
    NearPlane, NearCircle = CheckCylRing(
        NodesValue, NearCap, NearLoop, NodesValue[EdgeIds[1]]
    )
    CheckCylChain(BodyValue.Integer("boundary_curve"), (FarCircle, NearCircle))
    CheckCylChain(
        BodyValue.Integer("boundary_surface"), (MantleValue, FarPlane, NearPlane)
    )
    CheckCylFrame(MantleValue, NearPlane, FarPlane, NearCircle, FarCircle)
