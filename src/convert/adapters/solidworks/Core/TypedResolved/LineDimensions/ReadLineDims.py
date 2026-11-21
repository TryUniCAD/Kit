from collections import Counter

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.CheckDimGroups import (
    CheckDimGroups,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.LineDims import (
    LineDims,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.Origin.ReadOriginDim import (
    ReadOriginDim,
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
    OriginValue = ReadOriginDim(SketchValue, LinkValue)
    CheckDimGroups(FieldsValue, OriginValue is not None)
    Values = ReadDimRows(FieldsValue, "ng2", "val_g2")
    AxesValue = ReadDimRows(FieldsValue, "nlog1", "log_g1")
    DisplayList = RequireNative(FieldsValue.get("f118"), "suObList")
    Displays = NativeRows(DisplayList.FieldsValue.get("items"))
    DriverCount = len(Values)
    if (
        DriverCount not in (0, 2)
        or (OriginValue is not None and DriverCount != 2)
        or len(AxesValue) != 4
        or len(Displays) != DriverCount
        or DisplayList.FieldsValue.get("n") != DriverCount
    ):
        raise ValueError("typed rectangle has unqualified drivers or owned axes")
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
    if OriginValue is not None:
        References.update(
            ("point", Index)
            for Index in (OriginValue.ExternalIndex, OriginValue.LocalIndex)
        )
    return LineDims(DriverValues, AxisValues, dict(References), OriginValue)
