from collections.abc import Mapping

from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.CheckDimBase import (
    CheckDimBase,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadDimHandle import (
    ReadDimHandle,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineLoop import LineLoop
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows


# each actual saved relation names one segment slot and a signed axis code
def ReadStockRels(FieldsValue: Mapping[str, object]) -> dict[int, int]:
    DimsValue = NativeRecord(FieldsValue.get("dims"))
    Records = NativeRows(DimsValue.get("log_g1"))
    if (
        DimsValue.get("nlog1") != 4
        or len(Records) != 4
        or not all(
            IsLineState(Value)
            for FieldName, Value in DimsValue.items()
            if FieldName not in ("log_g1", "nlog1")
        )
    ):
        raise ValueError("SOLIDWORKS shell stock carries additional sketch relations")
    Result: dict[int, int] = {}
    for Event in Records:
        Relation = NativeRecord(Event.get("d"))
        CheckDimBase(Relation)
        IndexValue = ReadDimHandle(Relation.get("h1"), "sgLineHandle")
        AxisCode = Relation.get("f80")
        if (
            IndexValue in Result
            or type(AxisCode) is not int
            or AxisCode not in (4, 5)
            or Relation.get("f28") is not None
            or Relation.get("fa0") != 0xFFFE
            or Relation.get("fa4") != 0
        ):
            raise ValueError("SOLIDWORKS shell stock relation has another owner")
        Result[IndexValue] = AxisCode
    return Result


# every relation must match its own actual horizontal or vertical segment
def CheckStockRels(Relations: Mapping[int, int], LoopValue: LineLoop) -> None:
    if set(Relations) != {Value.IndexValue for Value in LoopValue.LinesValue}:
        raise ValueError("SOLIDWORKS shell stock relations miss actual segments")
    for LineValue in LoopValue.LinesValue:
        Start, EndValue = (
            LoopValue.PointsValue[Index].PositionValue
            for Index in (LineValue.StartValue, LineValue.EndValue)
        )
        CodeValue = (
            4 if Start[1] == EndValue[1] else 5 if Start[0] == EndValue[0] else None
        )
        if CodeValue != Relations[LineValue.IndexValue]:
            raise ValueError(
                "SOLIDWORKS shell stock relation differs from solved geometry"
            )
