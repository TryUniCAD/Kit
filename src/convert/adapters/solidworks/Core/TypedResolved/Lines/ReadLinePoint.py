from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.TypedResolved.Lines.CheckLineEntity import (
    CheckLineEntity,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.LinePoint import LinePoint
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# point records supply owned coordinates while adjacency handles prove their actual line membership
def ReadLinePoint(RowValue: Mapping[str, object], IndexValue: int) -> LinePoint:
    FieldsValue = NativeRecord(RowValue.get("point"))
    CheckLineEntity(FieldsValue)
    CreationId = FieldsValue.get("f0c")
    if (
        RowValue.get("kind") != 0
        or FieldsValue.get("pflags") != 30
        or FieldsValue.get("fe4") != 0
        or FieldsValue.get("fe8") != 2
        or FieldsValue.get("f08") != 0
        or FieldsValue.get("fec") != 0
        or FieldsValue.get("has_jet") != 0
        or FieldsValue.get("ff0") != 0
        or FieldsValue.get("f108") != -2
        or type(CreationId) is not int
        or CreationId <= 0
    ):
        raise ValueError("typed line ring has an unqualified point")
    Position = NativeRecord(FieldsValue.get("pos"))
    return LinePoint(
        IndexValue,
        CreationId,
        (
            RequireScalar(RequireScalar(Position.get("x")) * 1000.0),
            RequireScalar(RequireScalar(Position.get("y")) * 1000.0),
        ),
        (
            RequireNative(FieldsValue.get("h1"), "sgLineHandle"),
            RequireNative(FieldsValue.get("h2"), "sgLineHandle"),
        ),
        {
            NameValue: Value
            for NameValue, Value in FieldsValue.items()
            if NameValue not in ("h1", "h2")
        },
    )
