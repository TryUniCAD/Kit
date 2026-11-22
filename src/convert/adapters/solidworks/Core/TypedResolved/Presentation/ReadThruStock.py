from math import isclose as IsClose

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.CheckDimGroups import (
    CheckDimGroups,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadAxisDim import (
    ReadAxisDim,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadDimRows import (
    ReadDimRows,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineLoop import LineLoop
from convert.adapters.solidworks.Core.TypedResolved.Lines.ReadLineLoop import (
    ReadLineLoop,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# each stock requires the actual four axis relations on its unmeasured contour
def ReadThruStock(ProfileValue: ArchiveNode, LinkValue: NativeLink) -> LineLoop:
    if (
        ProfileValue.FieldsValue.get("f3dc") != 0
        or ProfileValue.FieldsValue.get("pd_f110") is not None
    ):
        raise ValueError("two-stock rectangle has shared or spatial geometry")
    SketchValue = RequireNative(ProfileValue.FieldsValue.get("pd_f80"), "sgSketch")
    FieldsValue = NativeRecord(SketchValue.FieldsValue.get("dims"))
    CheckDimGroups(FieldsValue)
    RowsValue = ReadDimRows(FieldsValue, "nlog1", "log_g1")
    if (
        len(RowsValue) != 4
        or ReadDimRows(FieldsValue, "ng2", "val_g2")
        or not IsLineState(RequireNative(FieldsValue.get("f118"), "suObList"))
    ):
        raise ValueError("two-stock rectangle has unqualified drivers or axis count")
    AxisValues = tuple(
        ReadAxisDim(RowValue, Index, SketchValue, LinkValue)
        for Index, RowValue in enumerate(RowsValue)
    )
    LoopValue = ReadLineLoop(SketchValue, LinkValue, AxisValues)
    AxesByLine = {AxisValue.LineValue: AxisValue.CodeValue for AxisValue in AxisValues}
    if (
        len(LoopValue.PointsValue) != 4
        or len(LoopValue.LinesValue) != 4
        or set(AxesByLine) != {Value.IndexValue for Value in LoopValue.LinesValue}
        or sorted(AxesByLine.values()) != [4, 4, 5, 5]
    ):
        raise ValueError("rectangle axes do not cover every real contour line")
    for LineValue in LoopValue.LinesValue:
        Index = int(AxesByLine[LineValue.IndexValue] == 4)
        Start, EndValue = (
            LoopValue.PointsValue[PointIndex].PositionValue[Index]
            for PointIndex in (LineValue.StartValue, LineValue.EndValue)
        )
        if not IsClose(Start, EndValue, rel_tol=0.0, abs_tol=1e-9):
            raise ValueError("rectangle axis conflicts with its actual line")
    CheckTreeAlias(
        LinkValue,
        (SketchValue, *(AxisValue.HandleValue for AxisValue in AxisValues)),
    )
    return LoopValue
