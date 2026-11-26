from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyFaces import (
    ReadBodyFaces,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.CheckLocalFins import (
    CheckLocalFins,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.CheckLocalGeom import (
    CheckLocalGeom,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalRoot import (
    ReadLocalRoot,
)


# all transmitted nodes must belong to the single typed local solid
def CheckLocalGraph(NodesValue: Mapping[int, XmtNode]) -> None:
    BodyValue, KindsValue = ReadLocalRoot(NodesValue)
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
    CheckLocalGeom(NodesValue, KindsValue)
    if len(KindsValue.get(17, set())) != 2 * len(KindsValue[16]):
        raise ValueError("local solid must have two fins per edge")
