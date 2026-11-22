from collections.abc import Mapping

from convert.adapters.solidworks.Core.TypedResolved.Lines.LineSegment import LineSegment
from convert.adapters.solidworks.Core.TypedResolved.Lines.ReadLineSegment import (
    ReadLineSegment,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.ReadLiveLines import (
    ReadLiveLines,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord


# retired native rows remain history while the selected axis stays outside the body perimeter
def ReadRevRows(
    RowsValue: tuple[Mapping[str, object], ...],
    AxisIndex: int,
    References: Mapping[int, int],
) -> tuple[tuple[LineSegment, ...], tuple[Mapping[str, object], ...]]:
    LinesValue: list[LineSegment] = []
    RetiredRows: list[Mapping[str, object]] = []
    for IndexValue, RowValue in enumerate(RowsValue):
        if IndexValue == AxisIndex:
            continue
        FieldsValue = NativeRecord(RowValue.get("line"))
        FlagsValue = FieldsValue.get("f54")
        if type(FlagsValue) is int and FlagsValue & 1:
            if IndexValue != 0:
                raise ValueError(
                    "ordinary revolve has unqualified retired line history"
                )
            EmptyValue, RetiredValue = ReadLiveLines((RowValue,), {})
            if EmptyValue:
                raise ValueError("retired revolve line unexpectedly remains live")
            RetiredRows.extend(RetiredValue)
        else:
            LinesValue.append(
                ReadLineSegment(RowValue, IndexValue, References.get(IndexValue, 0))
            )
    if (
        len(LinesValue) != 4
        or set(References) != {LineValue.IndexValue for LineValue in LinesValue}
        or (set(References.values()) != {1})
    ):
        raise ValueError("ordinary revolve contour and actual unary owners differ")
    return tuple(LinesValue), tuple(RetiredRows)
