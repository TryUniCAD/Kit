from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Partition.CheckXmtGraph import CheckXmtGraph
from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import (
    ReadActiveNodes,
)
from convert.adapters.solidworks.Archive.Partition.Sweeps.MakeGhostAttrib import (
    KGhostBodyKey,
)
from convert.adapters.solidworks.Archive.Partition.Sweeps.ReadSwFrame import ReadSwFrame
from convert.adapters.solidworks.Archive.Partition.Sweeps.ReadSwSect import ReadSwSect
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.CheckSwWire import (
    CheckSwWire,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.SwReadGraph import (
    SwReadGraph,
)
from interchange.geometry.Models.GeometryCurves import ArcGeometry


# a ghost transport must link actual kernel objects of each expected schema kind
def GhostLink(
    NodesValue: Mapping[int, XmtNode],
    OwnerValue: XmtNode,
    FieldName: str,
    KindValue: int,
) -> XmtNode:
    Value = NodesValue.get(OwnerValue.Integer(FieldName))
    if Value is None or Value.KindValue != KindValue:
        raise ValueError("SOLIDWORKS sweep ghost kernel link has the wrong owner class")
    return Value


# the kernel body is attributed separately from its circular edge and world slot
def GhostBodyId(NodesValue: Mapping[int, XmtNode], BodyValue: XmtNode) -> int:
    AttrValue = GhostLink(NodesValue, BodyValue, "attributes_features", 81)
    DefValue = GhostLink(NodesValue, AttrValue, "definition", 80)
    TextValue = GhostLink(NodesValue, DefValue, "identifier", 79)
    FieldsValue = AttrValue.Indexes("fields")
    if (
        AttrValue.Integer("owner") != BodyValue.IndexValue
        or TextValue.String("string") != KGhostBodyKey
        or len(FieldsValue) != 2
        or FieldsValue[0] != 0
    ):
        raise ValueError("SOLIDWORKS sweep ghost lacks its attributed body identity")
    DataValue = NodesValue.get(FieldsValue[1])
    if DataValue is None or DataValue.KindValue != 82:
        raise ValueError("SOLIDWORKS sweep ghost identity has the wrong integer type")
    (Identity,) = DataValue.Indexes("values")
    return Identity


# the live manager owns the same ordered path and section identities as the physical ghost partition
def CheckSwManager(
    PartValue: ArchiveNode, SweepValue: ArchiveNode, PathId: int, SectionId: int
) -> None:
    Manager = NativeRecord(PartValue.FieldsValue.get("fd90"))
    RowsValue = NativeRows(Manager.get("objects"))
    if Manager.get("n") != 2 or Manager.get("fe0") != 2 or Manager.get("f80") != PathId:
        raise ValueError("SOLIDWORKS sweep has an alternate ghost manager state")
    for RowValue, Identity in zip(RowsValue, (PathId, SectionId), strict=True):
        FieldsValue = NativeRecord(RowValue.get("o"))
        OwnersValue = NativeRows(FieldsValue.get("fa0"))
        if (
            FieldsValue.get("f08") != Identity
            or tuple(
                FieldsValue.get(NameValue)
                for NameValue in ("f0c", "f10", "fc0", "has_f50", "nf0")
            )
            != (8, 0, -1, 0, 0)
            or FieldsValue.get("nb0") != 1
            or OwnersValue != ({"v": NativeNodeId(SweepValue)},)
        ):
            raise ValueError(
                "SOLIDWORKS sweep ghost row does not bind its actual feature"
            )


# neither selected sketch may acquire a substituted transport body or a saved result
def BindSwGhosts(
    WrappedValue: bytes,
    PartValue: ArchiveNode,
    SweepValue: ArchiveNode,
    PathId: int,
    SectionId: int,
    SavedGraph: SwReadGraph | None = None,
) -> None:
    CheckSwManager(PartValue, SweepValue, PathId, SectionId)
    NodesValue = ReadActiveNodes(ReadSwFrame(WrappedValue))
    (WorldValue,) = (Value for Value in NodesValue.values() if Value.KindValue == 101)
    PathValue = GhostLink(NodesValue, WorldValue, "body", 12)
    SectionValue = GhostLink(NodesValue, PathValue, "next", 12)
    if (
        sum(Value.KindValue == 12 for Value in NodesValue.values()) != 2
        or PathValue.Integer("body_type") != 2
        or SectionValue.Integer("body_type") != 3
        or PathValue.Integer("previous") != 0
        or SectionValue.Integer("next") != 0
        or SectionValue.Integer("previous") != PathValue.IndexValue
        or any(
            Value.Integer("owner") != WorldValue.IndexValue
            for Value in (PathValue, SectionValue)
        )
        or (GhostBodyId(NodesValue, PathValue), GhostBodyId(NodesValue, SectionValue))
        != (PathId, SectionId)
    ):
        raise ValueError(
            "SOLIDWORKS sweep ghost partition does not match its live picks"
        )
    if SavedGraph is not None:
        CheckXmtGraph(NodesValue)
        if ReadSwSect(NodesValue, SectionValue) != SavedGraph.SectionValue.CurveValue:
            raise ValueError(
                "SOLIDWORKS saved sweep ghost section disagrees with its selected sketch"
            )
        PathCurve = SavedGraph.PathValue.CurveValue
        if type(PathCurve) is not ArcGeometry:
            raise ValueError("SOLIDWORKS saved sweep path does not own a quarter arc")
        CheckSwWire(NodesValue, PathValue, PathCurve)
