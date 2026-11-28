from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.CheckBinaryDim import (
    CheckBinaryDim,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadDimHandle import (
    ReadDimHandle,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Profile.LineEqual import (
    LineEqual,
)


# only an ordinary equal length record with two distinct local line handles can own the extra contour relation
def ReadRevEqual(
    RowValue: Mapping[str, object], SketchValue: ArchiveNode, LinkValue: NativeLink
) -> LineEqual:
    FieldsValue = NativeRecord(RowValue.get("d"))
    CheckBinaryDim(FieldsValue, 14)
    First = ReadDimHandle(FieldsValue.get("h1"), "sgLineHandle")
    Second = ReadDimHandle(FieldsValue.get("h2"), "sgLineHandle")
    if (
        First == Second
        or FieldsValue.get("f30") != 0
        or FieldsValue.get("refcount") != 0
    ):
        raise ValueError("revolve equal length has unqualified operands or ownership")
    return LineEqual(
        (First, Second),
        {
            **NativeNodeSpan(LinkValue, SketchValue),
            "embedded_array": "dims.log_g2",
            "row_index": 0,
            "embedded_class": "sgLogG2Dim",
        },
    )
