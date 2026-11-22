from collections.abc import Mapping
from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Partition.KernelShapes import KKernelShapes
from convert.adapters.solidworks.Archive.Partition.Sweeps.MakeGhostAttrib import (
    MakeGhostAttr,
)
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# resident and persistent identities for an attached shape derive from its actual world and sibling order
@DataClass(frozen=True, slots=True)
class GhostPlacement:
    FirstIndex: int
    Following: int
    Previous: int
    WorldIndex: int
    BodySchema: int
    EdgeSchema: int
    GhostId: int


# local cell pointers must follow their newly allocated actual kernel residents
def MoveGhostCell(NodeValue: XmtNode, Indices: Mapping[int, int]) -> XmtNode:
    FieldsValue = dict(NodeValue.FieldsValue)
    for FieldValue in KKernelShapes[NodeValue.KindValue].FieldsValue:
        if FieldValue.EncodingValue != "p":
            continue
        NameValue = FieldValue.NameValue
        FieldsValue[NameValue] = (
            tuple(Indices[MemberValue] for MemberValue in NodeValue.Indexes(NameValue))
            if FieldValue.CountValue
            else Indices[NodeValue.Integer(NameValue)]
        )
    return XmtNode(Indices[NodeValue.IndexValue], NodeValue.KindValue, FieldsValue)


# the ghost world attaches a freshly generated isolated sheet or wire and its real sole edge
def BindGhostShape(
    ShapeValue: tuple[XmtNode, ...], Placement: GhostPlacement
) -> tuple[XmtNode, ...]:
    RootValue, *Geometry = ShapeValue
    (EdgeValue,) = (NodeValue for NodeValue in Geometry if NodeValue.KindValue == 16)
    if RootValue.KindValue != 12 or any(
        RootValue.Integer(KeyName) for KeyName in ("owner", "next", "previous")
    ):
        raise ValueError(
            "ghost attachment requires a freshly generated isolated local shape"
        )
    Indices = {
        NodeValue.IndexValue: IndexValue
        for IndexValue, NodeValue in enumerate(ShapeValue, Placement.FirstIndex)
    } | {0: 0}
    BodyValue, *MoveValues = (
        MoveGhostCell(NodeValue, Indices) for NodeValue in ShapeValue
    )
    LastEntity = BodyValue.Integer("highest_node_id")
    EdgeIndex = Indices[EdgeValue.IndexValue]
    ExtrasValue = MakeGhostAttr(
        Placement.FirstIndex + len(ShapeValue),
        BodyValue.IndexValue,
        EdgeIndex,
        LastEntity,
        Placement.BodySchema,
        Placement.EdgeSchema,
        Placement.GhostId,
    )
    BodyLink, _, EdgeLink, ChainValue, _ = ExtrasValue
    BodyValue = XmtNode(
        BodyValue.IndexValue,
        BodyValue.KindValue,
        dict(BodyValue.FieldsValue)
        | {
            "owner": Placement.WorldIndex,
            "next": Placement.Following,
            "previous": Placement.Previous,
            "highest_node_id": LastEntity + 2,
            "attributes_features": BodyLink.IndexValue,
            "attribute_chains": ChainValue.IndexValue,
        },
    )
    MovedValues = tuple(
        (
            XmtNode(
                NodeValue.IndexValue,
                NodeValue.KindValue,
                dict(NodeValue.FieldsValue)
                | {"attributes_features": EdgeLink.IndexValue},
            )
            if NodeValue.IndexValue == EdgeIndex
            else NodeValue
        )
        for NodeValue in MoveValues
    )
    return BodyValue, *MovedValues, *ExtrasValue
