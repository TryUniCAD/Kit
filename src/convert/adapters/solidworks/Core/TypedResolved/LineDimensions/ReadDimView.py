from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# a display must select exactly one actual value group entry through the retained sketch alias
def ReadDimView(
    DisplayValue: ArchiveNode, SketchValue: ArchiveNode, IndexValue: int
) -> ArchiveNode:
    RowsValue = NativeRows(DisplayValue.FieldsValue.get("f850"))
    if DisplayValue.FieldsValue.get("n850") != 1 or len(RowsValue) != 1:
        raise ValueError("typed rectangle display has multiple dimension targets")
    Handle = RequireNative(RowsValue[0].get("o"), "moSkDimHandleValG2_c")
    if (
        Handle.FieldsValue.get("ff0") is not SketchValue
        or Handle.FieldsValue.get("ff8") != IndexValue
        or Handle.FieldsValue.get("fe8") is not None
        or Handle.FieldsValue.get("f100") is not None
    ):
        raise ValueError(
            "typed rectangle display does not own its selected sketch value"
        )
    return Handle
