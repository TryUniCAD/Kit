from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.CheckDimGroups import (
    CheckDimGroups,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.LineAxis import (
    LineAxis,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadAxisDim import (
    ReadAxisDim,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadDimRows import (
    ReadDimRows,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineLoop import LineLoop
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)


# each stock line must retain one actual mapped unary relation with the matching orientation
def CheckPatAxes(
    SketchValue: ArchiveNode, LoopValue: LineLoop, LinkValue: NativeLink
) -> tuple[LineAxis, ...]:
    Fields = NativeRecord(SketchValue.FieldsValue.get("dims"))
    CheckDimGroups(Fields)
    RowsValue = ReadDimRows(Fields, "nlog1", "log_g1")
    if (
        ReadDimRows(Fields, "ng2", "val_g2")
        or not IsLineState(Fields.get("f118"))
        or len(RowsValue) != 4
        or len(LoopValue.LinesValue) != 4
    ):
        raise ValueError("cold pattern stock requires four local unary relations")
    AxisValues = tuple(
        ReadAxisDim(RowValue, Index, SketchValue, LinkValue)
        for Index, RowValue in enumerate(RowsValue)
    )
    if {AxisValue.LineValue for AxisValue in AxisValues} != set(range(4)):
        raise ValueError("cold pattern relation does not own every stock line once")
    CheckTreeAlias(
        LinkValue, (SketchValue, *(Value.HandleValue for Value in AxisValues))
    )
    for AxisValue in AxisValues:
        Segment = LoopValue.LinesValue[AxisValue.LineValue]
        StartValue = LoopValue.PointsValue[Segment.StartValue].PositionValue
        EndValue = LoopValue.PointsValue[Segment.EndValue].PositionValue
        Coordinate = 1 if AxisValue.CodeValue == 4 else 0
        if StartValue[Coordinate] != EndValue[Coordinate]:
            raise ValueError(
                "cold pattern relation disagrees with its actual local segment"
            )
    return AxisValues
