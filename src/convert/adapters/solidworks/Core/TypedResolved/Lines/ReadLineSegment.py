from collections.abc import Mapping

from convert.adapters.solidworks.Core.TypedResolved.Lines.CheckLineEntity import (
    CheckLineEntity,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineIndex import LineIndex
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineSegment import LineSegment
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord


# plain segments must join explicit point indices without borrowing coordinate marker heuristics
def ReadLineSegment(
    RowValue: Mapping[str, object], IndexValue: int, RelationCount: int = 0
) -> LineSegment:
    FieldsValue = NativeRecord(RowValue.get("line"))
    CheckLineEntity(FieldsValue, RelationCount)
    PermanentId, CreationId = FieldsValue.get("f08"), FieldsValue.get("f0c")
    if (
        RowValue.get("flags") != 0
        or FieldsValue.get("fd0") != 1
        or FieldsValue.get("fd4") != 0
        or FieldsValue.get("fe8") != 0
        or type(PermanentId) is not int
        or PermanentId <= 0
        or type(CreationId) is not int
        or CreationId <= 0
    ):
        raise ValueError("typed line ring has an unqualified segment")
    return LineSegment(
        IndexValue,
        PermanentId,
        CreationId,
        LineIndex(FieldsValue, "fc8_s", "fc8", 65535),
        LineIndex(FieldsValue, "fcc_s", "fcc", 65535),
        FieldsValue,
    )
