from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.LocalPrism.CheckPocketLoop import (
    CheckPocketLoop,
)
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
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.CheckPocketFins import (
    CheckPocketFins,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalRoot import (
    ReadLocalRoot,
)


# individual boundary cells must agree with their local owners and permitted auxiliary state
def CheckLocalCells(
    NodesValue: Mapping[int, XmtNode], AllowStoredAttrs: bool, AllowPocket: bool
) -> None:
    for NodeValue in NodesValue.values():
        KindValue = NodeValue.KindValue
        if (
            not AllowStoredAttrs
            and 13 <= KindValue <= 50
            and NodeValue.Integer("attributes_features")
        ):
            raise ValueError("local boundary has unprojected attributes")
        if KindValue == 14 and not AllowPocket:
            LoopValue = RequireXmt(NodesValue, NodeValue.Integer("loop"), 15)
            if LoopValue.Integer("face") != NodeValue.IndexValue or LoopValue.Integer(
                "next"
            ):
                raise ValueError("local face is outside the single-loop profile")
        if KindValue == 17:
            if NodeValue.Integer("curve"):
                raise ValueError("local fin carries an independent curve")
            CheckLocalFins(NodesValue, NodeValue)


# all transmitted nodes must belong to the single typed local solid
def CheckLocalGraph(
    NodesValue: Mapping[int, XmtNode],
    *,
    AllowStoredAttrs: bool = False,
    AllowPocket: bool = False,
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
    if AllowPocket:
        if (
            BodyValue.Integer("attributes_features")
            or BodyValue.Integer("attribute_chains")
            or any(KindValue >= 70 for KindValue in KindsValue)
        ):
            raise ValueError("local pocket has unqualified body attributes")
        CheckPocketLoop(NodesValue)
        CheckPocketFins(NodesValue)
    CheckLocalCells(NodesValue, AllowStoredAttrs, AllowPocket)
    CheckLocalGeom(NodesValue, KindsValue)
    if len(KindsValue.get(17, set())) != 2 * len(KindsValue[16]):
        raise ValueError("local solid must have two fins per edge")
