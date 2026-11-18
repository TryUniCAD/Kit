from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.LineDims import (
    LineDims,
)
from collections.abc import Mapping
from convert.adapters.solidworks.Core.TypedResolved.Lines.CheckLineScope import (
    CheckLineScope,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineLoop import LineLoop
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineOrder import LineOrder
from convert.adapters.solidworks.Core.TypedResolved.Lines.ReadLinePoint import (
    ReadLinePoint,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.ReadLiveLines import (
    ReadLiveLines,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.ReadLineRegions import (
    ReadLineRegions,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows


# the linked typed sketch owns array membership and provenance independently of legacy marker discovery
def ReadLineLoop(
    SketchValue: ArchiveNode, LinkValue: NativeLink, DimsValue: LineDims | None = None
) -> LineLoop:
    FieldsValue = SketchValue.FieldsValue
    References: Mapping[tuple[str, int], int] = (
        DimsValue.ReferencesValue if DimsValue is not None else {}
    )
    PointRows = NativeRows(FieldsValue.get("points"))
    OriginValue = None if DimsValue is None else DimsValue.OriginValue
    ExtraCount = int(OriginValue is not None)
    if OriginValue is not None:
        if len(PointRows) != 5 or OriginValue.ExternalIndex != 4:
            raise ValueError(
                "typed origin point must remain outside the four vertex contour"
            )
        PointRows = PointRows[:4]
    PointsValue = tuple(
        ReadLinePoint(RowValue, Index, References.get(("point", Index), 0))
        for Index, RowValue in enumerate(PointRows)
    )
    LineRows = NativeRows(FieldsValue.get("lines"))
    LinesValue, RetiredRows = ReadLiveLines(LineRows, References)
    Regions = ReadLineRegions(SketchValue, LinesValue, LinkValue)
    CheckLineScope(FieldsValue, DimsValue is not None, bool(Regions))
    if FieldsValue.get("npoints") != len(PointsValue) + ExtraCount or FieldsValue.get(
        "nlines"
    ) != len(LineRows):
        raise ValueError("typed line ring counts disagree with owned rows")
    return LineLoop(
        PointsValue,
        LinesValue,
        LineOrder(PointsValue, LinesValue),
        NativeNodeSpan(LinkValue, SketchValue),
        DimsValue,
        RetiredRows,
        Regions,
    )
