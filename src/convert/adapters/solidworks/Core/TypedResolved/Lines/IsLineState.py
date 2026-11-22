from collections.abc import Mapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# relation managers must contain no hidden authored state before replacing a legacy sketch projection
def IsLineState(Value: object) -> bool:
    if isinstance(Value, ArchiveNode):
        return IsLineState(RequireNative(Value, "suObList").FieldsValue)
    if isinstance(Value, Mapping):
        return all(
            IsLineState(ItemValue)
            for ItemValue in CastValue(Mapping[str, object], Value).values()
        )
    if isinstance(Value, (list, tuple)):
        return len(CastValue(tuple[object, ...], Value)) == 0
    return type(Value) is int and Value == 0
