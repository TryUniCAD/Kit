from collections.abc import Mapping
from convert.adapters.solidworks.Core.TypedResolved.Lines.CheckLineEntity import (
    CheckLineEntity,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineIndex import LineIndex
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineSegment import LineSegment
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord


# thin body incidence uses its native open line flag and two live endpoints
def ReadThinEdge(RowValue: Mapping[str, object]) -> LineSegment:
    FieldsValue = NativeRecord(RowValue.get("line"))
    CheckLineEntity(FieldsValue, FlagsValue=68)
    Permanent = FieldsValue.get("f08")
    Creation = FieldsValue.get("f0c")
    if (
        RowValue.get("flags") != 0
        or FieldsValue.get("fd0") != 1
        or FieldsValue.get("fd4") != 0
        or FieldsValue.get("fe8") != 0
        or type(Permanent) is not int
        or Permanent <= 0
        or type(Creation) is not int
        or Creation <= 0
    ):
        raise ValueError("SOLIDWORKS thin sketch requires its actual open body line")
    return LineSegment(
        0,
        Permanent,
        Creation,
        LineIndex(FieldsValue, "fc8_s", "fc8", 65535),
        LineIndex(FieldsValue, "fcc_s", "fcc", 65535),
        FieldsValue,
    )
