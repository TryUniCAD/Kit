from convert.adapters.solidworks.Archive.Partition.ReadXmtValueMut import (
    ReadXmtValueMut,
)
from convert.adapters.solidworks.Archive.Partition.XmtCursor import XmtCursor
from convert.adapters.solidworks.Archive.Partition.XmtField import XmtField


# previous rows qualify each pointer against the originating native allocation domain
def ReadXmtQualMut(
    CursorValue: XmtCursor,
    FieldValue: XmtField,
    PreviousWorld: bool,
    *,
    Qualifiers: dict[int, bool],
) -> object:
    if FieldValue.EncodingValue != "p":
        return ReadXmtValueMut(CursorValue, FieldValue, PreviousWorld)
    IndexValue = CursorValue.ReadIndex()
    FlagValue = CursorValue.TakeBytes(1)[0]
    if FlagValue not in (0, 1) or not (IndexValue or FlagValue):
        raise ValueError("invalid qualified kernel reference")
    if bool(FlagValue) != Qualifiers.setdefault(IndexValue, bool(FlagValue)):
        raise ValueError("inconsistent source index selector for a rollback target")
    return IndexValue
