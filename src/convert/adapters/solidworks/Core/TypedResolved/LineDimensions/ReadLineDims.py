from collections import Counter

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.CheckDimGroups import (
    CheckDimGroups,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.LineDims import (
    LineDims,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadAxisDim import (
    ReadAxisDim,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadDimRows import (
    ReadDimRows,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadLineDriver import (
    ReadLineDriver,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# complete dimension managers derive entity reference counts from their actual local handle occurrences
def ReadLineDims(SketchValue: ArchiveNode, LinkValue: NativeLink) -> LineDims:
    FieldsValue = NativeRecord(SketchValue.FieldsValue.get("dims"))
    CheckDimGroups(FieldsValue)
    Values = ReadDimRows(FieldsValue, "ng2", "val_g2")
    AxesValue = ReadDimRows(FieldsValue, "nlog1", "log_g1")
    DisplayList = RequireNative(FieldsValue.get("f118"), "suObList")
    Displays = NativeRows(DisplayList.FieldsValue.get("items"))
    if (
        len(Values) != 2
        or len(AxesValue) != 4
        or len(Displays) != 2
        or DisplayList.FieldsValue.get("n") != 2
    ):
        raise ValueError("typed rectangle requires two drivers and four owned axes")
    DriverValues = tuple(
        ReadLineDriver(
            RowValue,
            Index,
            RequireNative(Displays[Index].get("o"), "moDisplayDistanceDim_c"),
            SketchValue,
            LinkValue,
        )
        for Index, RowValue in enumerate(Values)
    )
    AxisValues = tuple(
        ReadAxisDim(RowValue, Index, SketchValue, LinkValue)
        for Index, RowValue in enumerate(AxesValue)
    )
    References: Counter[tuple[str, int]] = Counter()
    References.update(
        ("point", Point) for Driver in DriverValues for Point in Driver.PointValues
    )
    References.update(("line", AxisValue.LineValue) for AxisValue in AxisValues)
    return LineDims(DriverValues, AxisValues, dict(References))
