from collections.abc import Callable

from convert.adapters.solidworks.Archive.Partition.ReadXmtValueMut import (
    ReadXmtValueMut,
)

from convert.adapters.solidworks.Archive.Partition.XmtCursor import XmtCursor
from convert.adapters.solidworks.Archive.Partition.XmtField import XmtField


# typed arrays must preserve every declared field without unchecked slicing or incidental scans
def ReadXmtArrayMut(
    CursorValue: XmtCursor,
    FieldValue: XmtField,
    CountValue: int,
    PreviousWorld: bool,
    ValueReader: Callable[[XmtCursor, XmtField, bool], object] = ReadXmtValueMut,
) -> tuple[object, ...]:
    Values: list[object] = []
    while len(Values) < CountValue:
        Values.append(ValueReader(CursorValue, FieldValue, PreviousWorld))
    return tuple(Values)
