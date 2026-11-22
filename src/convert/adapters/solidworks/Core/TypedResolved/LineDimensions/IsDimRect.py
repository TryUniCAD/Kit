from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadDimRows import (
    ReadDimRows,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# two actual point distances identify the rectangle whose complete owned relation graph must be checked
def IsDimRect(SketchValue: ArchiveNode) -> bool:
    FieldsValue = SketchValue.FieldsValue
    if FieldsValue.get("npoints") != 4 or FieldsValue.get("nlines") != 4:
        return False
    DimsValue = NativeRecord(FieldsValue.get("dims"))
    Values = ReadDimRows(DimsValue, "ng2", "val_g2")
    if len(Values) != 2:
        return False
    for RowValue in Values:
        _ = RequireNative(RowValue.get("d"), "sgPntPntDist")
    return True
