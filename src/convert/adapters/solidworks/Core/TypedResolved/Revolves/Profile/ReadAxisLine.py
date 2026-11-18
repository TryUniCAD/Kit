from collections.abc import Mapping

from convert.adapters.solidworks.Core.TypedResolved.Lines.CheckLineEntity import (
    CheckLineEntity,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineIndex import LineIndex
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineSegment import LineSegment
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.Revolves.AxisReference import (
    AxisReference,
)


# centerline state and permanent identity must agree with the selected native handle before geometry is exposed
def ReadAxisLine(
    RowValue: Mapping[str, object], AxisValue: AxisReference
) -> LineSegment:
    FieldsValue = NativeRecord(RowValue.get("line"))
    CheckLineEntity(FieldsValue, 0, 12)
    PermanentValue, CreationValue = FieldsValue.get("f08"), FieldsValue.get("f0c")
    if (
        RowValue.get("flags") != 2
        or any(FieldsValue.get(NameValue) != 0 for NameValue in ("fd0", "fd4", "fe8"))
        or type(PermanentValue) is not int
        or PermanentValue <= 0
        or (
            type(CreationValue) is not int
            or CreationValue <= 0
            or PermanentValue != AxisValue.MarkValue
        )
    ):
        raise ValueError(
            "ordinary revolve construction identity differs from its actual selected mark"
        )
    return LineSegment(
        AxisValue.IndexValue,
        PermanentValue,
        CreationValue,
        LineIndex(FieldsValue, "fc8_s", "fc8", 65535),
        LineIndex(FieldsValue, "fcc_s", "fcc", 65535),
        FieldsValue,
    )
