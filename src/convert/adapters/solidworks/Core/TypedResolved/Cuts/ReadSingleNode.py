from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# body ownership requires count agreement before following an archived pointer
def ReadSingleNode(ArrayValue: object, ClassName: str) -> ArchiveNode:
    RecordValue = NativeRecord(ArrayValue)
    RowsValue = NativeRows(RecordValue.get("items"))
    CountValue = RecordValue.get("n")
    if type(CountValue) is not int or CountValue != 1 or len(RowsValue) != 1:
        raise ValueError("cut body reference requires one actual array member")
    return RequireNative(RowsValue[0].get("o"), ClassName)
