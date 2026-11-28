from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.CheckDimBase import (
    CheckDimBase,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.LineAxis import (
    LineAxis,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadDimHandle import (
    ReadDimHandle,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# declared embedded unary records bind horizontal and vertical intent to their retained line handles
def ReadAxisDim(
    RowValue: Mapping[str, object],
    IndexValue: int,
    SketchValue: ArchiveNode,
    LinkValue: NativeLink,
) -> LineAxis:
    FieldsValue = NativeRecord(RowValue.get("d"))
    CheckDimBase(FieldsValue)
    CodeValue = FieldsValue.get("f80")
    if (
        type(CodeValue) is not int
        or CodeValue not in (4, 5)
        or FieldsValue.get("f28") is not None
        or FieldsValue.get("fa0") != 0xFFFE
        or FieldsValue.get("fa4") != 0
    ):
        raise ValueError("typed rectangle unary relation is not an ordinary axis")
    Handle = RequireNative(FieldsValue.get("h1"), "sgLineHandle")
    return LineAxis(
        IndexValue,
        ReadDimHandle(Handle, "sgLineHandle"),
        CodeValue,
        Handle,
        {
            **NativeNodeSpan(LinkValue, SketchValue),
            "embedded_array": "dims.log_g1",
            "row_index": IndexValue,
            "embedded_class": "sgLogG1Dim",
        },
    )
