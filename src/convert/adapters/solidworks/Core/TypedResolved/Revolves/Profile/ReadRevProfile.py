from collections import Counter

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Lines.CheckLineScope import (
    CheckLineScope,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineLoop import LineLoop
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineOrder import LineOrder
from convert.adapters.solidworks.Core.TypedResolved.Lines.ReadLineRegions import (
    ReadLineRegions,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.Revolves.AxisReference import (
    AxisReference,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Profile.CheckRevShape import (
    CheckRevShape,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Profile.ReadAxisLine import (
    ReadAxisLine,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Profile.ReadRevDims import (
    ReadRevDims,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Profile.ReadRevPoints import (
    ReadRevPoints,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Profile.ReadRevRows import (
    ReadRevRows,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Profile.RevolveProfile import (
    RevolveProfile,
)


# the selected construction axis and actual body region need separate complete ownership before neutral projection
def ReadRevProfile(
    SketchValue: ArchiveNode, AxisValue: AxisReference, LinkValue: NativeLink
) -> RevolveProfile:
    FieldsValue = RequireNative(SketchValue, "sgSketch").FieldsValue
    CheckLineScope(FieldsValue, True, True)
    RulesValue = ReadRevDims(SketchValue, LinkValue)
    References = Counter(RuleValue.LineValue for RuleValue in RulesValue)
    PointRows = NativeRows(FieldsValue.get("points"))
    LineRows = NativeRows(FieldsValue.get("lines"))
    if (
        FieldsValue.get("npoints") != len(PointRows)
        or FieldsValue.get("nlines") != len(LineRows)
        or (
            not 0 <= AxisValue.IndexValue < len(LineRows)
            or References[AxisValue.IndexValue]
        )
    ):
        raise ValueError(
            "ordinary revolve sketch counts or selected axis relation differ"
        )
    AxisLine = ReadAxisLine(LineRows[AxisValue.IndexValue], AxisValue)
    LinesValue, RetiredRows = ReadRevRows(LineRows, AxisValue.IndexValue, References)
    Regions = ReadLineRegions(SketchValue, LinesValue, LinkValue)
    CheckLineScope(FieldsValue, True, bool(Regions))
    PointsValue, AxisPoints, RetiredPoints = ReadRevPoints(
        PointRows, AxisLine, LinesValue
    )
    CheckRevShape(PointsValue, LinesValue, AxisPoints, AxisLine, RulesValue)
    LoopValue = LineLoop(
        PointsValue,
        LinesValue,
        LineOrder(PointsValue, LinesValue),
        NativeNodeSpan(LinkValue, SketchValue),
        RetiredRows=RetiredRows,
        RegionValues=Regions,
        RetiredPointRows=tuple(
            {
                "array_index": PointValue.IndexValue,
                "native_fields": PointValue.FieldsValue,
            }
            for PointValue in RetiredPoints
        ),
    )
    return RevolveProfile(LoopValue, AxisLine, AxisPoints, RulesValue, RetiredPoints)
