from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Archive.Partition.XmtReferences import XmtReferences
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyFaces import (
    ReadBodyFaces,
)


# local fin links must agree across both uses of each solid edge
def CheckLocalFins(NodesValue: Mapping[int, XmtNode], FinValue: XmtNode) -> None:
    MateValue = RequireXmt(NodesValue, FinValue.Integer("other"), 17)
    NextValue = RequireXmt(NodesValue, FinValue.Integer("forward"), 17)
    if (
        MateValue.Integer("other") != FinValue.IndexValue
        or MateValue.Integer("edge") != FinValue.Integer("edge")
        or MateValue.Integer("loop") == FinValue.Integer("loop")
        or {MateValue.String("sense"), FinValue.String("sense")} != {"+", "-"}
        or NextValue.Integer("backward") != FinValue.IndexValue
        or NextValue.Integer("loop") != FinValue.Integer("loop")
        or RequireXmt(NodesValue, NextValue.Integer("other"), 17).Integer("vertex")
        != FinValue.Integer("vertex")
    ):
        raise ValueError("local body has inconsistent fin ownership")


# all transmitted nodes must belong to the single typed local solid
def CheckLocalGraph(NodesValue: Mapping[int, XmtNode]) -> None:
    BodyValue = RequireXmt(NodesValue, 1, 12)
    KindsValue: dict[int, set[int]] = {}
    for NodeValue in NodesValue.values():
        KindsValue.setdefault(NodeValue.KindValue, set()).add(NodeValue.IndexValue)
    if (
        KindsValue[12] != {1}
        or BodyValue.Integer("body_type") != 1
        or any(
            BodyValue.Integer(NameValue)
            for NameValue in (
                "owner",
                "previous",
                "next",
                "child",
                "ref_instance",
                "lattice",
                "mesh",
                "polyline",
                "boundary_lattice",
                "boundary_mesh",
                "boundary_polyline",
            )
        )
    ):
        raise ValueError("local body is outside the ordinary solid representation")
    Pending = {BodyValue.IndexValue}
    Visited: set[int] = set()
    while Pending:
        IndexValue = Pending.pop()
        Visited.add(IndexValue)
        Pending.update(set(XmtReferences(NodesValue[IndexValue])) - Visited)
    if Visited != NodesValue.keys():
        raise ValueError("local body has detached nodes")
    FaceIds = KindsValue.get(14, set())
    if (
        not FaceIds
        or set(ReadBodyFaces(NodesValue, BodyValue, len(FaceIds))) != FaceIds
    ):
        raise ValueError("local body face inventory differs")
    for KindValue, NameValue in ((16, "edge"), (18, "vertex")):
        Indexes = WalkXmtChain(
            NodesValue,
            BodyValue.Integer(NameValue),
            KindValue,
            OwnerField="owner",
            OwnerValue=1,
        )
        if not Indexes or set(Indexes) != KindsValue.get(KindValue):
            raise ValueError("local body boundary inventory differs")
    for NodeValue in NodesValue.values():
        KindValue = NodeValue.KindValue
        if 13 <= KindValue <= 50 and NodeValue.Integer("attributes_features"):
            raise ValueError("local boundary has unprojected attributes")
        if KindValue == 14:
            LoopValue = RequireXmt(NodesValue, NodeValue.Integer("loop"), 15)
            if LoopValue.Integer("face") != NodeValue.IndexValue or LoopValue.Integer(
                "next"
            ):
                raise ValueError("local face is outside the single-loop profile")
        if KindValue == 17:
            if NodeValue.Integer("curve"):
                raise ValueError("local fin carries an independent curve")
            CheckLocalFins(NodesValue, NodeValue)
    for OwnerKind, OwnerField, MemberKind in (
        (14, "surface", 50),
        (16, "curve", 30),
        (18, "point", 29),
    ):
        CarrierIds: set[int] = set()
        for IndexValue in KindsValue[OwnerKind]:
            MemberIndex = NodesValue[IndexValue].Integer(OwnerField)
            if (
                RequireXmt(NodesValue, MemberIndex, MemberKind).Integer("owner")
                != IndexValue
            ):
                raise ValueError("local geometry has a foreign topological owner")
            CarrierIds.add(MemberIndex)
        if CarrierIds != KindsValue.get(MemberKind):
            raise ValueError("local body geometry inventory differs")
    if len(KindsValue.get(17, set())) != 2 * len(KindsValue[16]):
        raise ValueError("local solid must have two fins per edge")
