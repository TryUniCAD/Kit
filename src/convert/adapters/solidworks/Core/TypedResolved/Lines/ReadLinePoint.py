from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.TypedResolved.Lines.CheckLineEntity import (
    CheckLineEntity,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.LinePoint import LinePoint
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# point records supply owned coordinates while adjacency handles prove their actual line membership
def ReadLinePoint(
    RowValue: Mapping[str, object], IndexValue: int, ReferenceValue: int = 0
) -> LinePoint:
    FieldsValue = NativeRecord(RowValue.get("point"))
    Retired = FieldsValue.get("f54") == 5
    CheckLineEntity(FieldsValue, 0 if Retired else ReferenceValue, 5 if Retired else 4)
    CreationId = FieldsValue.get("f0c")
    if (
        RowValue.get("kind") != 0
        or FieldsValue.get("pflags") != 30
        or FieldsValue.get("fe4") != 0
        or FieldsValue.get("fe8") != (0 if Retired else 2)
        or FieldsValue.get("f08") != 0
        or FieldsValue.get("fec") != 0
        or FieldsValue.get("has_jet") != 0
        or FieldsValue.get("ff0") != 0
        or FieldsValue.get("f108") != -2
        or type(CreationId) is not int
    ):
        raise ValueError("typed line ring has an unqualified point")
    if Retired:
        if (
            CreationId != -1
            or ReferenceValue
            or FieldsValue.get("h1") is not None
            or FieldsValue.get("h2") is not None
        ):
            raise ValueError("typed line ring has an unqualified deleted point history")
        Handles: tuple[ArchiveNode, ...] = ()
    else:
        if CreationId <= 0:
            raise ValueError("typed line ring has an unqualified point identity")
        Handles = (
            RequireNative(FieldsValue.get("h1"), "sgLineHandle"),
            RequireNative(FieldsValue.get("h2"), "sgLineHandle"),
        )
    Position = NativeRecord(FieldsValue.get("pos"))
    return LinePoint(
        IndexValue,
        CreationId,
        (
            RequireScalar(RequireScalar(Position.get("x")) / 0.001),
            RequireScalar(RequireScalar(Position.get("y")) / 0.001),
        ),
        Handles,
        {
            NameValue: Value
            for NameValue, Value in FieldsValue.items()
            if Retired or NameValue not in ("h1", "h2")
        },
    )
