from collections.abc import Sequence
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.PlanarMates.FieldRecord import (
    FieldRecord,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireNode,
    RequireRecord,
)


# header and body list views must expose the same actual ordered log nodes without replacing their identities or values
def ReadLogItems(Value: object, ItemClass: str) -> tuple[ArchiveNode, ...]:
    if ItemClass not in ("moLogs_c", "moStamp_c"):
        raise ValueError("header epoch items require log or stamp classes")
    ListClass = "suObList" if ItemClass == "moLogs_c" else "moLogs_c"
    if isinstance(Value, ArchiveNode) and Value.ClassValue != RuntimeClass(
        ListClass, 1
    ):
        raise ValueError("header epoch list has an unsupported owner schema")
    FieldsValue = FieldRecord(Value)
    ItemsValue = FieldsValue.get("items")
    if not isinstance(ItemsValue, (tuple, list)):
        raise ValueError("header epoch items require an ordered collection")
    ItemsValue = CastValue(Sequence[object], ItemsValue)
    if "n" in FieldsValue and FieldInt(FieldsValue, "n") != len(ItemsValue):
        raise ValueError("header epoch list count differs from its actual items")
    NodesValue: list[ArchiveNode] = []
    for ItemValue in ItemsValue:
        NodeValue = RequireNode(
            (
                ItemValue
                if isinstance(ItemValue, ArchiveNode)
                else RequireRecord(ItemValue).get("o")
            ),
            ItemClass,
        )
        if NodeValue.ClassValue != RuntimeClass(ItemClass, 1):
            raise ValueError("header epoch item has an unsupported concrete schema")
        NodesValue.append(NodeValue)
    return tuple(NodesValue)
