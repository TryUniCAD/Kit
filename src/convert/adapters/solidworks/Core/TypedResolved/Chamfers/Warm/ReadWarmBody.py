from collections.abc import Mapping

from convert.Geometry.Parasolid import DecodePartData
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import (
    DatumTime,
)
from convert.adapters.solidworks.Archive.Partition.History.ReadXmtStages import (
    ReadXmtStages,
)
from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import (
    ReadActiveNodes,
)
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KPartitionStream
from convert.adapters.solidworks.Container.Parasolid import DecodeBrep
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyFaces import (
    ReadBodyFaces,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyTree import (
    ReadBodyTree,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.BuildChmfGeom import (
    ChmfPrism,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ChmfOwners import (
    ChmfOwners,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ChmfPartRead import (
    ChmfEdgeRead,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfRows import (
    KChmfRoleKey,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.Warm.CheckWarmSolid import (
    CheckWarmBase,
    CheckWarmSolid,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.Warm.PickWarmEdge import (
    PickWarmEdge,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.Warm.ReadWarmRoles import (
    ReadWarmFaceId,
    ReadWarmRoles,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.Warm.WarmChmfBody import (
    WarmChmfBody,
)
from convert.adapters.solidworks.Core.TypedResolved.Fillets.CheckFilletDeps import (
    CheckFilletDeps,
)
from convert.adapters.solidworks.Core.TypedResolved.Fillets.CheckFilletUndo import (
    CheckFilletUndo,
)
from convert.adapters.solidworks.Core.TypedResolved.Fillets.ReadFilletSlot import (
    ReadFilletSlot,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismPlan import PrismPlan
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineLoop import LineLoop
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId


# retained stock faces keep their actual keys and only the directly owned bevel is new
def CheckWarmFace(
    NodesValue: Mapping[int, XmtNode],
    BodyValue: XmtNode,
    StockFaces: Mapping[int, tuple[int, ...]],
    LinkValue: NativeLink,
    Owners: ChmfOwners,
) -> int:
    ChamferId = NativeNodeId(Owners.FeatureValue)
    HeaderValue = LinkValue.ConfigValue.HeaderValue
    MatchValue = (72, ChamferId, DatumTime(HeaderValue, ChamferId), 0, 1)
    Actual = {
        IndexValue: ReadWarmFaceId(NodesValue, IndexValue)
        for IndexValue in ReadBodyFaces(NodesValue, BodyValue, 7)
    }
    (Bevel,) = (
        IndexValue for IndexValue, FaceKey in Actual.items() if FaceKey == MatchValue
    )
    _ = Actual.pop(Bevel)
    if Actual != StockFaces:
        raise ValueError(
            "saved chamfer live face ownership differs from the restored stock and chamfer keeper"
        )
    return Bevel


# the native rollback is mandatory and the modeled prism is used only to validate its active result
def ReadWarmBody(
    Archive: SldprtArchive,
    LinkValue: NativeLink,
    Owners: ChmfOwners,
    PlanValue: PrismPlan,
    LoopValue: LineLoop,
    EdgeValue: ChmfEdgeRead,
    KeysValue: tuple[KChmfRoleKey, ...],
) -> WarmChmfBody:
    Active, History = DecodePartData(
        Archive.require(KPartitionStream), KPartitionStream
    )
    if (Active.kind, History.kind) != ("partition", "deltas"):
        raise ValueError(
            "saved chamfer lacks the local partition and its delta companion"
        )
    NodesValue = ReadActiveNodes(Active.data)
    Selectors = tuple(
        FieldInt(Value.FieldsValue, "f18") for Value in Owners.Controllers
    )
    Stages = ReadXmtStages(History.data, NodesValue, Selectors)
    CheckFilletDeps(Stages)
    LiveBody, LiveName = ReadFilletSlot(
        NodesValue, Owners.AtomValue, Owners.FeatureValue
    )
    Previous = Stages[1].NodesValue
    StockBody, StockName = ReadFilletSlot(Previous, Owners.AtomValue, Owners.StockValue)
    CheckFilletUndo(Stages, LiveBody, StockBody, LiveName, StockName)
    TreeValue = ReadBodyTree(Previous)
    StockId = NativeNodeId(Owners.StockValue)
    StockFaces = {
        IndexValue: ReadWarmFaceId(Previous, IndexValue)
        for IndexValue in TreeValue.FaceIds
    }
    Roles = ReadWarmRoles(
        StockFaces, StockId, DatumTime(LinkValue.ConfigValue.HeaderValue, StockId)
    )
    CheckWarmBase(Previous, Roles, PlanValue, LoopValue)
    EdgeSlot = PickWarmEdge(Previous, TreeValue, Roles, KeysValue, EdgeValue)
    UndoValue = Stages[0].UndoValue
    if (
        TreeValue.BodyIndex != StockBody.IndexValue
        or EdgeSlot in NodesValue
        or UndoValue is None
        or not any(Value is Previous[EdgeSlot] for Value in UndoValue.RestoredValue)
    ):
        raise ValueError("saved chamfer did not restore the actual selected edge")
    FaceSlot = CheckWarmFace(NodesValue, LiveBody, StockFaces, LinkValue, Owners)
    BrepValue = DecodeBrep(Active.data)
    if BrepValue is None:
        raise ValueError("saved chamfer active partition has no valid Parasolid solid")
    CheckWarmSolid(
        NodesValue, LiveBody, BrepValue, ChmfPrism(LinkValue, Owners, EdgeValue)
    )
    return WarmChmfBody(
        BrepValue,
        Active.sha256,
        tuple(Value.MarkValue.Integer("id") for Value in Stages),
        LiveBody.IndexValue,
        EdgeSlot,
        FaceSlot,
    )
