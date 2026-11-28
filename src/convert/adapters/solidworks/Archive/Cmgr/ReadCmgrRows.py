from collections.abc import Mapping, Sequence
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# configuration metadata must follow the manager list rather than scanning class name strings
def ReadCmgrRows(RootValue: ArchiveNode) -> tuple[ArchiveNode, ...]:
    FieldsValue = RootValue.FieldsValue.get("f370")
    if not isinstance(FieldsValue, Mapping):
        raise ValueError("SOLIDWORKS manager has no typed configuration directory")
    Directory = CastValue(Mapping[str, object], FieldsValue)
    ItemsValue = Directory.get("items")
    if not isinstance(ItemsValue, (list, tuple)):
        raise ValueError(
            "SOLIDWORKS manager configuration directory has no ordered rows"
        )
    NodesValue: list[ArchiveNode] = []
    for ItemValue in CastValue(Sequence[object], ItemsValue):
        if not isinstance(ItemValue, Mapping):
            raise ValueError("SOLIDWORKS manager configuration row is not typed")
        RowFields = CastValue(Mapping[str, object], ItemValue)
        NodeValue = ArchiveNode.RequireNode(RowFields.get("o"))
        if NodeValue.ClassValue not in (
            RuntimeClass("moPartConfiguration_c", 1),
            RuntimeClass("moConfiguration_c", 1),
        ):
            raise ValueError(
                "SOLIDWORKS manager configuration row has an unsupported class"
            )
        NodesValue.append(NodeValue)
    return tuple(NodesValue)
