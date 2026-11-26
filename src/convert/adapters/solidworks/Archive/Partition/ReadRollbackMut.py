from collections.abc import Mapping
from struct import pack as PackValue

from convert.adapters.solidworks.Archive.Partition.ReadXmtNodeMut import ReadXmtNodeMut
from convert.adapters.solidworks.Archive.Partition.XmtCursor import XmtCursor
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# retained rollback ownership must resolve every deleted record and its preceding world
def ReadRollbackMut(
    CursorValue: XmtCursor, NodesValue: Mapping[int, XmtNode]
) -> frozenset[int]:
    CursorValue.ExpectBytes(PackValue(">HH", 1, 1))
    DeletedValue: set[int] = set()
    while IndexValue := CursorValue.ReadIndex():
        KindValue = CursorValue.ReadKind()
        if (
            IndexValue in DeletedValue
            or IndexValue not in NodesValue
            or NodesValue[IndexValue].KindValue != KindValue
        ):
            raise ValueError("rollback deletion has an unresolved owner")
        DeletedValue.add(IndexValue)
    CursorValue.ExpectBytes(PackValue(">iH", 1, 101))
    PreviousValue = ReadXmtNodeMut(CursorValue, 101, True)
    if PreviousValue.IndexValue != 1:
        raise ValueError("rollback world has a foreign identity")
    CursorValue.ExpectBytes(PackValue(">HH", 1, 1))
    return frozenset(DeletedValue)
