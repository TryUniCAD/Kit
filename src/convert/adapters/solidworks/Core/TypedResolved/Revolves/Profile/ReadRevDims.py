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
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Profile.LineEqual import (
    LineEqual,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Profile.ReadRevEqual import (
    ReadRevEqual,
)


# only witnessed contour relations may replace legacy inferred constraints on the selected sketch
def ReadRevDims(
    SketchValue: ArchiveNode, LinkValue: NativeLink
) -> tuple[tuple[LineAxis, ...], LineEqual | None]:
    FieldsValue = NativeRecord(SketchValue.FieldsValue.get("dims"))
    CheckDimGroups(FieldsValue, AllowBinary=True)
    if ReadDimRows(FieldsValue, "ng2", "val_g2") or not IsLineState(
        FieldsValue.get("f118")
    ):
        raise ValueError("ordinary revolve profile has other value drivers or displays")
    RowsValue = ReadDimRows(FieldsValue, "nlog1", "log_g1")
    if len(RowsValue) != 4:
        raise ValueError("ordinary revolve requires four actual contour axis relations")
    AxesValue = tuple(
        ReadAxisDim(RowValue, IndexValue, SketchValue, LinkValue)
        for IndexValue, RowValue in enumerate(RowsValue)
    )
    PairRows = ReadDimRows(FieldsValue, "nlog2", "log_g2")
    if len(PairRows) > 1:
        raise ValueError("ordinary revolve has unqualified binary relation count")
    EqualValue = ReadRevEqual(PairRows[0], SketchValue, LinkValue) if PairRows else None
    return AxesValue, EqualValue
