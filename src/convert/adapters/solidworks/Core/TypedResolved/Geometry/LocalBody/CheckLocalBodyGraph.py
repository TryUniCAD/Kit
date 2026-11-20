from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyFaces import (
    ReadBodyFaces,
)

from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.CheckLocalGeom import (
    CheckLocalGeom,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalRoot import (
    ReadLocalRoot,
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
def CheckLocalGraph(
    NodesValue: Mapping[int, XmtNode], *, AllowStoredAttrs: bool = False
) -> None:
    BodyValue, KindsValue = ReadLocalRoot(NodesValue, AllowStoredAttrs)
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
        if (
            not AllowStoredAttrs
            and 13 <= KindValue <= 50
            and NodeValue.Integer("attributes_features")
        ):
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
    CheckLocalGeom(NodesValue, KindsValue)
    if len(KindsValue.get(17, set())) != 2 * len(KindsValue[16]):
        raise ValueError("local solid must have two fins per edge")
