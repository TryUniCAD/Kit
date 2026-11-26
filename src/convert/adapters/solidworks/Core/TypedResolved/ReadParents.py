from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# profile dependency must follow the retained concept list rather than the preceding sketch in history
def ReadParents(NodeValue: ArchiveNode) -> tuple[ArchiveNode, ...]:
    RecordValue = NativeRecord(NodeValue.FieldsValue.get("f60"))
    ListValue = NativeRecord(RecordValue.get("list"))
    ItemsValue = NativeRows(ListValue.get("items"))
    if type(ListValue.get("n")) is not int or ListValue["n"] != len(ItemsValue):
        raise ValueError("typed feature parent collection is incomplete")
    ParentsValue = tuple(RequireNative(ItemValue.get("o")) for ItemValue in ItemsValue)
    NativeIds = tuple(NativeNodeId(ParentValue) for ParentValue in ParentsValue)
    if len(set(NativeIds)) != len(NativeIds):
        raise ValueError("typed feature parent identities are duplicated")
    return ParentsValue
