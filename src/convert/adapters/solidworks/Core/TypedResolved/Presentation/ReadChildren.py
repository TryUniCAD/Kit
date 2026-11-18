from collections.abc import Mapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# system children must be reached through the actual typed owner list rather than keyword adjacency
def ReadChildren(NodeValue: ArchiveNode) -> tuple[ArchiveNode, ...]:
    ListValue = NodeValue.FieldsValue.get("f60")
    if not isinstance(ListValue, Mapping):
        raise ValueError("system owner has no typed feature list")
    EntryValue = CastValue(Mapping[str, object], ListValue).get("list")
    if not isinstance(EntryValue, Mapping):
        raise ValueError("system owner feature list has no counted entries")
    EntryValue = CastValue(Mapping[str, object], EntryValue)
    ItemsValue = EntryValue.get("items")
    if not isinstance(ItemsValue, (tuple, list)):
        raise ValueError("system owner feature entries are not a sequence")
    NodesValue: list[ArchiveNode] = []
    for ItemValue in CastValue(tuple[object, ...] | list[object], ItemsValue):
        if not isinstance(ItemValue, Mapping):
            raise ValueError("system owner feature entry is not typed")
        NodesValue.append(
            RequireNative(CastValue(Mapping[str, object], ItemValue).get("o"))
        )
    CountValue = EntryValue.get("n")
    if type(CountValue) is not int or CountValue != len(NodesValue):
        raise ValueError("system owner feature count disagrees with its entries")
    if len({NativeNodeId(Child) for Child in NodesValue}) != len(NodesValue):
        raise ValueError("system owner children have duplicate identities")
    return tuple(NodesValue)
