from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.LineDims import (
    LineDims,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.CheckLineScope import (
    CheckLineScope,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineLoop import LineLoop
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineOrder import LineOrder
from convert.adapters.solidworks.Core.TypedResolved.Lines.ReadLinePoint import (
    ReadLinePoint,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.ReadLineSegment import (
    ReadLineSegment,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows


# the linked typed sketch owns array membership and provenance independently of legacy marker discovery
def ReadLineLoop(
    SketchValue: ArchiveNode, LinkValue: NativeLink, DimsValue: LineDims | None = None
) -> LineLoop:
    FieldsValue = SketchValue.FieldsValue
    CheckLineScope(FieldsValue, DimsValue is not None)
    References: Mapping[tuple[str, int], int] = (
        DimsValue.ReferencesValue if DimsValue is not None else {}
    )
    PointsValue = tuple(
        ReadLinePoint(RowValue, Index, References.get(("point", Index), 0))
        for Index, RowValue in enumerate(NativeRows(FieldsValue.get("points")))
    )
    LinesValue = tuple(
        ReadLineSegment(RowValue, Index, References.get(("line", Index), 0))
        for Index, RowValue in enumerate(NativeRows(FieldsValue.get("lines")))
    )
    if FieldsValue.get("npoints") != len(PointsValue) or FieldsValue.get(
        "nlines"
    ) != len(LinesValue):
        raise ValueError("typed line ring counts disagree with owned rows")
    return LineLoop(
        PointsValue,
        LinesValue,
        LineOrder(PointsValue, LinesValue),
        NativeNodeSpan(LinkValue, SketchValue),
        DimsValue,
    )


from collections.abc import Mapping
