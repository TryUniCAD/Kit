from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadDimHandle import (
    ReadDimHandle,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.CheckLineEntity import (
    CheckLineEntity,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.LinePoint import LinePoint
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# standalone construction endpoints have one actual adjacency handle rather than contour vertex pairs
def ReadAxisPoint(
    RowValue: Mapping[str, object], IndexValue: int, AxisIndex: int
) -> LinePoint:
    FieldsValue = NativeRecord(RowValue.get("point"))
    CheckLineEntity(FieldsValue)
    CreationValue = FieldsValue.get("f0c")
    if (
        RowValue.get("kind") != 0
        or FieldsValue.get("pflags") != 30
        or any(
            FieldsValue.get(NameValue) != 0
            for NameValue in ("fe4", "f08", "fec", "has_jet", "ff0")
        )
        or FieldsValue.get("fe8") != 1
        or FieldsValue.get("f108") != -2
        or (
            FieldsValue.get("h2") is not None
            or type(CreationValue) is not int
            or CreationValue <= 0
        )
    ):
        raise ValueError(
            "ordinary revolve axis endpoint has unqualified native ownership"
        )
    HandleValue = RequireNative(FieldsValue.get("h1"), "sgLineHandle")
    if ReadDimHandle(HandleValue, "sgLineHandle") != AxisIndex:
        raise ValueError("ordinary revolve axis endpoint adjacency differs")
    PositionValue = NativeRecord(FieldsValue.get("pos"))
    return LinePoint(
        IndexValue,
        CreationValue,
        (
            RequireScalar(RequireScalar(PositionValue.get("x")) * 1000.0),
            RequireScalar(RequireScalar(PositionValue.get("y")) * 1000.0),
        ),
        (HandleValue,),
        {
            NameValue: Value
            for NameValue, Value in FieldsValue.items()
            if NameValue not in ("h1", "h2")
        },
    )
