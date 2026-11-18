from collections.abc import Mapping

from convert.adapters.solidworks.Core.TypedResolved.Lines.LineSegment import LineSegment
from convert.adapters.solidworks.Core.TypedResolved.Lines.ReadLineSegment import (
    ReadLineSegment,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord


# native deletion flags exclude a retired line from geometry while its actual archive row and state remain preserved
def ReadLiveLines(
    RowsValue: tuple[Mapping[str, object], ...],
    References: Mapping[tuple[str, int], int],
) -> tuple[tuple[LineSegment, ...], tuple[Mapping[str, object], ...]]:
    LinesValue: list[LineSegment] = []
    RetiredRows: list[Mapping[str, object]] = []
    for IndexValue, RowValue in enumerate(RowsValue):
        FieldsValue = NativeRecord(RowValue.get("line"))
        FlagsValue = FieldsValue.get("f54")
        if type(FlagsValue) is int and FlagsValue & 1:
            if (
                IndexValue != 0
                or FlagsValue != 5
                or RowValue.get("flags") != 0
                or FieldsValue.get("f08") != 0
                or FieldsValue.get("f0c") != -1
                or FieldsValue.get("fd0") != 0
                or FieldsValue.get("f20") != 0
                or FieldsValue.get("ext") is not None
                or FieldsValue.get("group") is not None
                or References.get(("line", IndexValue), 0)
            ):
                raise ValueError(
                    "typed line ring has an unqualified deleted line history"
                )
            RetiredRows.append(
                {
                    "array_index": IndexValue,
                    "flags": RowValue["flags"],
                    "native_fields": dict(FieldsValue),
                }
            )
        else:
            LinesValue.append(
                ReadLineSegment(
                    RowValue, IndexValue, References.get(("line", IndexValue), 0)
                )
            )
    return tuple(LinesValue), tuple(RetiredRows)
