from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.CheckDimGroups import (
    CheckDimGroups,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadDimRows import (
    ReadDimRows,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.CheckLineScope import (
    CheckLineScope,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the counted straight outline must own only the supported binary distances and unary axes
def IsDimRect(SketchValue: ArchiveNode) -> bool:
    FieldsValue = SketchValue.FieldsValue
    if FieldsValue.get("npoints") != 4 or FieldsValue.get("nlines") != 4:
        return False
    CheckLineScope(FieldsValue, HasDrivers=True)
    DimsValue = NativeRecord(FieldsValue.get("dims"))
    CheckDimGroups(DimsValue)
    Values = ReadDimRows(DimsValue, "ng2", "val_g2")
    AxesValue = ReadDimRows(DimsValue, "nlog1", "log_g1")
    if len(Values) != 2 or len(AxesValue) != 4:
        return False
    for RowValue in Values:
        _ = RequireNative(RowValue.get("d"), "sgPntPntDist")
    return all(
        NativeRecord(RowValue.get("d")).get("f80") in (4, 5) for RowValue in AxesValue
    )
